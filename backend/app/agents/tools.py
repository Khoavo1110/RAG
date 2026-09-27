import asyncio
import math
import re
import unicodedata
from collections import Counter
from backend.app.schemas import Document, DocumentChunk
from backend.app.ingestion.database_sync import SessionLocal, tenant_filter
from backend.app.ingestion.chunker import DocumentChunker
from backend.app.ingestion.graph_extractor import graph_extractor

STOP=set('va la cua cho cac mot nhung voi duoc trong co toi ban nay gi nao the de ve hay bao nhieu'.split())
def tokens(text):
    folded=unicodedata.normalize('NFD',text.lower()).replace('đ','d')
    return [x for x in re.findall(r'[a-z0-9]+',''.join(c for c in folded if not unicodedata.combining(c))) if x not in STOP and len(x)>1]

def lexical_search(query,tenant_id=None,limit=12):
    with SessionLocal() as db:
        docs=tenant_filter(db.query(Document),tenant_id).all()
        corpus=[dict(title=d.title,document_id=d.id,content=c,chunk_index=i,source_type='text')
                for d in docs for i,c in enumerate(DocumentChunker().split_text(d.content))]
    terms=set(tokens(query))
    if not terms or not corpus: return []
    counts=[Counter(tokens(c['title']+' '+c['content'])) for c in corpus]
    avg=sum(sum(c.values()) for c in counts)/len(counts) or 1
    ranked=[]
    for chunk,count in zip(corpus,counts):
        score=0.0
        for term in terms:
            tf=count[term]
            df=sum(term in c for c in counts)
            idf=math.log(1+(len(counts)-df+0.5)/(df+0.5))
            score+=idf*tf*2.2/(tf+1.2*(0.25+0.75*sum(count.values())/avg))
        if score>0: ranked.append({**chunk,'score':round(score,4)})
    return sorted(ranked,key=lambda c:c['score'],reverse=True)[:limit]

def vector_search_tool(db,query,tenant_id=None,limit=12):
    vector=DocumentChunker().generate_embeddings([query])[0]
    distance=DocumentChunk.embedding.cosine_distance(vector)
    rows=tenant_filter(db.query(DocumentChunk,distance.label('distance')).join(Document),tenant_id).order_by(distance).limit(limit).all()
    return [dict(title=c.document.title,document_id=c.document_id,content=c.content,chunk_index=c.chunk_index,source_type='vector',score=round(1-d,4)) for c,d in rows if d<0.65]

def vector_search(query,tenant_id):
    with SessionLocal() as db: return vector_search_tool(db,query,tenant_id,limit=12)

async def graph_search_tool(db,query,tenant_id=None):
    groups=[tenant_id] if tenant_id else None
    edges=await asyncio.wait_for(graph_extractor.graphiti.search(query,group_ids=groups),timeout=12)
    edges=edges.edges if hasattr(edges,'edges') else edges
    docs=tenant_filter(db.query(Document),tenant_id).all()
    allowed={(d.metadata_json or {}).get('graphiti_episode_uuid') for d in docs}-{None}
    facts=[dict(fact=e.fact,episodes=e.episodes,source_node_uuid=e.source_node_uuid,target_node_uuid=e.target_node_uuid) for e in edges if allowed.intersection(e.episodes)]
    return dict(source_type='graph',context_string='\n'.join(f['fact'] for f in facts),raw_facts=facts)

async def graph_search(query,tenant_id):
    with SessionLocal() as db: return await graph_search_tool(db, query, tenant_id)


import datetime
from typing import Optional

CODE = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")
ENTITY_REGEX = re.compile(r'\b[A-ZĐÀ-Ỵ][a-zđà-ỵ]+(?:\s+[A-ZĐÀ-Ỵ][a-zđà-ỵ]+){1,3}\b')
SPECIAL_ENTITIES = [
    'ATLAS', 'LANTERN', 'ID-GATE', 'BUG-17', 'WH-BD-02', 'FPT', 'NVIDIA',
    'BẮC SAO', 'BẮC SAO TECH', 'KẾT NỐI SỐ', 'VÂN HẢI CLOUD', 'VÂN HẢI',
    'AN PHÚ', 'AN PHÚ RETAIL', 'MINH AN', 'MINH AN SUPPLY', 'MINH PHÚC'
]
DATE_PATTERN = re.compile(r'\b(?:ngày\s+)?(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2,4}))?\b', re.IGNORECASE)
AMENDMENT_INDICATORS = ('cr-', 'steer-', 'thay đổi', 'điều chỉnh', 'biên bản', 'phụ lục', 'hóa đơn đợt hai', 'nghiệm thu', 'bổ sung')


