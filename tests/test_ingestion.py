import os
import sys
import asyncio

# Add current workspace root to python path to resolve backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from backend.app.ingestion.database_sync import init_db, SessionLocal, db_sync_manager
from backend.app.schemas import Document, DocumentChunk
from backend.app.ingestion.graph_extractor import graph_extractor

async def test_pipeline():
    print("1. Initializing database tables...")
    init_db()
    print("Database tables initialized successfully!")

    print("\n2. Initializing Neo4j indices and constraints...")
    await graph_extractor.initialize()
    print("Neo4j indices initialized successfully!")

    # Open db session
    db = SessionLocal()

    try:
        title = "Báo cáo Nhân sự và Công nghệ FPT 2026"
        content = (
            "FPT Software hợp tác chiến lược với NVIDIA để phát triển nhà máy AI. "
            "Trong thỏa thuận này, CEO Phạm Minh Tuấn cho biết FPT sẽ đầu tư 200 triệu USD "
            "để mua chip GPU của NVIDIA nhằm phục vụ việc đào tạo mô hình ngôn ngữ lớn cho khách hàng tại Việt Nam."
        )
        tenant_id = "tenant_fpt_001"

        print(f"\n3. Ingesting sample document: '{title}'...")
        doc = await db_sync_manager.ingest_document(db, title, content, tenant_id)
        
        print(f"Postgres Ingestion Successful!")
        print(f" - Document ID: {doc.id}")
        print(f" - Title: {doc.title}")
        print(f" - Metadata: {doc.metadata_json}")

        # Check Chunks in Postgres
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
        print(f" - Number of Vector Chunks created in Postgres: {len(chunks)}")
        for idx, chunk in enumerate(chunks):
            print(f"   * Chunk {idx} content: '{chunk.content[:60]}...'")
            print(f"   * Chunk {idx} embedding dimension: {len(chunk.embedding)}")

        # Check Neo4j Graphiti
        episode_uuid = doc.metadata_json.get("graphiti_episode_uuid")
        print(f"\n4. Verifying Neo4j Episode Ingest (UUID: {episode_uuid})...")
        
        # We can search the graph
        search_results = await graph_extractor.graphiti.search("FPT Software hợp tác với ai?")
        print("Neo4j Search Results (FPT Software partner query):")
        for res in search_results:
            print(f" - Fact: {getattr(res, 'fact', 'N/A')}")
            print(f" - Name: {getattr(res, 'name', 'N/A')}")

        # Wait a second to inspect
        await asyncio.sleep(2)

        # Step 5: Test Cascade Delete
        print(f"\n5. Testing Cascade Delete for Document ID: {doc.id}...")
        success = await db_sync_manager.delete_document(db, doc.id)
        print(f"Delete operation status: {success}")

        # Verify Postgres is empty
        doc_count = db.query(Document).filter(Document.id == doc.id).count()
        chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).count()
        print(f" - Documents remaining in Postgres with ID {doc.id}: {doc_count}")
        print(f" - Chunks remaining in Postgres for Document: {chunk_count}")

        # Verify Neo4j has removed the episode
        print(" - Verify Graphiti episode removal...")
        try:
            nodes_and_edges = await graph_extractor.graphiti.get_nodes_and_edges_by_episode([episode_uuid])
            print(f"   * Nodes/edges linked to removed episode: {nodes_and_edges}")
        except Exception as e:
            print(f"   * Episode not found as expected (Success). Details: {e}")

    finally:
        db.close()
        await graph_extractor.close()

if __name__ == "__main__":
    asyncio.run(test_pipeline())
