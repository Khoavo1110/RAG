from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.app.config import settings
from backend.app.schemas import Base, Document, DocumentChunk
from backend.app.ingestion.chunker import DocumentChunker
from backend.app.ingestion.graph_extractor import graph_extractor

# Initialize Postgres engine and SessionLocal
engine = create_engine(settings.postgres_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all tables in PostgreSQL (e.g. documents, document_chunks)."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Database session generator."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DatabaseSyncManager:
    def __init__(self):
        self.chunker = DocumentChunker()

    async def ingest_document(self, db: Session, title: str, content: str, tenant_id: str | None = None) -> Document:
        """
        Orchestrate parallel ingestion:
        1. Extract and store knowledge graph in Neo4j via Graphiti.
        2. Chunk and generate embeddings, store in Postgres (PGVector).
        """
        # Step 1: Ingest into Neo4j Graphiti
        episode_uuid = await graph_extractor.add_episode(
            name=title,
            content=content,
            source_description=f"tenant:{tenant_id}" if tenant_id else "global",
            group_id=tenant_id
        )

        # Step 2: Create Postgres Document record
        metadata = {
            "tenant_id": tenant_id,
            "graphiti_episode_uuid": episode_uuid
        }
        db_doc = Document(
            title=title,
            content=content,
            metadata_json=metadata
        )
        db.add(db_doc)
        db.flush()  # Generate document ID

        # Step 3: Chunk and embed document for Vector search
        chunks_data = self.chunker.chunk_and_embed(content)
        for chunk in chunks_data:
            db_chunk = DocumentChunk(
                document_id=db_doc.id,
                content=chunk["content"],
                chunk_index=chunk["chunk_index"],
                embedding=chunk["embedding"]
            )
            db.add(db_chunk)

        db.commit()
        db.refresh(db_doc)
        return db_doc

    async def delete_document(self, db: Session, doc_id: str) -> bool:
        """
        Cascade Delete:
        1. Retrieve document metadata to get Graphiti episode UUID.
        2. Remove the episode from Neo4j (Graphiti cleans up nodes/edges).
        3. Delete the document from Postgres (ondelete="CASCADE" automatically deletes chunks).
        """
        db_doc = db.query(Document).filter(Document.id == doc_id).first()
        if not db_doc:
            return False

        # Retrieve Graphiti episode UUID from metadata
        metadata = db_doc.metadata_json or {}
        episode_uuid = metadata.get("graphiti_episode_uuid")

        # Step 1: Delete from Neo4j Graphiti
        if episode_uuid:
            try:
                await graph_extractor.remove_episode(episode_uuid)
            except Exception as e:
                # Log error but continue deleting from local database
                print(f"Error removing episode {episode_uuid} from Graphiti: {e}")

        # Step 2: Delete from Postgres (Cascade handles chunks)
        db.delete(db_doc)
        db.commit()
        return True

# Singleton instance
db_sync_manager = DatabaseSyncManager()
