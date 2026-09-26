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
    with SessionLocal() as db: return await graph_search_tool(db,query,tenant_id)


CODE = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")


def scoped_documents(tenant_id):
    with SessionLocal() as db:
        return tenant_filter(db.query(Document), tenant_id).all()


def fuse_sources(vector, lexical):
    """Reciprocal rank fusion avoids mixing cosine similarity with BM25 scores."""
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
    """Resolve explicit references and episode provenance only inside this workspace.

    Graph facts select original documents; model-extracted facts are never themselves
    presented as authoritative evidence. Expansion is bounded to two reference hops.
    """
    docs = scoped_documents(tenant_id)
    by_id = {d.id: d for d in docs}
    codes = {}
    for doc in docs:
        # Only a document's title/header identifies it, not references in its body.
        header = doc.content.split('\n', 1)[0]
        identity = doc.title.upper() + (' ' + header.upper() if header.startswith('#') else '')
        for code in CODE.findall(identity):
            codes.setdefault(code, []).append(doc.id)
    requested = set(CODE.findall(query.upper()))
    acronyms = set(re.findall(r'\b[A-Z]{3,}\b', query))
    catalog_terms = set(tokens(' '.join(d.title + ' ' + d.content for d in docs)))
    missing_acronyms = {word for word in acronyms if word.lower() not in catalog_terms}
    if len(missing_acronyms) >= 2 and missing_acronyms == acronyms:
        return []
    anchors = [key for code in requested for key in codes.get(code, [])]
    # An explicit unknown record must not be answered with unrelated similar records.
    if requested and not anchors and not any(code in d.content.upper() for d in docs for code in requested):
        return []
    seeds = list(dict.fromkeys(anchors + [s['document_id'] for s in ranked if s.get('document_id') in by_id]))
    episodes = {episode for fact in graph_facts for episode in fact.get('episodes', [])}
    graph_ids = [d.id for d in docs if (d.metadata_json or {}).get('graphiti_episode_uuid') in episodes]
    # Reserve capacity for relationships rather than filling it with shallow hits.
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
        ordered = sorted(candidates, key=lambda key: (
            -len(terms.intersection(tokens(by_id[key].title + ' ' + by_id[key].content))),
            -rank_scores.get(key, 0), by_id[key].title))
        frontier = ordered[:max_documents-len(selected)]
        selected.extend(frontier)
        if not frontier:
            break
    for key in seeds:
        if key not in selected and len(selected) < max_documents:
            selected.append(key)
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
