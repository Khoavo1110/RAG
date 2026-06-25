from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, Field

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSONB, nullable=True)  # Store tenant_id, source etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # Vector column. text-embedding-004 has 768 dimensions
    embedding = Column(Vector(768), nullable=False)

    document = relationship("Document", back_populates="chunks")


# ====== PYDANTIC MODELS (FOR API) ======

class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the document")
    content: str = Field(..., min_length=1, description="Content of the document")
    metadata: dict | None = Field(default=None, description="Metadata dictionary e.g., tenant_id")

class DocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    metadata: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    tenant_id: str | None = None

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[dict]
    thought_process: list[str] | None = None
