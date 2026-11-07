"""Part 4: MCP round trip, SQLite checkpoint resume, retry and timeouts (Tasks 14-16)."""
import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import TypedDict

import pytest
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from app.agent import SupportAgent
from app.memory import ConversationStore
from app.resilience import (EXEC_COUNTS, GlobalTimeoutError, NodeTimeoutError, TransientError,
                            arun_with_global_timeout, with_node_timeout)

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def mcp_server():
    port = 8765
    env = {**os.environ, "MCP_PORT": str(port)}
    p = subprocess.Popen([sys.executable, str(ROOT / "mcp_server.py")], cwd=ROOT, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.5).close()
            break
        except OSError:
            time.sleep(0.5)
    yield f"http://127.0.0.1:{port}/mcp"
    p.terminate()


def test_mcp_round_trip_two_ids(mcp_server):
    from fastmcp import Client

    async def go():
        async with Client(mcp_server) as c:
            names = [t.name for t in await c.list_tools()]
            a = await c.call_tool("check_loan_application_status", {"record_id": "LA-1001"})
            b = await c.call_tool("check_loan_application_status", {"record_id": "LA-1005"})
            return names, a, b
    names, a, b = asyncio.run(go())
    assert "check_loan_application_status" in names
    assert a.data["record_id"] == "LA-1001" and b.data["record_id"] == "LA-1005"
    assert 0 <= a.data["escalation_score"] <= 1


def test_checkpoint_resume_does_not_reexecute(tmp_path):
    db, store = str(tmp_path / "ck.sqlite"), ConversationStore(tmp_path / "c.json")
    cfg = {"configurable": {"thread_id": "T"}}
    a1 = SupportAgent(db, store, interrupt_before=["generate_answer"])
    EXEC_COUNTS.clear()
    a1.graph.invoke({"query": "How is EMI calculated?", "conversation_id": "T", "trace_id": ""}, cfg)
    assert a1.state("T").next == ("generate_answer",)
    assert EXEC_COUNTS["rag_retrieve"] == 1 and EXEC_COUNTS["generate_answer"] == 0
    a1.conn.close()
    EXEC_COUNTS.clear()
    a2 = SupportAgent(db, store, interrupt_before=["generate_answer"])
    out = a2.graph.invoke(None, cfg)
    assert out["response"]["answer"]
    assert EXEC_COUNTS["guard_input"] == EXEC_COUNTS["classify_intent"] == EXEC_COUNTS["rag_retrieve"] == 0
    assert EXEC_COUNTS["generate_answer"] == 1


class S(TypedDict, total=False):
    r: str


def test_retry_recovers_transient_failure():
    calls = {"n": 0}

    def flaky(s):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise TransientError("boom")
        return {"r": "ok"}
    g = StateGraph(S)
    g.add_node("f", flaky, retry_policy=RetryPolicy(max_attempts=4, initial_interval=0.05,
                                                    max_interval=0.2, jitter=True, retry_on=TransientError))
    g.add_edge(START, "f")
    g.add_edge("f", END)
    assert g.compile().invoke({})["r"] == "ok" and calls["n"] == 3


def test_retry_gives_up_after_max_attempts():
    def always(s):
        raise TransientError("x")
    g = StateGraph(S)
    g.add_node("f", always, retry_policy=RetryPolicy(max_attempts=2, initial_interval=0.01, retry_on=TransientError))
    g.add_edge(START, "f")
    g.add_edge("f", END)
    with pytest.raises(TransientError):
        g.compile().invoke({})


def test_per_node_timeout_clean_error():
    @with_node_timeout(0.3)
    def slow(s):
        time.sleep(2)
        return {"r": "late"}
    g = StateGraph(S)
    g.add_node("s", slow)
    g.add_edge(START, "s")
    g.add_edge("s", END)
    t = time.perf_counter()
    with pytest.raises(NodeTimeoutError):
        g.compile().invoke({})
    assert time.perf_counter() - t < 1.5


def test_global_timeout_cancels_run():
    flag = {"c": False}

    async def long(s):
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            flag["c"] = True
            raise
    g = StateGraph(S)
    g.add_node("l", long)
    g.add_edge(START, "l")
    g.add_edge("l", END)
    t = time.perf_counter()
    with pytest.raises(GlobalTimeoutError):
        asyncio.run(arun_with_global_timeout(g.compile(), {}, {}, 0.5))
    assert flag["c"] and time.perf_counter() - t < 3
