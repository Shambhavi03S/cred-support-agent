r"""Part 2: LangGraph support agent.

START -> guard_input --(injection/invalid)--> refuse ----------------------------> finalize
              |
              v
        classify_intent --(policy_question)--> rag_retrieve --\
              |--(loan_status)----------------> loan_lookup ----+--> generate_answer
              |--(clarification)--> clarify ----------------\    |        |
                                                             \   v        v
                                                              \  groundedness_check
                                                               \------> finalize -> END
"""
from __future__ import annotations

import operator
import sqlite3
import uuid
from typing import Annotated, Any, Optional, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from . import config, guardrails
from .llm import classify_intent as _classify, get_llm
from .loan_tool import check_loan_application_status
from .memory import ConversationStore
from .resilience import (EXEC_COUNTS, TransientError, default_retry_policy,
                         run_with_global_timeout, with_node_timeout)
from .schemas import AgentResponse, validate_response

FALLBACK_ANSWER = ("I don't know based on the information available to me. "
                   "I couldn't find this in our knowledge base, so please contact Cred support.")


def _nodes_reducer(old: list[str], new: list[str]) -> list[str]:
    # guard_input starts a new turn -> reset the per-turn trace of executed nodes
    return list(new) if new and new[0] == "guard_input" else (old or []) + list(new)


class AgentState(TypedDict, total=False):
    query: str
    conversation_id: str
    trace_id: str
    masked_query: str
    pii_found: list[str]
    injection: bool
    input_ok: bool
    input_reason: Optional[str]
    intent: str
    record_id: Optional[str]
    route: str
    hits: list[dict]
    loan: Optional[dict]
    answer: str
    grounded: bool
    fallback: bool
    response: dict
    nodes: Annotated[list[str], _nodes_reducer]


def _count(name: str) -> None:
    EXEC_COUNTS[name] += 1


