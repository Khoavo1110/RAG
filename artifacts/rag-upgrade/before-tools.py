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

def lexical_search(query,tenant_id=None,limit=5):
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

def vector_search_tool(db,query,tenant_id=None,limit=5):
    vector=DocumentChunker().generate_embeddings([query])[0]
    distance=DocumentChunk.embedding.cosine_distance(vector)
    rows=tenant_filter(db.query(DocumentChunk,distance.label('distance')).join(Document),tenant_id).order_by(distance).limit(limit).all()
    return [dict(title=c.document.title,document_id=c.document_id,content=c.content,chunk_index=c.chunk_index,source_type='vector',score=round(1-d,4)) for c,d in rows if d<0.65]

def vector_search(query,tenant_id):
    with SessionLocal() as db: return vector_search_tool(db,query,tenant_id)

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
