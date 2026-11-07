"""Part 3: FastAPI + JSON-Lines logging (Tasks 11-12)."""
import json

import pytest
from fastapi.testclient import TestClient

from app import config
from app.api import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["llm_mode"] == "MOCK_LLM"
    assert "X-Trace-Id" in r.headers


def test_ask_and_validation(client):
    r = client.post("/ask", json={"query": "What KYC documents do I need?"})
    assert r.status_code == 200
    body = r.json()
    assert body["route"] == "rag" and body["sources"] and body["conversation_id"]
    assert client.post("/ask", json={"query": ""}).status_code == 422
    assert client.post("/ask", json={}).status_code == 422


def test_loans_and_history(client):
    assert client.get("/loans/LA-1001").json()["found"] is True
    assert client.get("/loans/NOPE").status_code == 404
    assert len(client.get("/loans").json()) >= 40
    cid = client.post("/ask", json={"query": "status of LA-1004", "conversation_id": "api-h"}).json()["conversation_id"]
    hist = client.get(f"/conversations/{cid}").json()
    assert len(hist["messages"]) == 2
    assert client.get("/conversations/does-not-exist").status_code == 404


def test_add_document_then_retrievable(client):
    r = client.post("/add-document", json={
        "doc_id": "zz_test_doc", "title": "Gold Loan Rules",
        "text": "Cred gold loans lend up to 75 percent of the gold value. Gold must be valued by an approved appraiser."})
    try:
        assert r.status_code == 200 and r.json()["chunks_indexed"]
        res = client.get("/knowledge/search", params={"q": "How much can I borrow against gold?"}).json()
        assert any(h["doc_id"] == "zz_test_doc" for h in res["results"])
    finally:
        (config.KB_DIR / "zz_test_doc.md").unlink(missing_ok=True)


def test_jsonl_log_has_trace_id_and_no_raw_pii(client):
    pan, acct = "ABCDE1234F", "123456789012"
    client.post("/ask", json={"query": f"my PAN {pan} account {acct} status of LA-1001"})
    lines = [json.loads(l) for l in config.REQUEST_LOG.read_text().splitlines()]
    assert lines and all("trace_id" in l and "duration_ms" in l for l in lines)
    raw = config.REQUEST_LOG.read_text()
    assert pan not in raw and acct not in raw and "[PAN_MASKED]" in raw
    # every request -> exactly one entry
    n = len(lines)
    client.get("/health")
    assert len(config.REQUEST_LOG.read_text().splitlines()) == n + 1


def test_stats_from_real_data(client):
    s = client.get("/stats").json()
    assert s["total_loans"] >= 40 and s["kb_documents"] >= 12
