from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, Field, field_validator

Base = declarative_base()
def new_id(): return str(uuid4())
def now(): return datetime.now(timezone.utc)

class Document(Base):
    __tablename__ = 'documents'
    id = Column(String(36), primary_key=True, default=new_id)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSONB)
    created_at = Column(DateTime, default=now)
    chunks = relationship('DocumentChunk', back_populates='document', cascade='all, delete-orphan')

class DocumentChunk(Base):
    __tablename__ = 'document_chunks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(3072), nullable=False)
    document = relationship('Document', back_populates='chunks')

class Conversation(Base):
    __tablename__ = 'nori_conversations'
    id = Column(String(36), primary_key=True, default=new_id)
    title = Column(String(120), nullable=False)
    tenant_id = Column(String(120), nullable=False, default='')
    created_at = Column(DateTime, default=now)
    messages = relationship('Message', cascade='all, delete-orphan', order_by='Message.created_at')

class Message(Base):
    __tablename__ = 'nori_messages'
    id = Column(String(36), primary_key=True, default=new_id)
    conversation_id = Column(String(36), ForeignKey('nori_conversations.id', ondelete='CASCADE'), nullable=False)
    role = Column(String(20), nullable=False)
    text = Column(Text, nullable=False)
    sources = Column(JSONB, default=list)
    steps = Column(JSONB, default=list)
    created_at = Column(DateTime, default=now)

class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=1_000_000)
    metadata: dict | None = None
    @field_validator('title', 'content')
    @classmethod
    def nonempty(cls, value):
        if not value.strip(): raise ValueError('Nội dung không được để trống')
        return value.strip()

class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=8000)
    tenant_id: str | None = Field(default=None, max_length=120)
    conversation_id: str | None = Field(default=None, max_length=36)
    model_profile: str | None = Field(default=None, max_length=200)
    mode: str = Field(default='hybrid', pattern='^(hybrid|documents)$')
    @field_validator('query')
    @classmethod
    def nonempty(cls, value):
        if not value.strip(): raise ValueError('Câu hỏi không được để trống')
        return value.strip()
