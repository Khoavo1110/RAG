import asyncio
from unittest.mock import AsyncMock
import backend.app.agents.router as router


def setup(monkeypatch, verdicts):
    source = {"title": "Acceptance", "document_id": "missing-test-doc", "content": "Failover must not exceed 60 seconds.", "source_type": "text"}
    monkeypatch.setattr(router, "lexical_search", lambda *a: [source])
    monkeypatch.setattr(router, "vector_search", lambda *a: [])
    monkeypatch.setattr(router, "expand_evidence", lambda q,t,r,f: r)
    monkeypatch.setattr(router, "complete", AsyncMock(return_value="Failover exceeds 60 seconds [1]"))
    verifier = AsyncMock(side_effect=verdicts)
    monkeypatch.setattr(router, "verify_answer", verifier)
    return verifier


def test_repaired_answer_is_verified_again(monkeypatch):
    verifier = setup(monkeypatch, [(False, "Wrong threshold"), (True, "")])
    asyncio.run(router.AgenticRAG().ainvoke({"query": "failover", "route": "documents"}))
    assert verifier.await_count == 2


def test_invalid_repair_is_not_published(monkeypatch):
    setup(monkeypatch, [(False, "Wrong threshold"), (False, "Still wrong")])
    result = asyncio.run(router.AgenticRAG().ainvoke({"query": "failover", "route": "documents"}))
    assert "Failover exceeds" not in result["final_answer"]
    assert "Failover must not exceed 60 seconds." in result["final_answer"]


def test_unavailable_verifier_uses_evidence(monkeypatch):
    setup(monkeypatch, [TimeoutError()])
    result = asyncio.run(router.AgenticRAG().ainvoke({"query": "failover", "route": "documents"}))
    assert "Failover exceeds" not in result["final_answer"]
    assert result["answer_mode"] == "extractive"


def test_document_reference_expansion(monkeypatch):
    from types import SimpleNamespace
    import backend.app.agents.tools as tools
    expand = getattr(tools, "expand_evidence", None)
    assert callable(expand), "Document reference expansion is missing"
    docs = [SimpleNamespace(id="invoice",title="INV-X-042",content="See ACC-X-08.",metadata_json={}),
            SimpleNamespace(id="acceptance",title="ACC-X-08",content="Requires FIN-POL-01.",metadata_json={}),
            SimpleNamespace(id="policy",title="FIN-POL-01",content="Finance approves payment.",metadata_json={})]
    monkeypatch.setattr(tools,"scoped_documents",lambda tenant: docs)
    sources = expand("INV-X-042", "tenant", [{"document_id":"invoice", "content":"See ACC-X-08.","title":"INV-X-042"}], [])
    assert {s["document_id"] for s in sources} == {"invoice","acceptance","policy"}


def test_followup_uses_previous_question():
    make_query = getattr(router,"retrieval_query",None)
    assert callable(make_query), "Context-aware retrieval is missing"
    history = [{"role":"user","content":"Ai giao bản tích hợp cho Atlas?"},{"role":"assistant","content":"Hoàng Nam [1]"}]
    assert "Atlas" in make_query("Người đó làm cho công ty nào?", history)
    assert "Hoàng Nam" in make_query("Người đó làm cho công ty nào?", history)
    assert make_query("Ngân sách Lantern?",history) == "Ngân sách Lantern?"



def test_citation_indices_are_validated():
    check=getattr(router,"citations_valid",None)
    assert callable(check), "Citation validation is missing"
    assert check("Supported [1]",1)
    assert not check("Unsupported [9]",1)
    assert not check("Uncited answer",1)


def test_malformed_verifier_is_unknown(monkeypatch):
    import backend.app.agents.critic as critic
    monkeypatch.setattr(critic, "complete", AsyncMock(return_value='{"is_valid":"true","feedback":"ok"}'))
    verdict, _ = asyncio.run(critic.verify_answer("question","[1] Evidence","Answer [1]"))
    assert verdict is None


def test_verifier_rejects_unsupported_claim(monkeypatch):
    import backend.app.agents.critic as critic
    monkeypatch.setattr(critic,"complete",AsyncMock(return_value='{"is_valid":true,"complete":true,"claims":[{"supported":false,"source_ids":[1]}],"feedback":"Wrong threshold"}'))
    verdict, _ = asyncio.run(critic.verify_answer("question","[1] Evidence","Answer [1]"))
    assert verdict is False


def test_inverse_references_are_retrieved(monkeypatch):
    from types import SimpleNamespace
    import backend.app.agents.tools as tools
    docs=[SimpleNamespace(id="contract",title="CON-X-01",content="Contract",metadata_json={}),
          SimpleNamespace(id="policy",title="POL-X-01",content="# POL-X-01\n\nPayment policy applies to CON-X-01.",metadata_json={})]
    monkeypatch.setattr(tools,"scoped_documents",lambda tenant:docs)
    found=tools.expand_evidence("CON-X-01 payment", "tenant", [{"document_id":"contract"}], [])
    assert "policy" in {s["document_id"] for s in found}


def test_ollama_context_is_explicit(monkeypatch):
    import httpx
    import backend.app.agents.critic as critic
    original=httpx.AsyncClient
    captured=[]
    def handler(request):
        import json
        payload=json.loads(request.content);captured.append(payload)
        return httpx.Response(200,json={"message":{"content":"Supported [1]"}})
    monkeypatch.setattr(critic.settings,"LLM_PROVIDER","ollama")
    monkeypatch.setattr(httpx,"AsyncClient",lambda **kwargs:original(transport=httpx.MockTransport(handler),**kwargs))
    assert asyncio.run(critic.complete([{"role":"user","content":"question"}])) == "Supported [1]"
    assert captured[0]["options"]["num_ctx"] >= 16384
