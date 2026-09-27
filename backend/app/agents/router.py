import asyncio
import re
import json
from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel
from backend.app.agents.tools import (
    lexical_search, vector_search, graph_search, fuse_sources, expand_evidence,
    tokens, evidence_window, vector_search_tool, graph_search_tool
)
from backend.app.agents.critic import complete, verify_answer, is_quote_supported, CriticResult, get_llm, critic_agent
from backend.app.models import selected_profile, resolve_profile


# Compatibility data structures for LangGraph / Evaluation agents
class AgentState(TypedDict, total=False):
    query: str
    tenant_id: Optional[str]
    route: str
    retrieved_contexts: List[Dict[str, Any]]
    draft_answer: str
    critic_feedback: Optional[str]
    refinement_query: Optional[str]
    loop_count: int
    final_answer: str
    thought_process: List[str]
    sources: List[Dict[str, Any]]


class RouteChoice(BaseModel):
    route: str
    reason: str


def model_failure_reason(exc):
    status = getattr(exc, 'status_code', None)
    if status is None and getattr(exc, 'response', None) is not None:
        status = exc.response.status_code
    reasons = {429: 'Provider đang giới hạn tần suất hoặc quota (429).',
               401: 'Provider chưa chấp nhận thông tin xác thực (401).',
               403: 'Provider chưa cấp quyền dùng mô hình này (403).',
               402: 'Provider yêu cầu kiểm tra hạn mức thanh toán (402).',
               400: 'Provider chưa chấp nhận cấu hình yêu cầu (400).',
               404: 'Provider không tìm thấy mô hình đã chọn (404).'}
    if status in reasons:
        return reasons[status]
    if isinstance(exc, TimeoutError) or 'Timeout' in type(exc).__name__:
        return 'Mô hình đã chọn phản hồi quá thời gian chờ.'
    return 'Mô hình đã chọn chưa trả được nội dung hợp lệ.'


def retrieval_query(query, history):
    # Previous conversation resolves referents, never substitutes for source evidence.
    followup = re.search(r"người đó|họ\b|việc đó|khoản đó|dự án đó|công ty đó|nó\b|còn .* thì", query, re.I)
    if not followup or not history:
        return query
    previous_user = next((m.get('content', '') for m in reversed(history) if m.get('role') == 'user'), '')
    previous_answer = next((m.get('content', '') for m in reversed(history) if m.get('role') == 'assistant'), '')
    return query + '\nCâu hỏi trước: ' + previous_user[:1500] + '\nTham chiếu hội thoại: ' + previous_answer[:1000]


def citations_valid(answer, count):
    citations = [int(n) for n in re.findall(r"\[(\d+)\]", answer)]
    return bool(citations) and all(1 <= n <= count for n in citations)


def preserves_constraints(text, quote):
    # Exact numerical boundaries must survive paraphrasing.
    pattern = r'(không quá|không vượt quá|tối đa|ít nhất|tối thiểu|lớn hơn|nhỏ hơn|dưới|trên|hơn)\s+(\d+(?:[.,]\d+)*)\s*(giây|phút|triệu|tỷ|%)?'
    operators = {'không quá':'<=','không vượt quá':'<=','tối đa':'<=',
                 'ít nhất':'>=','tối thiểu':'>=','lớn hơn':'>','trên':'>','hơn':'>',
                 'nhỏ hơn':'<','dưới':'<'}
    original = {}
    for operator, value, unit in re.findall(pattern, quote.lower()):
        original.setdefault((value, unit), set()).add(operators[operator])
    for operator, value, unit in re.findall(pattern, text.lower()):
        expected = original.get((value, unit))
        if expected and operators[operator] not in expected:
            return False
    # Preserve direct person/action pairs instead of reversing subject/object.
    action = r'(đề nghị|phê duyệt|xác nhận|chủ trì|chứng kiến|gửi|giữ|kiểm tra|quản lý|phụ trách|hoàn thiện)'
    modal = r'(?:(?:đã|sẽ|phải|cần|là người|chịu trách nhiệm)\s+)*'
    person = r'\b([A-ZĐÀ-Ỵ][a-zđà-ỵ]+(?:\s+[A-ZĐÀ-Ỵ][a-zđà-ỵ]+){1,3})\s+'
    for match in re.finditer(person + modal + action, text):
        name, verb = match.group(1), match.group(2)
        if not re.search(re.escape(name) + r'\s+' + modal + re.escape(verb), quote):
            return False
    return True


