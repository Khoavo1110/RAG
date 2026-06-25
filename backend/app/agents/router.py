from typing import TypedDict, List, Dict, Any, Literal
import json
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END

from backend.app.agents.critic import get_llm, critic_agent
from backend.app.agents.tools import vector_search_tool, graph_search_tool

# Define agent state schema
class AgentState(TypedDict):
    query: str
    tenant_id: str | None
    route: str  # "vector", "graph", "hybrid"
    retrieved_contexts: List[Dict[str, Any]]
    draft_answer: str
    critic_feedback: str | None
    refinement_query: str | None
    loop_count: int
    final_answer: str
    thought_process: List[str]
    sources: List[Dict[str, Any]]

# Schema for intent routing
class RouteChoice(BaseModel):
    route: Literal["vector", "graph", "hybrid"] = Field(
        description="Select 'vector' for specific facts/descriptions, 'graph' for relations/multi-hop queries, 'hybrid' if both are needed."
    )
    reason: str = Field(description="Reasoning for this route choice.")

def format_contexts_to_string(retrieved_contexts: List[Dict[str, Any]]) -> str:
    """Helper to format all accumulated contexts into a single prompt context."""
    vector_texts = []
    graph_texts = []
    
    seen_vector_contents = set()
    seen_graph_facts = set()

    for ctx in retrieved_contexts:
        if ctx["source_type"] == "vector":
            content = ctx["content"]
            if content not in seen_vector_contents:
                seen_vector_contents.add(content)
                vector_texts.append(f"- [{ctx['title']}]: {content}")
        elif ctx["source_type"] == "graph":
            # Avoid repeating exactly same fact context strings
            ctx_str = ctx["context_string"]
            if ctx_str not in seen_graph_facts:
                seen_graph_facts.add(ctx_str)
                graph_texts.append(ctx_str)
                
    combined = ""
    if vector_texts:
        combined += "=== VECTOR DATABASE CONTEXT ===\n" + "\n".join(vector_texts) + "\n\n"
    if graph_texts:
        combined += "=== KNOWLEDGE GRAPH CONTEXT ===\n" + "\n".join(graph_texts) + "\n\n"
        
    return combined

# ====== NODE 1: ROUTER ======
async def route_question_node(state: AgentState) -> Dict[str, Any]:
    llm = get_llm(temperature=0.0)
    
    system_prompt = (
        "You are an Intent Classifier / Router in a Hybrid RAG system.\n"
        "Analyze the user's query and decide the best retrieval route:\n"
        "1. 'vector': For queries asking about specific facts, detailed descriptions of a single entity, or general document lookup (e.g., 'What did CEO Pham Minh Tuấn say?', 'Báo cáo công nghệ FPT 2026 nói về gì?').\n"
        "2. 'graph': For queries asking about relationships between entities, multi-hop reasoning, connections, or comparing entities (e.g., 'FPT Software hợp tác với công ty nào?', 'Ai đang cung cấp chip cho đối tác của FPT?').\n"
        "3. 'hybrid': For complex queries that ask about both specific content details AND relationships, requiring a combined search.\n\n"
        "Respond in JSON matching the schema of RouteChoice."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "User Query: {query}")
    ])
    
    messages = prompt.format_messages(query=state["query"])
    
    thought = f"Phân tích ý định câu hỏi: '{state['query']}'"
    route = "hybrid"  # fallback default
    
    try:
        structured_llm = llm.with_structured_output(RouteChoice)
        res = await structured_llm.ainvoke(messages)
        route = res.route
        thought += f" -> Chọn hướng truy xuất: '{route}' (Lý do: {res.reason})"
    except Exception as e:
        # Fallback manual parsing
        thought += f" (Lỗi gọi structured output: {e}, mặc định chọn 'hybrid')"
        try:
            messages.append(("user", "IMPORTANT: Respond ONLY with a raw JSON matching: {\"route\": \"vector\"|\"graph\"|\"hybrid\", \"reason\": \"string\"}"))
            res = await llm.ainvoke(messages)
            content = res.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            data = json.loads(content.strip())
            route = data.get("route", "hybrid")
            thought += f" -> Chọn hướng truy xuất (manual parse): '{route}'"
        except:
            pass

    return {
        "route": route,
        "thought_process": [thought]
    }

