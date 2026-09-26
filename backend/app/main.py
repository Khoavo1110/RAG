import asyncio
import logging
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.schemas import Document, Conversation, Message, DocumentCreate, QueryRequest
from backend.app.ingestion.database_sync import engine, init_db, get_db, tenant_filter, db_sync_manager, index_document
from backend.app.ingestion.graph_extractor import graph_extractor
from backend.app.agents.router import agentic_rag_app
from backend.app.agents.critic import provider_config
from backend.app.models import model_catalog, resolve_profile, refresh_model_catalog

logger=logging.getLogger(__name__)
@asynccontextmanager
async def lifespan(app):
    await asyncio.to_thread(init_db)
    yield
    await graph_extractor.close()
    engine.dispose()

app=FastAPI(title='Nori API',version='3.0.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173','http://127.0.0.1:5173'],allow_methods=['GET','POST','DELETE'],allow_headers=['Content-Type'],allow_credentials=False)
@app.middleware('http')
async def size_limit(request,call_next):
    from starlette.responses import JSONResponse
    if int(request.headers.get('content-length','0'))>2_000_000:
        return JSONResponse({'detail':'Tệp quá lớn. Giới hạn 1 MB văn bản.'},status_code=413)
    return await call_next(request)

def document_json(doc):
    return dict(id=doc.id,title=doc.title,content=doc.content,metadata=doc.metadata_json,created_at=doc.created_at,characters=len(doc.content))
def conversation_json(c,full=False):
    result=dict(id=c.id,title=c.title,tenant_id=c.tenant_id or None,created_at=c.created_at)
    if full: result['messages']=[dict(id=m.id,role=m.role,text=m.text,sources=m.sources or [],steps=m.steps or []) for m in c.messages]
    return result

@app.get('/health')
@app.get('/api/health')
async def health():
    async def postgres():
        try:
            def check():
                with engine.connect() as conn: conn.execute(text('SELECT 1'))
            await asyncio.to_thread(check)
            return True
        except Exception: return False
    async def neo4j():
        from neo4j import AsyncGraphDatabase
        try:
            async with AsyncGraphDatabase.driver(settings.NEO4J_URI,auth=(settings.NEO4J_USERNAME,settings.NEO4J_PASSWORD),connection_timeout=3) as driver:
                await asyncio.wait_for(driver.verify_connectivity(),timeout=4)
            return True
        except Exception: return False
    async def model():
        if settings.LLM_PROVIDER!='ollama': return bool(provider_config()[1])
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r=await client.get(settings.OLLAMA_BASE_URL.removesuffix('/v1').rstrip('/')+'/api/tags')
                return r.is_success and any(m['name']==settings.OLLAMA_MODEL or m['name']==settings.OLLAMA_MODEL+':latest' for m in r.json().get('models',[]))
        except Exception: return False
    pg,graph,llm=await asyncio.gather(postgres(),neo4j(),model())
    return dict(status='healthy' if pg and llm else 'degraded',services=dict(postgres=pg,neo4j=graph,llm=llm),provider=settings.LLM_PROVIDER,model=provider_config()[2])

@app.get('/api/models')
async def models():
    return await refresh_model_catalog()

@app.get('/api/workspaces')
def workspaces(db:Session=Depends(get_db)):
    tenants=db.query(Document.metadata_json['tenant_id'].astext).distinct().all()
    return [None]+sorted({t[0] for t in tenants if t[0]})

@app.get('/api/documents')
def documents(tenant_id:str|None=None,db:Session=Depends(get_db)):
    return [document_json(d) for d in tenant_filter(db.query(Document),tenant_id).order_by(Document.created_at.desc()).all()]

@app.post('/api/ingest',status_code=201)
async def ingest(body:DocumentCreate,tasks:BackgroundTasks,db:Session=Depends(get_db)):
    tenant=(body.metadata or {}).get('tenant_id')
    if tenant is not None and (not isinstance(tenant,str) or len(tenant)>120): raise HTTPException(422,'Không gian không hợp lệ.')
    doc=await db_sync_manager.ingest_document(db,body.title,body.content,tenant,index=False)
    tasks.add_task(index_document,doc.id)
    return document_json(doc)

@app.delete('/api/documents/{doc_id}',status_code=204)
async def delete_document(doc_id:str,tenant_id:str|None=None,db:Session=Depends(get_db)):
    doc=tenant_filter(db.query(Document),tenant_id).filter(Document.id==doc_id).first()
    if not doc: raise HTTPException(404,'Không tìm thấy tài liệu.')
    if (doc.metadata_json or {}).get('status')=='processing': raise HTTPException(409,'Tài liệu đang được xử lý; vui lòng thử lại sau.')
    try: await db_sync_manager.delete_document(db,doc_id)
    except Exception: raise HTTPException(503,'Chưa xóa được dữ liệu đồ thị. Vui lòng thử lại.')

@app.get('/api/conversations')
def conversations(tenant_id:str|None=None,db:Session=Depends(get_db)):
    return [conversation_json(c) for c in db.query(Conversation).filter_by(tenant_id=tenant_id or '').order_by(Conversation.created_at.desc()).all()]
@app.get('/api/conversations/{cid}')
def conversation(cid:str,tenant_id:str|None=None,db:Session=Depends(get_db)):
    c=db.query(Conversation).filter_by(id=cid,tenant_id=tenant_id or '').first()
    if not c: raise HTTPException(404,'Không tìm thấy hội thoại.')
    return conversation_json(c,True)
@app.delete('/api/conversations/{cid}',status_code=204)
def delete_conversation(cid:str,tenant_id:str|None=None,db:Session=Depends(get_db)):
    c=db.query(Conversation).filter_by(id=cid,tenant_id=tenant_id or '').first()
    if not c: raise HTTPException(404,'Không tìm thấy hội thoại.')
    db.delete(c);db.commit()

@app.post('/api/query')
async def query(body:QueryRequest,db:Session=Depends(get_db)):
    profile = None
    if body.model_profile:
        try:
            profile = resolve_profile(body.model_profile)
        except ValueError as exc:
            raise HTTPException(422, str(exc))
    c=None
    if body.conversation_id:
        c=db.query(Conversation).filter_by(id=body.conversation_id,tenant_id=body.tenant_id or '').first()
        if not c: raise HTTPException(404,'Không tìm thấy hội thoại.')
    history=[{'role':m.role,'content':m.text} for m in c.messages[-6:]] if c else []
    try:
        result=await asyncio.wait_for(agentic_rag_app.ainvoke(dict(query=body.query,tenant_id=body.tenant_id,route=body.mode,history=history,model_profile=body.model_profile)),timeout=420 if profile and profile.mode=='api' else 240)
    except asyncio.TimeoutError: raise HTTPException(504,'Mô hình phản hồi quá lâu. Vui lòng thử lại.')
    except Exception:
        logger.exception('Query failed')
        raise HTTPException(503,'Không nhận được câu trả lời từ mô hình. Hãy kiểm tra Ollama và thử lại.')
    if not c:
        c=Conversation(title=body.query[:100],tenant_id=body.tenant_id or '')
        db.add(c);db.flush()
    db.add_all([Message(conversation_id=c.id,role='user',text=body.query),Message(conversation_id=c.id,role='assistant',text=result['final_answer'],sources=result['sources'],steps=result['thought_process'])])
    db.commit()
    return dict(query=body.query,answer=result['final_answer'],sources=result['sources'],thought_process=result['thought_process'],conversation_id=c.id,model_used=result.get('model_used'),answer_mode=result.get('answer_mode'),failure_reason=result.get('failure_reason'))