def render_grounded_answer(raw, sources):
    """Xử lý và chuẩn hóa câu trả lời có trích dẫn nguồn, nới lỏng quote match và fallback text."""
    try:
        data = json.loads(raw.removeprefix('```json').removeprefix('```').removesuffix('```').strip())
        claims = data.get('claims')
        if not isinstance(claims, list) or not claims:
            return None
        lines = []
        for claim in claims:
            index, quote, text = claim.get('source_id'), claim.get('quote'), claim.get('text')
            if type(index) is not int or not 1 <= index <= len(sources):
                return None
            if not isinstance(quote, str) or not quote.strip():
                return None
            # Nới lỏng kiểm tra quote bằng hàm is_quote_supported
            if not is_quote_supported(quote, sources[index-1]['content']):
                return None
            # Pha 1: Nếu LLM chỉ trả về quote mà không có text, tự động lấy text = quote
            if not isinstance(text, str) or not text.strip():
                text = quote.strip()
            if not preserves_constraints(text, quote):
                return None
            lines.append(f"{text.strip()} [{index}]")
        missing = data.get('missing_information', [])
        if not isinstance(missing, list) or any(not isinstance(item, str) for item in missing):
            return None
        return '\n\n'.join(lines + missing)
    except (ValueError, AttributeError, TypeError):
        return None


def extractive_answer(sources, query=''):
    """Trích xuất các đoạn bằng chứng nguyên văn khi mô hình không thể hoàn tất tổng hợp."""
    paragraphs = ['Các đoạn bằng chứng gốc liên quan được trích xuất từ tài liệu:']
    for index, source in enumerate(sources[:8], 1):
        passage = evidence_window(source['content'], query, 1800)
        paragraphs.append(f"**[{index}] {source['title']}**\n\n" + '\n'.join('> ' + line for line in passage.splitlines()))
    return '\n\n'.join(paragraphs)


