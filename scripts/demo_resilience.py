"""Task 16: exponential-backoff retry, per-node timeout, global timeout (all simulated, all executed)."""
import asyncio
import sys
import time
from pathlib import Path
from typing import TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from langgraph.graph import END, START, StateGraph  # noqa: E402
from langgraph.types import RetryPolicy  # noqa: E402

from app.resilience import (GlobalTimeoutError, NodeTimeoutError, TransientError,  # noqa: E402
                            arun_with_global_timeout, with_node_timeout)

# Retry policy parameters (stated explicitly as required)
POLICY = RetryPolicy(max_attempts=4, initial_interval=0.2, backoff_factor=2.0, max_interval=1.0,
                     jitter=True, retry_on=TransientError)
print("RetryPolicy: max_attempts=4 initial_interval=0.2s backoff_factor=2.0 max_interval=1.0s jitter=True\n")


class S(TypedDict, total=False):
    result: str


# ---- (a) retry recovers a transient failure ------------------------------
calls = {"n": 0}
t0 = time.perf_counter()


def flaky(state: S) -> S:
    calls["n"] += 1
    print(f"   attempt {calls['n']} at t={time.perf_counter() - t0:.2f}s")
    if calls["n"] <= 2:
        raise TransientError(f"simulated transient failure #{calls['n']}")
    return {"result": f"succeeded on attempt {calls['n']}"}


g = StateGraph(S)
g.add_node("flaky", flaky, retry_policy=POLICY)
g.add_edge(START, "flaky")
g.add_edge("flaky", END)
print("(a) RETRY: node fails its first 2 calls, then succeeds")
out = g.compile().invoke({})
print("   ->", out["result"], "| total calls:", calls["n"])
assert calls["n"] == 3

# ---- (b) per-node timeout fires a clean error ----------------------------
@with_node_timeout(0.5)
def slow_body(state: S) -> S:
    time.sleep(3)
    return {"result": "never returned"}


g2 = StateGraph(S)
g2.add_node("slow", slow_body)
g2.add_edge(START, "slow")
g2.add_edge("slow", END)
print("\n(b) PER-NODE TIMEOUT: node sleeps 3s, limit 0.5s")
t = time.perf_counter()
try:
    g2.compile().invoke({})
    raise SystemExit("FAIL: no timeout")
except NodeTimeoutError as e:
    print(f"   -> clean NodeTimeoutError after {time.perf_counter() - t:.2f}s: {e}")


# ---- (c) global timeout cancels the whole run ----------------------------
cancelled = {"flag": False}


async def long_a(state: S) -> S:
    try:
        await asyncio.sleep(10)  # simulated total-time overrun
    except asyncio.CancelledError:
        cancelled["flag"] = True
        raise
    return {"result": "never"}


g3 = StateGraph(S)
g3.add_node("long_a", long_a)
g3.add_edge(START, "long_a")
g3.add_edge("long_a", END)
print("\n(c) GLOBAL TIMEOUT: graph needs ~10s, global limit 1.0s")


async def run_c():
    t = time.perf_counter()
    try:
        await arun_with_global_timeout(g3.compile(), {}, {}, 1.0)
        raise SystemExit("FAIL: no global timeout")
    except GlobalTimeoutError as e:
        print(f"   -> GlobalTimeoutError after {time.perf_counter() - t:.2f}s: {e}")
        print("   -> running node was cancelled:", cancelled["flag"])


asyncio.run(run_c())
assert cancelled["flag"]
print("\nPASS: retry recovered, per-node timeout fired cleanly, global timeout cancelled the run.")
