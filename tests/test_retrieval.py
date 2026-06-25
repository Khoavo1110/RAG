import os
import sys
import asyncio
from dotenv import load_dotenv

# Add current workspace root to python path to resolve backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from backend.app.ingestion.database_sync import init_db, SessionLocal, db_sync_manager
from backend.app.schemas import DocumentChunk
from backend.app.ingestion.graph_extractor import graph_extractor
from backend.app.ingestion.chunker import DocumentChunker

async def main():
    print("1. Đang khởi tạo cơ sở dữ liệu và Neo4j...")
    init_db()
    await graph_extractor.initialize()
    
    db = SessionLocal()
    chunker = DocumentChunker()
    
    # Dữ liệu mẫu để nạp thử nghiệm
    title = "Sự kiện Hợp tác Công nghệ FPT và NVIDIA"
    content = (
        "Vào ngày 24/06/2026, FPT Software đã công bố ký kết hợp tác chiến lược với tập đoàn NVIDIA "
        "để phát triển nhà máy trí tuệ nhân tạo (AI Factory) đầu tiên tại Việt Nam. "
        "CEO FPT Software, ông Phạm Minh Tuấn, nhấn mạnh khoản đầu tư trị giá 200 triệu USD "
        "nhằm mua sắm chip GPU H100 của NVIDIA phục vụ việc xây dựng và huấn luyện mô hình ngôn ngữ lớn cho khách hàng."
    )
    tenant_id = "tenant_fpt_001"
    
    print("\n2. Đang nạp dữ liệu mẫu vào cả 2 cơ sở dữ liệu (Postgres Vector & Neo4j Graph)...")
    doc = await db_sync_manager.ingest_document(db, title, content, tenant_id)
    print(f"-> Nạp thành công! ID tài liệu lưu ở Postgres: {doc.id}")
    
    # Câu hỏi thử nghiệm để truy xuất thông tin
    query = "FPT đầu tư bao nhiêu tiền để mua chip GPU của NVIDIA?"
    print(f"\n3. Thực hiện truy xuất thử nghiệm cho câu hỏi: '{query}'")
    
    # --- TRUY XUẤT 1: VECTOR DB (POSTGRESQL + PGVECTOR) ---
    print("\n🔎 === [TRUY XUẤT VECTOR - POSTGRES] ===")
    query_vector = chunker.generate_embeddings([query])[0]
    
    # Thực hiện truy xuất vector khoảng cách cosine sử dụng pgvector trong SQLAlchemy
    vector_results = db.query(DocumentChunk).order_by(
        DocumentChunk.embedding.cosine_distance(query_vector)
    ).limit(2).all()
    
    for idx, chunk in enumerate(vector_results):
        print(f"  [Chunk {idx + 1}]")
        print(f"   - Nội dung đoạn văn: \"{chunk.content}\"")
        print(f"   - ID Document liên kết: {chunk.document_id}")

    # --- TRUY XUẤT 2: KNOWLEDGE GRAPH (NEO4J + GRAPHITI) ---
    print("\n🕸️ === [TRUY XUẤT ĐỒ THỊ - NEO4J] ===")
    graph_results = await graph_extractor.graphiti.search(query)
    
    if not graph_results:
        print("  Không tìm thấy quan hệ phù hợp trong Đồ thị tri thức.")
    else:
        for idx, res in enumerate(graph_results):
            print(f"  [Quan hệ {idx + 1}]")
            print(f"   - Mối quan hệ: {getattr(res, 'name', 'N/A')}")
            print(f"   - Sự thật trích xuất (Fact): \"{getattr(res, 'fact', 'N/A')}\"")
            
    # --- DỌN DẸP DỮ LIỆU ---
    print("\n4. Tiến hành dọn dẹp dữ liệu thử nghiệm...")
    await db_sync_manager.delete_document(db, doc.id)
    print("-> Dữ liệu thử nghiệm đã được dọn dẹp sạch sẽ (Cascade Delete thành công).")
    
    db.close()
    await graph_extractor.close()

if __name__ == "__main__":
    asyncio.run(main())