class AgenticRAG:
    async def ainvoke(self, state, config=None):
        profile_id = state.get('model_profile')
        profile = resolve_profile(profile_id) if profile_id else None
        token = selected_profile.set(profile)
        try:
            result = await self._ainvoke(state, config)
            if profile is not None:
                result['model_used'] = profile.public()
            return result
        finally:
            selected_profile.reset(token)

    async def _ainvoke(self, state, config=None):
        query, tenant = state['query'], state.get('tenant_id')
        search_query = retrieval_query(query, state.get('history', [])[-6:])
        profile = selected_profile.get()
        steps = ([f'Mô hình sử dụng: {profile.label} · {profile.model}.'] if profile else [])
        steps.append('Tìm kiếm văn bản và vector trong không gian tài liệu hiện tại.')
        if search_query != query:
            steps.append('Đã dùng hội thoại để xác định đối tượng của câu hỏi tiếp nối.')
        lexical = await asyncio.to_thread(lexical_search, search_query, tenant)
        jobs = [asyncio.wait_for(asyncio.to_thread(vector_search, search_query, tenant), timeout=12)]
        if state.get('route', 'hybrid') == 'hybrid':
            jobs.append(graph_search(search_query, tenant))
        results = await asyncio.gather(*jobs, return_exceptions=True)
        vector = results[0] if isinstance(results[0], list) else []
        steps.append('Đã hợp nhất thứ hạng vector và văn bản.' if vector else 'Vector chưa khả dụng; dùng tìm kiếm văn bản.')
        facts = []
        if len(results) > 1:
            graph = results[1]
            if isinstance(graph, dict):
                facts = graph.get('raw_facts', [])
            steps.append('Đã đối chiếu nguồn quan hệ Neo4j.' if facts else 'Không có quan hệ Neo4j phù hợp hoặc dịch vụ chưa khả dụng.')
        ranked = fuse_sources(vector, lexical)
        sources = await asyncio.to_thread(expand_evidence, search_query, tenant, ranked, facts) if ranked or facts else []
        steps.append(f'Đã chọn {len(sources)} tài liệu gốc, mở rộng tham chiếu tối đa hai bước.')
        if not sources:
            answer = 'Tôi chưa tìm thấy thông tin phù hợp trong tài liệu của không gian này. Bạn có thể tải thêm tài liệu hoặc đặt câu hỏi cụ thể hơn.'
            return {**state, 'sources': [], 'final_answer': answer, 'draft_answer': answer,
                    'thought_process': steps, 'answer_mode': 'no_evidence'}
        context = '\n\n'.join(f"[{i+1}] {s['title']}\n{s['content']}" for i, s in enumerate(sources))

        # Pha 3: Tinh chỉnh Prompt với 4 Quy Tắc Cốt Lõi Chống Ảo Giác, Chống Bẫy Tiền Đề & Hỗ Trợ Tính Toán
        instruction = (
            'Bạn là Nori, trợ lý RAG chuyên sâu. Trả lời tiếng Việt, ngắn gọn, chính xác, chỉ dùng tài liệu gốc bên dưới. '
            'Mỗi nhận định phải trích dẫn [n] đúng tài liệu. Trả lời đủ từng phần câu hỏi: nguyên nhân, '
            'từng người chịu trách nhiệm, nhà cung cấp, số tiền và trạng thái khi được hỏi. '
            'Giữ nguyên điều kiện không quá/lớn hơn, mốc thời gian và phủ định. '
            'Phân biệt đã phê duyệt với sẽ phê duyệt, kế hoạch với kết quả thực tế. '
            'BẮT BUỘC TUÂN THỦ 4 QUY TẮC CỐT LÕI SAU:\n'
            '1. QUY TẮC THIẾU DỮ LIỆU: Nếu thực thể, số liệu (như tiền lương nhân sự, lợi nhuận công ty, chỉ số kho WH-BD-02, mức phạt chưa có điều khoản...) '
            'hoàn toàn không có trong tài liệu, BẮT BUỘC ghi vào missing_information hoặc trả lời rõ: "Tài liệu không cung cấp thông tin này", TUYỆT ĐỐI KHÔNG SUY ĐOÁN.\n'
            '2. QUY TẮC CHỐNG BẪY TIỀN ĐỀ: Kiểm tra thứ tự thời gian nhân - quả. Nếu câu hỏi gán ghép sự kiện xảy ra sau làm nguyên nhân cho sự kiện xảy ra trước, '
            'PHẢI BÁC BỎ TIỀN ĐỀ CỦA CÂU HỎI và nêu rõ mâu thuẫn thời gian.\n'
            '3. QUY TẮC TÍNH TOÁN & TRÁNH CỘNG TRÙNG: Khi tính tổng ngân sách, kiểm tra xem khoản thay đổi (CR) đã được gộp vào tổng hiện hành hay chưa. '
            'Nếu đã gộp, KHÔNG ĐƯỢC CỘNG LẶP LẦN HAI. Phân biệt rõ số tiền trước và sau VAT nếu có.\n'
            '4. QUY TẮC PHỦ QUYẾT THỜI GIAN: Văn bản có ngày hiệu lực mới hơn luôn PHỦ QUYẾT văn bản cũ (ví dụ CR-07 ngày 18/09 và STEER-09 ngày 22/09 thay thế mốc trong PRJ-AT-01). '
            'Phải lấy thông tin của văn bản mới nhất làm thông tin hiện hành.\n\n'
            'BẮT BUỘC trả JSON {"claims":[{"quote":"đoạn nguyên văn trong nguồn",'
            '"source_id":1,"text":"nhận định trả lời câu hỏi"}],"missing_information":[]}. '
            'Chọn quote trước rồi viết text sát nghĩa quote. source_id là số [n] của nguồn. '
            'Mỗi claim một ý, text không tự ghi mã trích dẫn. '
            'Với vai trò, mỗi claim chỉ nêu một người cùng hành động được ghi rõ trong quote. '
            'Không đổi chủ thể thành đối tượng, không đổi phê duyệt thành đề nghị. '
            'Không quá bao gồm bằng; không thay không quá bằng dưới. '
            'missing_information chỉ liệt kê phần câu hỏi chưa có dữ liệu. '
            'Chỉ trả lời các phần thực sự được hỏi, không thêm mục không liên quan.'
        )

        steps.append('Tổng hợp câu trả lời với trích dẫn từng nhận định.')
        try:
            answer = await complete([{'role': 'system', 'content': instruction},
                                     {'role': 'user', 'content': f'Câu hỏi cần trả lời: {search_query}\n\nNGUỒN:\n{context}'}], json_mode=True)
            rendered = render_grounded_answer(answer, sources)
            structured = rendered is not None
            answer = rendered or answer
        except Exception as exc:
            failure = model_failure_reason(exc)
            steps.append(failure + ' Trả bằng chứng gốc đã truy xuất.')
            answer = extractive_answer(sources, search_query)
            return {**state, 'sources': sources, 'draft_answer': '', 'final_answer': answer,
                    'thought_process': steps, 'answer_mode': 'extractive', 'failure_reason': failure}
        draft = answer
        failure = None
        mode = 'extractive'
        for attempt in range(2):
            try:
                valid, feedback = await verify_answer(search_query, context, answer)
            except Exception as exc:
                failure = model_failure_reason(exc)
                valid, feedback = None, failure
            if structured and valid is True and citations_valid(answer, len(sources)):
                mode = 'verified'
                steps.append('Bộ kiểm chứng xác nhận bản sửa bám sát nguồn.' if attempt else 'Bộ kiểm chứng xác nhận câu trả lời bám sát nguồn.')
                break
            if not structured:
                valid, feedback = False, 'Bản nháp không đạt hợp đồng quote. Giữ nguyên điều kiện số và cặp người/hành động trong đoạn gốc; mỗi người một claim.'
            if valid is None:
                steps.append(feedback + ' Chưa xác nhận được bản tổng hợp; chuyển sang trích nguyên văn bằng chứng.')
                break
            if attempt == 0:
                steps.append('Phát hiện lỗi hoặc trích dẫn không hợp lệ; hiệu chỉnh và kiểm chứng lại.')
                try:
                    answer = await complete([{'role':'system','content':instruction},
                        {'role':'user','content':f'Câu hỏi: {search_query}\nNguồn:\n{context}\nBản nháp:\n{answer}\nLỗi: {feedback}. Kiểm tra tất cả mã trích dẫn. Trả JSON theo cấu trúc yêu cầu.'}], json_mode=True)
                    rendered = render_grounded_answer(answer, sources)
                    structured = rendered is not None
                    answer = rendered or answer
                except Exception as exc:
                    failure = model_failure_reason(exc)
                    steps.append(failure + ' Chưa nhận được bản sửa; trả bằng chứng gốc.')
                    break
            else:
                steps.append('Bản sửa chưa đạt kiểm chứng; chuyển sang trích nguyên văn bằng chứng.')

        if mode != 'verified':
            answer = extractive_answer(sources, search_query)

        return {**state, 'sources': sources, 'draft_answer': draft, 'final_answer': answer,
                'thought_process': steps, 'answer_mode': mode, 'failure_reason': failure if mode != 'verified' else None}


