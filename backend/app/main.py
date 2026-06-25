from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import traceback

from backend.app.config import settings
from backend.app.ingestion.database_sync import init_db, get_db, db_sync_manager
from backend.app.ingestion.graph_extractor import graph_extractor
from backend.app.schemas import DocumentCreate, DocumentResponse, QueryRequest, QueryResponse
from backend.app.agents.router import agentic_rag_app

def get_langfuse_callback():
    """Returns a Langfuse CallbackHandler if credentials are configured."""
    if (settings.LANGFUSE_PUBLIC_KEY and 
        settings.LANGFUSE_PUBLIC_KEY != "your_langfuse_public_key_here" and
        settings.LANGFUSE_SECRET_KEY and 
        settings.LANGFUSE_SECRET_KEY != "your_langfuse_secret_key_here"):
        try:
            from langfuse.callback import CallbackHandler
            return CallbackHandler(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                host=settings.LANGFUSE_HOST
            )
        except Exception as e:
            print(f"Failed to load Langfuse CallbackHandler: {e}")
    return None

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 1. Startup: initialize databases
    print("Starting up: Initializing database and Neo4j indices...")
    try:
        init_db()
        await graph_extractor.initialize()
        print("Initialization successful!")
    except Exception as e:
        print(f"Error during startup initialization: {e}")
    
    yield
    
    # 2. Shutdown: close graph connections
    print("Shutting down: Closing graph connections...")
    try:
        await graph_extractor.close()
        print("Shutdown complete!")
    except Exception as e:
        print(f"Error during shutdown: {e}")

app = FastAPI(
    title="Agentic RAG 2.0 Backend",
    description="FastAPI Backend for Hybrid Vector & Knowledge Graph Agentic RAG System",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/ingest", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document(doc_in: DocumentCreate, db: Session = Depends(get_db)):
    """
    Ingest a document into both Postgres (Vector DB) and Neo4j (Knowledge Graph).
    """
    tenant_id = doc_in.metadata.get("tenant_id") if doc_in.metadata else None
    try:
        doc = await db_sync_manager.ingest_document(
            db=db,
            title=doc_in.title,
            content=doc_in.content,
            tenant_id=tenant_id
        )
        # Reformat response matching Pydantic DocumentResponse
        return DocumentResponse(
            id=doc.id,
            title=doc.title,
            content=doc.content,
            metadata=doc.metadata_json,
            created_at=doc.created_at
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}"
        )

@app.post("/api/query", response_model=QueryResponse)
async def query_agentic_rag(req: QueryRequest, db: Session = Depends(get_db)):
    """
    Execute the multi-agent reasoning loop (LangGraph) for hybrid retrieval and generation.
    """
    # 1. Prepare initial graph state
    initial_state = {
        "query": req.query,
        "tenant_id": req.tenant_id,
        "route": "hybrid",
        "retrieved_contexts": [],
        "draft_answer": "",
        "critic_feedback": None,
        "refinement_query": None,
        "loop_count": 0,
        "final_answer": "",
        "thought_process": [],
        "sources": []
    }
    
    # 2. Run graph with db session passed to configurable context
    config = {
        "configurable": {
            "db": db
        }
    }
    
    # 3. Add Langfuse callback if available
    lf_callback = get_langfuse_callback()
    if lf_callback:
        config["callbacks"] = [lf_callback]
    
    try:
        # Run graph execution
        result = await agentic_rag_app.ainvoke(initial_state, config=config)
        
        # Determine the final answer (fallback to draft if final_answer wasn't validated by loop count limit)
        answer = result.get("final_answer")
        if not answer:
            answer = result.get("draft_answer") or "Không thể tìm thấy hoặc sinh câu trả lời phù hợp dựa trên ngữ cảnh đã có."
            
        return QueryResponse(
            query=req.query,
            answer=answer,
            sources=result.get("sources", []),
            thought_process=result.get("thought_process", [])
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent loop execution failed: {str(e)}"
        )