# ====== NODE 2: RETRIEVER ======
async def retrieve_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    db: Session = config.get("configurable", {}).get("db")
    if not db:
        raise ValueError("Database session (db) must be provided in RunnableConfig configurable.")
        
    query = state.get("refinement_query") or state["query"]
    tenant_id = state.get("tenant_id")
    route = state["route"]
    loop_count = state.get("loop_count", 0)
    
    thought = f"Vòng {loop_count}: Thực hiện truy xuất với câu truy vấn: '{query}' qua kênh: '{route}'"
    new_contexts = []
    
    if route in ("vector", "hybrid"):
        vector_res = vector_search_tool(db, query, tenant_id=tenant_id)
        new_contexts.extend(vector_res)
        thought += f" -> Tìm thấy {len(vector_res)} đoạn văn từ Vector DB."
        
    if route in ("graph", "hybrid"):
        graph_res = await graph_search_tool(db, query, tenant_id=tenant_id)
        new_contexts.append(graph_res)
        num_facts = len(graph_res.get("raw_facts", []))
        thought += f" -> Tìm thấy {num_facts} mối quan hệ từ Knowledge Graph."
        
    # Append to accumulated contexts
    current_contexts = state.get("retrieved_contexts") or []
    updated_contexts = current_contexts + new_contexts
    
    # Update sources lists
    sources = []
    seen_sources = set()
    for ctx in updated_contexts:
        if ctx["source_type"] == "vector":
            source_key = (ctx["title"], ctx["document_id"])
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources.append({
                    "title": ctx["title"],
                    "document_id": ctx["document_id"],
                    "source_type": "vector"
                })
        elif ctx["source_type"] == "graph":
            for fact in ctx["raw_facts"]:
                source_key = (fact["fact"], tuple(fact["episodes"]))
                if source_key not in seen_sources:
                    seen_sources.add(source_key)
                    sources.append({
                        "fact": fact["fact"],
                        "name": fact["name"],
                        "episodes": fact["episodes"],
                        "source_type": "graph",
                        "source_node_uuid": fact.get("source_node_uuid"),
                        "target_node_uuid": fact.get("target_node_uuid"),
                        "source_node_name": fact.get("source_node_name"),
                        "target_node_name": fact.get("target_node_name")
                    })

    return {
        "retrieved_contexts": updated_contexts,
        "sources": sources,
        "thought_process": [thought]
    }

# ====== NODE 3: GENERATOR ======
async def generate_node(state: AgentState) -> Dict[str, Any]:
    llm = get_llm(temperature=0.3)
    
    query = state["query"]
    context_str = format_contexts_to_string(state["retrieved_contexts"])
    loop_count = state.get("loop_count", 0)
    
    system_prompt = (
        "You are a helpful AI Assistant.\n"
        "Your job is to answer the user's query based ONLY on the provided context (which contains Vector chunks and/or Knowledge Graph facts).\n"
        "You must write a comprehensive, clear, and direct answer. Do not add details not found in the context.\n"
        "If the context does not contain enough information to answer, state that you don't have enough information.\n"
        "Respond in the same language as the query (Vietnamese)."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "User Query: {query}\n\nRetrieved Context:\n{context}")
    ])
    
    messages = prompt.format_messages(query=query, context=context_str)
    
    res = await llm.ainvoke(messages)
    draft_answer = res.content.strip()
    
    thought = f"Vòng {loop_count}: Đã tạo dự thảo câu trả lời."
    
    return {
        "draft_answer": draft_answer,
        "thought_process": [thought]
    }

# ====== NODE 4: CRITIC ======
async def critic_node(state: AgentState) -> Dict[str, Any]:
    query = state["query"]
    context_str = format_contexts_to_string(state["retrieved_contexts"])
    draft_answer = state["draft_answer"]
    loop_count = state.get("loop_count", 0)
    
    # Run evaluation
    critic_res = await critic_agent.evaluate(query, context_str, draft_answer)
    
    thought = f"Vòng {loop_count}: Đánh giá câu trả lời từ Critic Agent -> Hợp lệ: {critic_res.is_valid}"
    if not critic_res.is_valid:
        thought += f" | Phản hồi: '{critic_res.feedback}' | Gợi ý truy vấn tiếp: '{critic_res.refinement_query}'"
        
    return {
        "critic_feedback": critic_res.feedback,
        "refinement_query": critic_res.refinement_query if not critic_res.is_valid else None,
        "final_answer": draft_answer if critic_res.is_valid else "",
        "thought_process": [thought]
    }

# ====== CONDITIONAL EDGE ======
def should_continue(state: AgentState) -> str:
    # If critic validates the answer OR we hit max loops (3), we stop
    if state["final_answer"] != "" or state.get("loop_count", 0) >= 2:
        return "end"
    return "continue"

# increment loop count in state transitions
def increment_loop_count(state: AgentState) -> Dict[str, Any]:
    return {"loop_count": state.get("loop_count", 0) + 1}

# ====== BUILD GRAPH ======
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("router", route_question_node)
workflow.add_node("retriever", retrieve_node)
workflow.add_node("generator", generate_node)
workflow.add_node("critic", critic_node)
workflow.add_node("increment_loop", increment_loop_count)

# Define transitions
workflow.set_entry_point("router")
workflow.add_edge("router", "retriever")
workflow.add_edge("retriever", "generator")
workflow.add_edge("generator", "critic")

workflow.add_conditional_edges(
    "critic",
    should_continue,
    {
        "continue": "increment_loop",
        "end": END
    }
)
workflow.add_edge("increment_loop", "retriever")

# Compile LangGraph
agentic_rag_app = workflow.compile()