agentic_rag_app = AgenticRAG()


# --- Node Functions for LangGraph Compatibility & Unit Testing ---

async def route_question_node(state: AgentState) -> AgentState:
    """Định tuyến câu hỏi tới vector, graph, hoặc hybrid."""
    llm = get_llm()
    query = state.get("query", "")
    route = "hybrid"
    reason = "Truy xuất mặc định kết hợp cả văn bản và quan hệ đồ thị."
    if llm and hasattr(llm, "with_structured_output"):
        try:
            structured_llm = llm.with_structured_output(RouteChoice)
            choice = await structured_llm.ainvoke(
                f"Phân loại câu hỏi sau để chọn nguồn truy xuất ('vector', 'graph', hoặc 'hybrid'): {query}"
            )
            route = choice.route
            reason = choice.reason
        except Exception:
            route = "hybrid"
    state["route"] = route
    thought = state.get("thought_process", [])
    thought.append(f"Chọn hướng truy xuất: '{route}' ({reason}).")
    state["thought_process"] = thought
    return state


async def retrieve_node(state: AgentState, config: Optional[dict] = None) -> AgentState:
    """Truy xuất tài liệu từ Vector DB và Neo4j Graphiti."""
    query = state.get("query", "")
    tenant_id = state.get("tenant_id")
    route = state.get("route", "hybrid")
    cfg = config or {}
    db = cfg.get("configurable", {}).get("db")

    retrieved = []
    sources = []

    if route in ("vector", "hybrid"):
        if db:
            chunks = vector_search_tool(db, query, tenant_id=tenant_id)
        else:
            chunks = vector_search(query, tenant_id=tenant_id)
        for c in chunks:
            retrieved.append(c)
            sources.append(c)

    if route in ("graph", "hybrid"):
        if db:
            graph_res = await graph_search_tool(db, query, tenant_id=tenant_id)
        else:
            graph_res = await graph_search(query, tenant_id=tenant_id)
        if graph_res:
            retrieved.append(graph_res)
            raw_facts = graph_res.get("raw_facts", [])
            for f in raw_facts:
                sources.append(f)

    state["retrieved_contexts"] = retrieved
    state["sources"] = sources
    return state