def extract_document_date(title: str, content: str = "") -> Optional[datetime.date]:
    """Trích xuất mốc thời gian nổi bật nhất từ tiêu đề hoặc đầu tài liệu."""
    header = (content or "").split('\n', 2)[:2]
    text_to_check = f"{title} " + " ".join(header)
    matches = DATE_PATTERN.findall(text_to_check)
    dates = []
    for match in matches:
        d, m, y = match[0], match[1], match[2]
        day = int(d)
        month = int(m)
        year = int(y) if y else 2026
        if year < 100:
            year += 2000
        try:
            if 1 <= month <= 12 and 1 <= day <= 31:
                dates.append(datetime.date(year, month, day))
        except ValueError:
            continue
    return max(dates) if dates else None


def is_amendment_doc(title: str, content: str = "") -> bool:
    """Kiểm tra văn bản có tính chất điều chỉnh/cập nhật/quyết định mới hơn hay không."""
    t = (title + ' ' + (content[:250] if content else '')).lower()
    return any(ind in t for ind in AMENDMENT_INDICATORS)


def scoped_documents(tenant_id):
    with SessionLocal() as db:
        return tenant_filter(db.query(Document), tenant_id).all()


def fuse_sources(vector, lexical):
    """Reciprocal rank fusion kết hợp Recency Boost cho các văn bản sửa đổi/thay đổi mới nhất."""
    scores, records = {}, {}
    for ranked in (vector, lexical):
        seen = set()
        for rank, source in enumerate(ranked, 1):
            key = source.get('document_id')
            if not key or key in seen:
                continue
            seen.add(key)
            scores[key] = scores.get(key, 0) + 1 / (60 + rank)
            records.setdefault(key, source)

    # Áp dụng hệ số Recency Boost (1.3x) cho văn bản điều chỉnh hoặc có mốc thời gian mới (từ tháng 9/2026)
    for key, score in list(scores.items()):
        rec = records[key]
        title = rec.get('title', '')
        content = rec.get('content', '')
        doc_date = extract_document_date(title, content)
        if is_amendment_doc(title, content) or (doc_date and doc_date >= datetime.date(2026, 9, 1)):
            scores[key] = score * 1.3

    return [dict(records[key], fusion_score=scores[key])
            for key in sorted(scores, key=lambda key: -scores[key])]


def evidence_window(content, query, limit=2400):
    """Keep whole small documents; select original paragraphs for larger ones."""
    if len(content) <= limit:
        return content
    terms = set(tokens(query))
    paragraphs = content.split('\n\n')
    scored = sorted(range(len(paragraphs)),
                    key=lambda i: -len(terms.intersection(tokens(paragraphs[i]))))
    selected, length = [], 0
    for index in scored:
        paragraph = paragraphs[index]
        if len(paragraph) > limit:
            if selected:
                continue
            for chunk in DocumentChunker(chunk_size=limit, chunk_overlap=min(100, max(0, limit-1))).split_text(paragraph):
                if terms.intersection(tokens(chunk)):
                    return chunk
            return paragraph[:limit]
        if length + len(paragraph) + 2 <= limit:
            selected.append(index)
            length += len(paragraph) + 2
    return '\n\n'.join(paragraphs[i] for i in sorted(selected))


