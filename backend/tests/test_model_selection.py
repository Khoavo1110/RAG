import asyncio
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
import backend.app.agents.critic as critic
from backend.app.main import app


def test_model_catalog_exposes_no_credentials(monkeypatch):
    import backend.app.main as main
    from backend.app.models import model_catalog
    monkeypatch.setattr(main,'refresh_model_catalog',AsyncMock(return_value=model_catalog()))
    with TestClient(app) as client:
        response=client.get('/api/models')
    assert response.status_code==200
    body=response.json()
    assert {'local','api'} <= {p['mode'] for p in body['profiles']}
    assert all('api_key' not in p and 'base_url' not in p for p in body['profiles'])


def test_unknown_profile_is_rejected_before_inference(monkeypatch):
    import backend.app.main as main
    inference=AsyncMock(side_effect=RuntimeError("Profile validation was skipped"));monkeypatch.setattr(main.agentic_rag_app,'ainvoke',inference)
    with TestClient(app) as client:
        response=client.post('/api/query',json={'query':'Question','model_profile':'unknown-provider'})
    assert response.status_code==422
    inference.assert_not_called()


def test_model_context_is_request_scoped():
    selected=getattr(critic,'selected_profile',None)
    assert selected is not None, 'Request-scoped model selection is missing'
    from backend.app.models import resolve_profile
    local=resolve_profile('ollama::qwen2.5:3b')
    cloud=resolve_profile('gemini::gemini-2.5-flash')
    async def call(profile):
        token=selected.set(profile)
        try:
            await asyncio.sleep(0)
            return critic.provider_config()[2]
        finally:selected.reset(token)
    async def run():return await asyncio.gather(call(local),call(cloud))
    assert asyncio.run(run())==['qwen2.5:3b','gemini-2.5-flash']
    assert selected.get() is None


def test_hermes_credentials_are_preferred_and_never_public(monkeypatch,tmp_path):
    import backend.app.models as models
    config=tmp_path/'config.yaml';config.write_text('providers: {gemini: {models: [gemini-2.5-flash]}}')
    monkeypatch.setattr(models,'hermes_home',lambda:tmp_path)
    monkeypatch.setattr(models,'dotenv_values',lambda path:{'GEMINI_API_KEY':'hermes-test-secret'})
    monkeypatch.setattr(models.settings,'GEMINI_API_KEY','project-test-secret')
    models.get_profiles.cache_clear()
    try:
        profile=models.get_profiles()['gemini::gemini-2.5-flash']
        assert profile.api_key=='hermes-test-secret'
        import json
        assert 'test-secret' not in json.dumps(models.model_catalog())
        assert 'test-secret' not in repr(profile)
    finally:models.get_profiles.cache_clear()


def test_failed_request_resets_model_context(monkeypatch):
    from backend.app.agents.router import AgenticRAG
    rag=AgenticRAG()
    monkeypatch.setattr(rag,'_ainvoke',AsyncMock(side_effect=RuntimeError('failure')))
    import pytest
    with pytest.raises(RuntimeError):asyncio.run(rag.ainvoke({'query':'question','model_profile':'ollama::qwen2.5:3b'}))
    assert critic.selected_profile.get() is None


def test_catalog_marks_unlisted_models_and_caches_probe(monkeypatch):
    import httpx
    import backend.app.models as models
    profiles={p.id:p for p in [models.ModelProfile('ollama','local','http://localhost:11434/v1','ollama'),models.ModelProfile('gemini','listed','https://example.test/v1','test-secret'),models.ModelProfile('gemini','retired','https://example.test/v1','test-secret')]}
    monkeypatch.setattr(models,'get_profiles',lambda:profiles)
    monkeypatch.setattr(models,'_catalog_snapshot',None)
    monkeypatch.setattr(models,'_catalog_updated',0)
    monkeypatch.setattr(models,'_catalog_lock',asyncio.Lock())
    calls=[]
    original=httpx.AsyncClient
    def handler(request):
        calls.append(request)
        return httpx.Response(200,json={'models':[{'name':'local'}]} if request.url.host=='localhost' else {'data':[{'id':'listed'}]})
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs))
    async def run():
        first=await models.refresh_model_catalog()
        second=await models.refresh_model_catalog()
        return first,second
    first,second=asyncio.run(run())
    assert first==second and len(calls)==2
    assert next(p for p in first['profiles'] if p['model']=='retired')['available'] is False
    assert first['api_default_id']=='gemini::listed'


def test_cloud_completion_uses_selected_provider(monkeypatch):
    from types import SimpleNamespace
    from backend.app.models import ModelProfile
    create=AsyncMock(return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok":true}'))]))
    clients=[]
    class Client:
        def __init__(self,**kwargs):
            clients.append(kwargs);self.chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
    monkeypatch.setattr(critic,'AsyncOpenAI',Client)
    profile=ModelProfile('gemini','selected-model','https://example.test/v1','fake-secret')
    token=critic.selected_profile.set(profile)
    try:assert asyncio.run(critic.complete([{'role':'user','content':'question'}],json_mode=True))=='{"ok":true}'
    finally:critic.selected_profile.reset(token)
    assert clients[0]['base_url']=='https://example.test/v1'
    assert create.call_args.kwargs['model']=='selected-model'
    assert create.call_args.kwargs['response_format']=={'type':'json_object'}
    assert create.call_args.kwargs['reasoning_effort']=='low'


def test_provider_failure_is_reported_without_leaking_details(monkeypatch):
    import backend.app.agents.router as router
    class ApiFailure(RuntimeError):status_code=429
    monkeypatch.setattr(router,'lexical_search',lambda *a:[{'document_id':'1','title':'Test','content':'Evidence'}])
    monkeypatch.setattr(router,'vector_search',lambda *a:[])
    monkeypatch.setattr(router,'expand_evidence',lambda q,t,r,f:r)
    monkeypatch.setattr(router,'complete',AsyncMock(side_effect=ApiFailure('private-key-do-not-show')))
    result=asyncio.run(router.AgenticRAG().ainvoke({'query':'question','route':'documents'}))
    assert '429' in result.get('failure_reason','')
    assert 'private-key-do-not-show' not in str(result)


def test_grounding_preserves_inclusive_threshold():
    from backend.app.agents.router import render_grounded_answer
    import json
    sources=[{'content':'Điều kiện là failover không quá 60 giây.'}]
    raw=json.dumps({'claims':[{'source_id':1,'quote':sources[0]['content'],'text':'Failover phải dưới 60 giây.'}]},ensure_ascii=False)
    assert render_grounded_answer(raw,sources) is None


def test_grounding_preserves_actor_action():
    from backend.app.agents.router import render_grounded_answer
    import json
    sources=[{'content':'An Bình hoàn thiện hồ sơ; Mai Lan phê duyệt chi tiền.'}]
    raw=json.dumps({'claims':[{'source_id':1,'quote':sources[0]['content'],'text':'Mai Lan đề nghị chi tiền.'}]},ensure_ascii=False)
    assert render_grounded_answer(raw,sources) is None