async def generate_node(state: AgentState) -> AgentState:
    """Sinh bản nháp câu trả lời từ ngữ cảnh đã truy xuất."""
    llm = get_llm()
    query = state.get("query", "")
    contexts = state.get("retrieved_contexts", [])
    ctx_text = "\n".join([c.get("content", "") if isinstance(c, dict) else str(c) for c in contexts])
    
    prompt = f"Trả lời câu hỏi: {query}\nDựa trên tài liệu:\n{ctx_text}"
    if llm:
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
    else:
        content = await complete([{"role": "user", "content": prompt}])

    state["draft_answer"] = content
    thought = state.get("thought_process", [])
    thought.append("Đã tạo dự thảo câu trả lời từ tài liệu truy xuất.")
    state["thought_process"] = thought
    return state


async def critic_node(state: AgentState) -> AgentState:
    """Kiểm chứng độ tin cậy và sự đầy đủ của câu trả lời."""
    eval_result = await critic_agent.evaluate(state)
    if eval_result.is_valid:
        state["final_answer"] = state.get("draft_answer", "")
    else:
        state["final_answer"] = ""
        state["critic_feedback"] = eval_result.feedback
        state["refinement_query"] = eval_result.refinement_query
    return state


def should_continue(state: AgentState) -> str:
    """Xác định tiếp tục vòng lặp tự sửa hay kết thúc."""
    if state.get("final_answer"):
        return "end"
    if state.get("loop_count", 0) >= 2:
        return "end"
    return "continue"

