"""Part 3: FastAPI deployment (Pydantic models, JSON-Lines logging with trace IDs)."""
from __future__ import annotations

import json
import time
import uuid
from collections import Counter, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import dataset

from . import config, guardrails, rag, regulatory
from .agent import SupportAgent
from .loan_tool import check_loan_application_status, ESCALATION_THRESHOLD
from .logging_setup import log_event, trace_id_var
from .resilience import GlobalTimeoutError
from .schemas import AgentResponse

_state: dict = {}
RECENT_RUNS: deque = deque(maxlen=50)  # feeds the Agent Monitor (real execution data only)


def get_agent() -> SupportAgent:
    if "agent" not in _state:
        _state["agent"] = SupportAgent()
    return _state["agent"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    rag.ensure_index()
    get_agent()
    yield


app = FastAPI(title="Cred Domain Support Agent", version="1.0.0",
              description="LangGraph banking support agent: RAG + loan lookup + guardrails.",
              lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])


# ------------------------------------------------------------------ models
class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000, examples=["What is the status of LA-1005?"])
    conversation_id: str | None = Field(default=None, max_length=64)


class AddDocumentRequest(BaseModel):
    doc_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_\-]+$")
    title: str = Field(..., min_length=1, max_length=200)
    text: str = Field(..., min_length=20, max_length=20000)
    source_url: str | None = None
    version: str | None = None


class AddDocumentResponse(BaseModel):
    doc_id: str
    chunks_indexed: dict[str, int]


class HealthResponse(BaseModel):
    status: str
    llm_mode: str
    kb_documents: int
    loan_records: int
    similarity_threshold: float


# -------------------------------------------------------------- middleware
@app.middleware("http")
async def trace_and_log(request: Request, call_next):
    trace_id = request.headers.get("x-trace-id") or uuid.uuid4().hex[:16]
    trace_id_var.set(trace_id)
    request.state.log_query = None
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["X-Trace-Id"] = trace_id
        return response
    finally:
        log_event(method=request.method, path=request.url.path, status=status,
                  duration_ms=round((time.perf_counter() - start) * 1000, 2),
                  query_masked=request.state.log_query)  # masked text only, never raw


@app.exception_handler(GlobalTimeoutError)
async def _timeout(request: Request, exc: GlobalTimeoutError):
    return JSONResponse(status_code=504, content={"error": "timeout", "detail": str(exc),
                                                  "trace_id": trace_id_var.get()})


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "internal_error",
                                                  "detail": type(exc).__name__,
                                                  "trace_id": trace_id_var.get()})


# ---------------------------------------------------------------- endpoints
@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    return HealthResponse(status="ok", llm_mode=config.LLM_MODE, kb_documents=len(rag.list_documents()),
                          loan_records=len(dataset.LOAN_APPLICATIONS),
                          similarity_threshold=config.similarity_threshold())


@app.post("/ask", response_model=AgentResponse, tags=["agent"])
def ask(req: AskRequest, request: Request):
    request.state.log_query, _ = guardrails.mask_pii(req.query)
    t0 = time.perf_counter()
    error = None
    try:
        resp = get_agent().ask(req.query, req.conversation_id, trace_id=trace_id_var.get())
    except Exception as e:  # recorded for the Agent Monitor, then re-raised to the handlers
        error = type(e).__name__
        RECENT_RUNS.appendleft({"trace_id": trace_id_var.get(), "error": error,
                                "query": request.state.log_query, "ts": time.time()})
        raise
    RECENT_RUNS.appendleft({"trace_id": trace_id_var.get(), "conversation_id": resp["conversation_id"],
                            "route": resp["route"], "intent": resp["intent"],
                            "nodes": resp["nodes_executed"], "error": error,
                            "sources": [s["doc_id"] for s in resp["sources"]],
                            "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
                            "query": request.state.log_query, "ts": time.time()})
    return resp


@app.post("/add-document", response_model=AddDocumentResponse, tags=["knowledge"])
def add_document(req: AddDocumentRequest):
    counts = rag.add_document(req.doc_id, req.title, req.text,
                              {"source_url": req.source_url or "", "version": req.version or ""})
    return AddDocumentResponse(doc_id=req.doc_id, chunks_indexed=counts)


