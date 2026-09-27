import asyncio
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.app.config import settings
from backend.app.schemas import Base, Document, DocumentChunk
from backend.app.ingestion.chunker import DocumentChunker
from backend.app.ingestion.graph_extractor import graph_extractor

logger=logging.getLogger(__name__)
engine=create_engine(settings.postgres_url,pool_pre_ping=True,connect_args={'connect_timeout':5})
SessionLocal=sessionmaker(bind=engine,expire_on_commit=False)
def init_db():
    with engine.begin() as conn: conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
    Base.metadata.create_all(engine)
def get_db():
    with SessionLocal() as db: yield db

def tenant_filter(query, tenant_id):
    if tenant_id: return query.filter(Document.metadata_json['tenant_id'].astext == tenant_id)
    return query.filter(Document.metadata_json['tenant_id'].astext.is_(None))

async def index_document(doc_id):
    with SessionLocal() as db:
        doc=db.get(Document,doc_id)
        if not doc: return
        content,title,tenant=doc.content,doc.title,(doc.metadata_json or {}).get('tenant_id')
    vector_status,graph_status='failed','failed'
    episode=None
    try:
        chunks=await asyncio.wait_for(asyncio.to_thread(DocumentChunker().chunk_and_embed,content),timeout=45)
        with SessionLocal() as db:
            if not db.get(Document,doc_id): return
            db.query(DocumentChunk).filter_by(document_id=doc_id).delete()
            db.add_all([DocumentChunk(document_id=doc_id,**chunk) for chunk in chunks])
            db.commit()
        vector_status='ready'
    except Exception:
        logger.warning('Vector indexing unavailable for document %s',doc_id)
    try:
        episode=await asyncio.wait_for(graph_extractor.add_episode(title,content,group_id=tenant or 'global'),timeout=90)
        graph_status='ready'
    except Exception:
        logger.warning('Graph indexing unavailable for document %s',doc_id)
    with SessionLocal() as db:
        doc=db.get(Document,doc_id)
        if doc:
            doc.metadata_json={**(doc.metadata_json or {}),'vector_status':vector_status,'graph_status':graph_status,'graphiti_episode_uuid':episode,'status':'ready' if vector_status=='ready' else 'text_only'}
            db.commit()

class DatabaseSyncManager:
    async def ingest_document(self,db,title,content,tenant_id=None,index=True):
        doc=Document(title=title,content=content,metadata_json={'tenant_id':tenant_id,'status':'processing','graphiti_episode_uuid':None})
        db.add(doc); db.commit(); db.refresh(doc)
        if index:
            await index_document(doc.id)
            db.refresh(doc)
        return doc
    async def delete_document(self,db,doc_id):
        doc=db.get(Document,doc_id)
        if not doc: return False
        episode=(doc.metadata_json or {}).get('graphiti_episode_uuid')
        if episode: await asyncio.wait_for(graph_extractor.remove_episode(episode),timeout=15)
        db.delete(doc); db.commit()
        return True

db_sync_manager=DatabaseSyncManager()
