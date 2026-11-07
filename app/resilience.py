"""Task 16: timeouts + retry helpers shared by the agent and the resilience demo."""
from __future__ import annotations

import asyncio
import concurrent.futures
import functools
from collections import Counter

from langgraph.types import RetryPolicy

from . import config

# Counts how many times each node body really executed (used to prove that
# checkpoint-resume does NOT re-execute already-completed nodes).
EXEC_COUNTS: Counter = Counter()


class NodeTimeoutError(TimeoutError):
    """A single node exceeded its per-node timeout."""


class GlobalTimeoutError(TimeoutError):
    """The whole graph run exceeded the global timeout."""


class TransientError(RuntimeError):
    """A failure that is worth retrying (network blip, flaky dependency)."""


def default_retry_policy() -> RetryPolicy:
    return RetryPolicy(initial_interval=config.RETRY_INITIAL_INTERVAL,
                       backoff_factor=config.RETRY_BACKOFF,
                       max_interval=config.RETRY_MAX_INTERVAL,
                       max_attempts=config.RETRY_MAX_ATTEMPTS,
                       jitter=config.RETRY_JITTER,
                       retry_on=(TransientError, ConnectionError))


_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=8, thread_name_prefix="node")


def with_node_timeout(seconds: float):
    """Decorator: run a *sync* node with a timeout; raise NodeTimeoutError cleanly
    (the abandoned worker thread cannot be killed, but the graph is not blocked)."""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **kw):
            fut = _POOL.submit(fn, *a, **kw)
            try:
                return fut.result(timeout=seconds)
            except concurrent.futures.TimeoutError:
                raise NodeTimeoutError(f"node '{fn.__name__}' exceeded {seconds}s") from None
        return wrapper
    return deco


def run_with_global_timeout(graph, inputs, run_config, seconds: float):
    """Sync API path: bound total wall-clock time of one graph run."""
    fut = _POOL.submit(graph.invoke, inputs, run_config)
    try:
        return fut.result(timeout=seconds)
    except concurrent.futures.TimeoutError:
        raise GlobalTimeoutError(f"graph run exceeded global timeout of {seconds}s") from None


async def arun_with_global_timeout(graph, inputs, run_config, seconds: float):
    """Async path: asyncio.wait_for genuinely *cancels* the running graph task."""
    try:
        return await asyncio.wait_for(graph.ainvoke(inputs, run_config), timeout=seconds)
    except asyncio.TimeoutError:
        raise GlobalTimeoutError(f"graph run cancelled after global timeout of {seconds}s") from None