@app.get("/loans", tags=["loans"])
def list_loans(customer_id: str | None = None, status: str | None = None,
               category: str | None = None, limit: int = Query(100, ge=1, le=500)):
    rows = dataset.LOAN_APPLICATIONS
    if customer_id:
        rows = [r for r in rows if r["customer_id"].lower() == customer_id.lower()]
    if status:
        rows = [r for r in rows if r["status"].lower() == status.lower()]
    if category:
        rows = [r for r in rows if r["category"].lower() == category.lower()]
    return [check_loan_application_status(r["record_id"]) | {
        "customer_id": r["customer_id"], "applicant_name": r["applicant_name"],
        "created_date": r["created_date"]} for r in rows[:limit]]


@app.get("/loans/{record_id}", tags=["loans"])
def get_loan(record_id: str):
    res = check_loan_application_status(record_id)
    if not res["found"]:
        raise HTTPException(404, res["error"])
    rec = dataset.get_record(record_id)
    return res | {"customer_id": rec["customer_id"], "applicant_name": rec["applicant_name"],
                  "created_date": rec["created_date"]}


@app.get("/conversations", tags=["conversations"])
def list_conversations():
    return get_agent().store.list_conversations()


@app.get("/conversations/{conversation_id}", tags=["conversations"])
def get_conversation(conversation_id: str):
    msgs = get_agent().store.get(conversation_id)
    if not msgs:
        raise HTTPException(404, "conversation not found")
    return {"conversation_id": conversation_id, "messages": msgs}


@app.get("/knowledge/documents", tags=["knowledge"])
def kb_documents():
    return rag.list_documents()


@app.get("/knowledge/search", tags=["knowledge"])
def kb_search(q: str = Query(..., min_length=1, max_length=500), k: int = Query(3, ge=1, le=10),
              collection: str | None = None, request: Request = None):
    request.state.log_query, _ = guardrails.mask_pii(q)
    return {"query": q, "threshold": config.similarity_threshold(collection),
            "results": rag.retrieve(q, collection, k)}


@app.get("/stats", tags=["system"])
def stats():
    rows = dataset.LOAN_APPLICATIONS
    checked = [check_loan_application_status(r["record_id"]) for r in rows]
    convs = get_agent().store.list_conversations()
    recent = sorted(convs, key=lambda c: c["created"], reverse=True)[:5]
    return {
        "total_loans": len(rows),
        "by_status": dict(Counter(r["status"] for r in rows)),
        "by_category": dict(Counter(r["category"] for r in rows)),
        "fraud_review": sum(r["flagged_for_fraud_review"] for r in rows),
        "escalations": sum(c["escalate"] for c in checked),
        "escalation_threshold": ESCALATION_THRESHOLD,
        "kb_documents": len(rag.list_documents()),
        "conversations": len(convs),
        "recent_queries": recent,
        "llm_mode": config.LLM_MODE,
    }


@app.get("/monitor/runs", tags=["system"])
def monitor_runs():
    return list(RECENT_RUNS)


# ------------------------------------------------------ regulatory centre
class RegisterRegRequest(BaseModel):
    doc_id: str = Field(..., pattern=r"^[A-Za-z0-9_\-]{1,64}$")
    title: str = Field(..., min_length=1, max_length=300)
    authority: str = Field(..., min_length=1, max_length=200)
    source_url: str = Field(..., pattern=r"^https?://")
    publication_date: str | None = None
    effective_date: str | None = None


@app.get("/regulatory/documents", tags=["regulatory"])
def reg_documents():
    return regulatory.list_documents()


@app.post("/regulatory/register", tags=["regulatory"])
def reg_register(req: RegisterRegRequest):
    return regulatory.register(**req.model_dump())


@app.post("/regulatory/{doc_id}/update", tags=["regulatory"])
def reg_update(doc_id: str):
    try:
        return regulatory.update(doc_id)
    except KeyError:
        raise HTTPException(404, "unknown regulatory document")


# -------------------------------------------------- analytics / monitoring
@app.get("/analytics/rag", tags=["system"])
def rag_analytics():
    """Serves the evaluation results that scripts/eval_*.py actually produced."""
    out = {}
    for key, name in (("calibration", "calibration.json"), ("chunking", "chunking_eval.json"),
                      ("triad", "triad_eval.json")):
        f = config.ARTIFACTS_DIR / name
        out[key] = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
    return out


@app.get("/monitor/logs", tags=["system"])
def monitor_logs(limit: int = Query(50, ge=1, le=500)):
    if not config.REQUEST_LOG.exists():
        return []
    lines = config.REQUEST_LOG.read_text(encoding="utf-8").splitlines()[-limit:]
    return [json.loads(l) for l in reversed(lines)]
