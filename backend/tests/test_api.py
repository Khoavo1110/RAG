import asyncio
from uuid import uuid4
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas import Document, Conversation
from backend.app.ingestion.database_sync import SessionLocal
from backend.app.agents.tools import lexical_search, tokens
from backend.app.agents.router import AgenticRAG

@pytest.fixture
def client(monkeypatch):
    import backend.app.main as main
    monkeypatch.setattr(main,'index_document',AsyncMock())
    with TestClient(app) as client: yield client

@pytest.fixture
def tenant():
    name='nori-test-'+str(uuid4())
    yield name
    with SessionLocal() as db:
        for c in db.query(Conversation).filter_by(tenant_id=name): db.delete(c)
        for d in db.query(Document).filter(Document.metadata_json['tenant_id'].astext==name): db.delete(d)
        db.commit()

def test_rejects_blank_and_oversize_input(client):
    assert client.post('/api/query',json={'query':'   '}).status_code==422
    assert client.post('/api/ingest',json={'title':'x','content':' '}).status_code==422
    assert client.post('/api/ingest',json={'title':'x'*256,'content':'x'}).status_code==422
    assert client.post('/api/query',content='x'*2_000_001,headers={'Content-Type':'application/json'}).status_code==413

def test_document_scope_and_lexical_retrieval(client,tenant):
    r=client.post('/api/ingest',json={'title':'Nori test','content':'Nori stores documents in PostgreSQL and uses Neo4j for relationships.','metadata':{'tenant_id':tenant}})
    assert r.status_code==201
    doc=r.json(); assert doc['metadata']['status']=='processing'
    assert len(client.get('/api/documents',params={'tenant_id':tenant}).json())==1
    assert doc['id'] not in [d['id'] for d in client.get('/api/documents').json()]
    assert client.delete('/api/documents/'+doc['id']).status_code==404
    assert client.delete('/api/documents/'+doc['id'],params={'tenant_id':tenant}).status_code==409
    assert lexical_search('PostgreSQL',tenant)[0]['document_id']==doc['id']
    assert not lexical_search('unfindablexyz',tenant)

def test_conversation_persistence_and_scope(client,tenant,monkeypatch):
    import backend.app.main as main
    mock=AsyncMock(return_value={'final_answer':'Grounded answer [1]','sources':[{'title':'Test','content':'Evidence','source_type':'text'}],'thought_process':['Retrieved evidence']})
    monkeypatch.setattr(main.agentic_rag_app,'ainvoke',mock)
    r=client.post('/api/query',json={'query':'First question','tenant_id':tenant})
    assert r.status_code==200
    cid=r.json()['conversation_id']
    assert len(client.get('/api/conversations/'+cid,params={'tenant_id':tenant}).json()['messages'])==2
    assert client.get('/api/conversations/'+cid).status_code==404
    assert client.post('/api/query',json={'query':'Second question','conversation_id':cid}).status_code==404
    r=client.post('/api/query',json={'query':'Follow up','tenant_id':tenant,'conversation_id':cid})
    assert r.status_code==200
    assert len(mock.call_args.args[0]['history'])==2
    assert len(client.get('/api/conversations/'+cid,params={'tenant_id':tenant}).json()['messages'])==4
    assert client.delete('/api/conversations/'+cid,params={'tenant_id':tenant}).status_code==204
    assert client.get('/api/conversations/'+cid,params={'tenant_id':tenant}).status_code==404

def test_failed_model_does_not_save_partial_conversation(client,tenant,monkeypatch):
    import backend.app.main as main
    monkeypatch.setattr(main.agentic_rag_app,'ainvoke',AsyncMock(side_effect=RuntimeError('private failure')))
    r=client.post('/api/query',json={'query':'Question','tenant_id':tenant})
    assert r.status_code==503
    assert 'private failure' not in r.text
    assert client.get('/api/conversations',params={'tenant_id':tenant}).json()==[]

def test_no_evidence_does_not_call_model(monkeypatch):
    import backend.app.agents.router as router
    monkeypatch.setattr(router,'lexical_search',lambda *args:[])
    monkeypatch.setattr(router,'vector_search',lambda *args:[])
    complete=AsyncMock();monkeypatch.setattr(router,'complete',complete)
    result=asyncio.run(AgenticRAG().ainvoke({'query':'unfindable','route':'documents'}))
    assert not result['sources']
    complete.assert_not_called()
    assert 'chưa tìm thấy' in result['final_answer']

def test_failed_critic_is_explicit(monkeypatch):
    import backend.app.agents.router as router
    source={'title':'Test','document_id':'1','content':'Evidence','source_type':'text'}
    monkeypatch.setattr(router,'lexical_search',lambda *args:[source])
    monkeypatch.setattr(router,'vector_search',lambda *args:[])
    monkeypatch.setattr(router,'expand_evidence',lambda q,t,r,f:r)
    monkeypatch.setattr(router,'complete',AsyncMock(return_value='Answer [1]'))
    monkeypatch.setattr(router,'verify_answer',AsyncMock(side_effect=TimeoutError()))
    result=asyncio.run(AgenticRAG().ainvoke({'query':'question','route':'documents'}))
    assert 'Answer [1]' not in result['final_answer']
    assert 'Evidence' in result['final_answer']
    assert result['answer_mode']=='extractive'

def test_vietnamese_normalization():
    assert 'do' in tokens('đồ thị')
    assert 'postgresql' in tokens('PostgreSQL')
