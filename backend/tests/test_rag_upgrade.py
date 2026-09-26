import asyncio
from unittest.mock import AsyncMock
import backend.app.agents.router as router


def setup(monkeypatch, verdicts):
    source = {"title": "Acceptance", "document_id": "missing-test-doc", "content": "Failover must not exceed 60 seconds.", "source_type": "text"}
    monkeypatch.setattr(router, "lexical_search", lambda *a: [source])
    monkeypatch.setattr(router, "vector_search", lambda *a: [])
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