def expand_evidence(query, tenant_id, ranked, graph_facts, max_documents=12, max_hops=2):
    """Resolve explicit references, named entities, and episode provenance inside this workspace.

    Mở rộng thực thể tên riêng (người, công ty, dự án) và mã văn bản để không bỏ sót liên kết logic đa chặng.
    """
    docs = scoped_documents(tenant_id)
    by_id = {d.id: d for d in docs}
    codes = {}
    entities_map = {}
    for doc in docs:
        header = doc.content.split('\n', 1)[0]
        identity = doc.title.upper() + (' ' + header.upper() if header.startswith('#') else '')
        for code in CODE.findall(identity):
            codes.setdefault(code, []).append(doc.id)
            entities_map.setdefault(code, []).append(doc.id)
        # Bắt tên riêng tiếng Việt (nhân sự, đối tác)
        for name in ENTITY_REGEX.findall(doc.title + " " + doc.content[:400]):
            entities_map.setdefault(name.upper(), []).append(doc.id)
        # Bắt các thực thể đặc biệt (dự án, hệ thống)
        for spec in SPECIAL_ENTITIES:
            if spec in identity or spec in doc.content[:400].upper():
                entities_map.setdefault(spec, []).append(doc.id)

    requested = set(CODE.findall(query.upper()))
    requested_names = set(name.upper() for name in ENTITY_REGEX.findall(query))
    requested_specials = {spec for spec in SPECIAL_ENTITIES if spec in query.upper()}
    all_requested = requested | requested_names | requested_specials

    acronyms = set(re.findall(r'\b[A-Z]{3,}\b', query))
    catalog_terms = set(tokens(' '.join(d.title + ' ' + d.content for d in docs)))
    missing_acronyms = {word for word in acronyms if word.lower() not in catalog_terms}
    if len(missing_acronyms) >= 2 and missing_acronyms == acronyms:
        return []

    # Anchors bao gồm cả mã văn bản và các thực thể được nhắc đến trong câu hỏi
    anchors = [key for ent in all_requested for key in entities_map.get(ent, [])]
    if requested and not any(code in entities_map for code in requested) and not any(code in d.content.upper() for d in docs for code in requested):
        return []

    seeds = list(dict.fromkeys(anchors + [s['document_id'] for s in ranked if s.get('document_id') in by_id]))
    episodes = {episode for fact in graph_facts for episode in fact.get('episodes', [])}
    graph_ids = [d.id for d in docs if (d.metadata_json or {}).get('graphiti_episode_uuid') in episodes]
    selected = list(dict.fromkeys(seeds[:6] + graph_ids[:2]))[:max_documents]
    frontier = list(selected)
    terms = set(tokens(query))
    references = {doc.id: set(CODE.findall(doc.content.upper())) for doc in docs}
    identities = {key: {code for code, ids in codes.items() if key in ids} for key in by_id}
    rank_scores = {source['document_id']: source.get('fusion_score', 0) for source in ranked}

    for _ in range(max_hops):
        candidates = set()
        for key in frontier:
            for code in references[key]:
                candidates.update(codes.get(code, []))
            # Inverse links locate policies and minutes which cite a contract/invoice.
            candidates.update(other for other in by_id if references[other].intersection(identities[key]))
        candidates.difference_update(selected)

        def candidate_sort_key(k):
            d = by_id[k]
            kw_match = len(terms.intersection(tokens(d.title + ' ' + d.content)))
            recency = 1 if is_amendment_doc(d.title, d.content) else 0
            score = rank_scores.get(k, 0)
            return (-kw_match, -recency, -score, d.title)

        ordered = sorted(candidates, key=candidate_sort_key)
        frontier = ordered[:max_documents-len(selected)]
        selected.extend(frontier)
        if not frontier:
            break

    for key in seeds:
        if key not in selected and len(selected) < max_documents:
            selected.append(key)

    # Ưu tiên các văn bản sửa đổi/thay đổi lên đầu danh sách để LLM thấy ngay mốc thời gian cập nhật
    def selected_order(k):
        d = by_id[k]
        is_amend = 0 if is_amendment_doc(d.title, d.content) else 1
        is_seed = 0 if k in seeds[:6] else 1
        return (is_amend, is_seed)

    selected.sort(key=selected_order)

    result, remaining = [], 24000
    for key in selected:
        doc = by_id[key]
        content = evidence_window(doc.content, query, min(2400, remaining))
        if not content or remaining < 300:
            break
        result.append(dict(document_id=key, title=doc.title, content=content,
                           source_type='document', retrieval_method='exact' if key in anchors else
                           'hybrid' if key in seeds[:6] else 'reference'))
        remaining -= len(content)
    return result