def build_graph(store: ConversationStore, llm, checkpointer=None, interrupt_before=None,
                inject_fault=None):
    """Compile the agent graph. `inject_fault` (optional callable run inside
    rag_retrieve) lets tests simulate transient failures."""

    # ---- nodes ---------------------------------------------------------
    def guard_input(state: AgentState) -> dict:
        _count("guard_input")
        chk = guardrails.check_input(state.get("query", ""))
        return {"masked_query": chk.masked_text, "pii_found": chk.pii_found,
                "injection": chk.injection, "input_ok": chk.ok, "input_reason": chk.reason,
                "intent": "unknown", "record_id": None, "hits": [], "loan": None,
                "answer": "", "grounded": True, "fallback": False, "response": {},
                "nodes": ["guard_input"]}

    def classify_intent(state: AgentState) -> dict:
        _count("classify_intent")
        mem_rid = store.last_record_id(state["conversation_id"])
        intent, rid = _classify(state["masked_query"], mem_rid)
        route = {"policy_question": "rag", "loan_status": "loan_tool",
                 "clarification": "clarify"}[intent]
        return {"intent": intent, "record_id": rid, "route": route, "nodes": ["classify_intent"]}

    @with_node_timeout(config.NODE_TIMEOUT_S)
    def _retrieve(query: str) -> list[dict]:
        from . import rag
        if inject_fault:
            inject_fault()
        return rag.retrieve(query, config.AGENT_COLLECTION, config.TOP_K)

    def rag_retrieve(state: AgentState) -> dict:
        _count("rag_retrieve")
        q = state["masked_query"]
        prev = store.last_user_query(state["conversation_id"])
        if prev and len(q.split()) <= 5:  # short follow-up -> carry the prior question
            q = f"{prev} {q}"
        return {"hits": _retrieve(q), "nodes": ["rag_retrieve"]}

    def loan_lookup(state: AgentState) -> dict:
        _count("loan_lookup")
        return {"loan": check_loan_application_status(state["record_id"]),
                "nodes": ["loan_lookup"]}

    def clarify(state: AgentState) -> dict:
        _count("clarify")
        return {"answer": "Could you share the loan application record ID (for example LA-1005) "
                          "so I can check its status?", "nodes": ["clarify"]}

    def refuse(state: AgentState) -> dict:
        _count("refuse")
        if state.get("injection"):
            msg = ("I can't act on that request. It looks like an attempt to override my "
                   "instructions, and I only answer Cred banking questions.")
        elif state.get("input_reason") == "query_too_long":
            msg = f"Your message is too long (max {guardrails.MAX_QUERY_CHARS} characters)."
        else:
            msg = "Please enter a question about Cred loans or accounts."
        return {"answer": msg, "route": "blocked", "intent": "blocked", "nodes": ["refuse"]}

    @with_node_timeout(config.NODE_TIMEOUT_S)
    def _generate(query: str, contexts: list[str]) -> str:
        return llm.generate_answer(query, contexts)

    def generate_answer(state: AgentState) -> dict:
        _count("generate_answer")
        if state["route"] == "loan_tool":
            ln = state["loan"]
            if not ln["found"]:
                return {"answer": ln["error"], "nodes": ["generate_answer"]}
            esc = ("Escalation is recommended" if ln["escalate"] else "No escalation is needed")
            ans = (f"Application {ln['record_id']} ({ln['category']}) is {ln['status']}, "
                   f"for INR {ln['loan_amount_inr']:,}. It was created {ln['days_since_created']} "
                   f"days ago and "
                   f"{'is' if ln['flagged_for_fraud_review'] else 'is not'} flagged for fraud review. "
                   f"{esc} (escalation score {ln['escalation_score']:.2f}, threshold "
                   f"{ln['escalation_threshold']:.2f}).")
            return {"answer": ans, "nodes": ["generate_answer"]}
        hits = state.get("hits", [])
        if not hits or hits[0]["similarity"] < config.similarity_threshold():
            return {"answer": FALLBACK_ANSWER, "fallback": True, "nodes": ["generate_answer"]}
        ans = _generate(state["masked_query"], [h["text"] for h in hits])
        return {"answer": ans, "nodes": ["generate_answer"]}

    def groundedness_check(state: AgentState) -> dict:
        """Output guardrail: RAG answers must be supported by the retrieved context."""
        _count("groundedness_check")
        ans, grounded, fallback = state["answer"], True, state.get("fallback", False)
        if state["route"] == "rag" and not fallback:
            ratio = guardrails.support_ratio(ans, [h["text"] for h in state["hits"]])
            if ratio < 0.7:
                ans, grounded, fallback = FALLBACK_ANSWER, False, True
        ans, _ = guardrails.mask_pii(ans)  # never emit fixed-format PII
        return {"answer": ans, "grounded": grounded, "fallback": fallback,
                "nodes": ["groundedness_check"]}

    def finalize(state: AgentState) -> dict:
        _count("finalize")
        route = state["route"]
        loan = state.get("loan")
        loan_info = None
        if loan and loan.get("found"):
            loan_info = {k: loan[k] for k in ("record_id", "category", "status", "loan_amount_inr",
                                              "days_since_created", "flagged_for_fraud_review",
                                              "escalation_score", "escalate")}
        sources = []
        if route == "rag" and not state.get("fallback"):
            seen = set()
            for h in state.get("hits", []):
                if h["doc_id"] in seen:
                    continue
                seen.add(h["doc_id"])
                sources.append({"doc_id": h["doc_id"], "title": h["title"],
                                "similarity": h["similarity"], "snippet": h["text"][:160]})
        resp = AgentResponse(
            conversation_id=state["conversation_id"], trace_id=state.get("trace_id"),
            intent=state["intent"], route=route, answer=state["answer"], sources=sources,
            loan=loan_info,
            guardrails={"pii_masked": state.get("pii_found", []),
                        "injection_detected": state.get("injection", False),
                        "grounded": state.get("grounded", True),
                        "fallback_triggered": state.get("fallback", False)},
            model=llm.name, nodes_executed=state["nodes"] + ["finalize"]).model_dump()
        validate_response(resp)  # Task 9: every response validated against the JSON Schema
        cid = state["conversation_id"]
        if state.get("input_ok", True):
            store.append(cid, "user", state["masked_query"], record_id=state.get("record_id"))
        store.append(cid, "assistant", resp["answer"], route=route,
                     record_id=(loan_info or {}).get("record_id"))
        return {"response": resp, "nodes": ["finalize"]}

    # ---- routing -------------------------------------------------------
    def after_guard(state: AgentState) -> str:
        return "classify_intent" if state["input_ok"] else "refuse"

    def after_classify(state: AgentState) -> str:
        return {"rag": "rag_retrieve", "loan_tool": "loan_lookup", "clarify": "clarify"}[state["route"]]

    g = StateGraph(AgentState)
    retry = default_retry_policy()
    g.add_node("guard_input", guard_input)
    g.add_node("classify_intent", classify_intent)
    g.add_node("rag_retrieve", rag_retrieve, retry_policy=retry)
    g.add_node("loan_lookup", loan_lookup)
    g.add_node("clarify", clarify)
    g.add_node("refuse", refuse)
    g.add_node("generate_answer", generate_answer, retry_policy=retry)
    g.add_node("groundedness_check", groundedness_check)
    g.add_node("finalize", finalize)

    g.add_edge(START, "guard_input")
    g.add_conditional_edges("guard_input", after_guard, ["classify_intent", "refuse"])
    g.add_conditional_edges("classify_intent", after_classify,
                            ["rag_retrieve", "loan_lookup", "clarify"])
    g.add_edge("rag_retrieve", "generate_answer")
    g.add_edge("loan_lookup", "generate_answer")
    g.add_edge("generate_answer", "groundedness_check")
    g.add_edge("groundedness_check", "finalize")
    g.add_edge("clarify", "finalize")
    g.add_edge("refuse", "finalize")
    g.add_edge("finalize", END)
    return g.compile(checkpointer=checkpointer, interrupt_before=interrupt_before)


class SupportAgent:
    def __init__(self, checkpoint_db: str | None = None, store: ConversationStore | None = None,
                 interrupt_before: list[str] | None = None, inject_fault=None, llm=None):
        from . import rag
        rag.ensure_index()
        rag.embed(["warm-up"])  # load the model before any per-node timeout clock starts
        self.store = store or ConversationStore()
        self.llm = llm or get_llm()
        self.conn = sqlite3.connect(checkpoint_db or config.CHECKPOINT_DB, check_same_thread=False)
        self.saver = SqliteSaver(self.conn)
        self.graph = build_graph(self.store, self.llm, self.saver, interrupt_before, inject_fault)

    def ask(self, query: str, conversation_id: str | None = None, trace_id: str | None = None,
            global_timeout: float | None = None) -> dict:
        cid = conversation_id or f"conv-{uuid.uuid4().hex[:10]}"
        cfg = {"configurable": {"thread_id": cid}}
        inputs = {"query": query, "conversation_id": cid, "trace_id": trace_id or ""}
        out = run_with_global_timeout(self.graph, inputs, cfg,
                                      global_timeout or config.GLOBAL_TIMEOUT_S)
        return out["response"]

    def resume(self, conversation_id: str) -> dict:
        """Resume an interrupted thread from its last checkpoint (Task 15)."""
        cfg = {"configurable": {"thread_id": conversation_id}}
        return self.graph.invoke(None, cfg)["response"]

    def state(self, conversation_id: str) -> Any:
        return self.graph.get_state({"configurable": {"thread_id": conversation_id}})
