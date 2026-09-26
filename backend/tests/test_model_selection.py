import asyncio
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
import backend.app.agents.critic as critic
from backend.app.main import app


def test_model_catalog_exposes_no_credentials():
    with TestClient(app) as client:
        response=client.get('/api/models')
    assert response.status_code==200
    body=response.json()
    assert {'local','api'} <= {p['mode'] for p in body['profiles']}
    assert all('api_key' not in p and 'base_url' not in p for p in body['profiles'])


def test_unknown_profile_is_rejected_before_inference(monkeypatch):
    import backend.app.main as main
    inference=AsyncMock();monkeypatch.setattr(main.agentic_rag_app,'ainvoke',inference)
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
