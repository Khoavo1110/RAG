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


import pytest
import json

@pytest.mark.parametrize("reply,expected", [
    ('not json',None), ('[]',None),
    ('{"is_valid":false,"feedback":"bad"}',False),
    ('{"is_valid":true}',None),
    ('{"is_valid":true,"complete":false,"claims":[{}]}',False),
    ('{"is_valid":true,"complete":true,"claims":[{}]}',None),
    ('{"is_valid":true,"complete":true,"claims":[{"supported":true,"source_ids":[9],"quote":"Evidence"}]}',False),
    ('{"is_valid":true,"complete":true,"claims":[{"supported":true,"source_ids":[1],"quote":"Invented evidence"}]}',False),
    ('{"is_valid":true,"complete":true,"claims":[{"supported":true,"source_ids":[1],"quote":"Evidence"}]}',True),
])
def test_verifier_evidence_contract(monkeypatch,reply,expected):
    import backend.app.agents.critic as critic
    monkeypatch.setattr(critic,"complete",AsyncMock(return_value=reply))
    verdict,_=asyncio.run(critic.verify_answer("question","[1] Source\nEvidence","Answer [1]"))
    assert verdict is expected


def test_fusion_preserves_lexical_only_documents():
    from backend.app.agents.tools import fuse_sources
    vector=[{"document_id":"a","content":"vector"}]*6
    lexical=[{"document_id":"b","content":"Critical payment policy"},{"document_id":"a","content":"text"}]
    assert {s["document_id"] for s in fuse_sources(vector,lexical)} == {"a","b"}
    assert fuse_sources(vector,lexical)[0]["document_id"] == "a"


def test_long_evidence_preserves_relevant_original_passage():
    from backend.app.agents.tools import evidence_window
    text="Noise "*1000+"\n\nFailover must not exceed 60 seconds.\n\n"+"Other "*1000
    result=evidence_window(text,"failover",100)
    assert "Failover must not exceed 60 seconds." in result
    assert len(result)<=100
    assert evidence_window("Noise "*1000,"absent",100) in "Noise "*1000


def test_unknown_record_and_foreign_document_are_excluded(monkeypatch):
    from types import SimpleNamespace
    import backend.app.agents.tools as tools
    docs=[SimpleNamespace(id="local",title="DOC-A-01",content="# DOC-A-01\nLocal evidence",metadata_json={})]
    monkeypatch.setattr(tools,"scoped_documents",lambda tenant:docs)
    assert not tools.expand_evidence("DOC-Z-99", "tenant", [{"document_id":"local"}], [])
    assert not tools.expand_evidence("question", "tenant", [{"document_id":"foreign"}], [])


def test_graph_provenance_selects_original_documents(monkeypatch):
    from types import SimpleNamespace
    import backend.app.agents.tools as tools
    docs=[SimpleNamespace(id="local",title="Evidence",content="Original evidence",metadata_json={"graphiti_episode_uuid":"allowed"})]
    monkeypatch.setattr(tools,"scoped_documents",lambda tenant:docs)
    assert not tools.expand_evidence("question","tenant",[],[{"episodes":["foreign"]}])
    sources=tools.expand_evidence("question","tenant",[],[{"episodes":["allowed"],"fact":"Hallucinated graph claim"}])
    assert sources[0]["content"] == "Original evidence"
    assert "Hallucinated" not in sources[0]["content"]


def test_expansion_hop_and_document_limits(monkeypatch):
    from types import SimpleNamespace
    import backend.app.agents.tools as tools
    docs=[SimpleNamespace(id=str(i),title=f"DOC-X-{i:02}",content=f"# DOC-X-{i:02}\n\nSee DOC-X-{i+1:02}",metadata_json={}) for i in range(6)]
    monkeypatch.setattr(tools,"scoped_documents",lambda tenant:docs)
    sources=tools.expand_evidence("DOC-X-00","tenant",[{"document_id":"0"}],[],max_hops=1)
    assert {s["document_id"] for s in sources} == {"0","1"}
    assert len(tools.expand_evidence("DOC-X-00","tenant",[{"document_id":"0"}],[],max_documents=1)) == 1


def test_graph_search_filters_foreign_episodes(monkeypatch):
    from types import SimpleNamespace
    import backend.app.agents.tools as tools
    docs=[SimpleNamespace(metadata_json={"graphiti_episode_uuid":"local"})]
    edges=[SimpleNamespace(fact=episode,episodes=[episode],source_node_uuid="a",target_node_uuid="b") for episode in ("local","foreign")]
    graph=SimpleNamespace(search=AsyncMock(return_value=edges))
    monkeypatch.setattr(tools,"graph_extractor",SimpleNamespace(graphiti=graph))
    monkeypatch.setattr(tools,"tenant_filter",lambda query,tenant:SimpleNamespace(all=lambda:docs))
    db=SimpleNamespace(query=lambda *args:None)
    result=asyncio.run(tools.graph_search_tool(db,"question","tenant"))
    assert [f["fact"] for f in result["raw_facts"]] == ["local"]
    assert graph.search.call_args.kwargs["group_ids"] == ["tenant"]


def test_hybrid_graph_failure_keeps_document_answer(monkeypatch):
    setup(monkeypatch,[(True,"")])
    monkeypatch.setattr(router,"graph_search",AsyncMock(side_effect=TimeoutError()))
    result=asyncio.run(router.AgenticRAG().ainvoke({"query":"failover","route":"hybrid"}))
    assert result["answer_mode"] == "verified"
    assert result["sources"]


def test_invalid_citation_triggers_repair_and_fallback(monkeypatch):
    verifier=setup(monkeypatch,[(True,""),(True,"")])
    monkeypatch.setattr(router,"complete",AsyncMock(return_value="Answer [99]"))
    result=asyncio.run(router.AgenticRAG().ainvoke({"query":"question","route":"documents"}))
    assert verifier.await_count == 2
    assert result["answer_mode"] == "extractive"
    assert "[99]" not in result["final_answer"]


def test_failed_repair_falls_back(monkeypatch):
    setup(monkeypatch,[(False,"bad")])
    monkeypatch.setattr(router,"complete",AsyncMock(side_effect=["Draft [1]",TimeoutError()]))
    result=asyncio.run(router.AgenticRAG().ainvoke({"query":"question","route":"documents"}))
    assert result["answer_mode"] == "extractive"
