"""Task 12: JSON-Lines request log. Only already-masked text is ever passed in."""
from __future__ import annotations

import json
import threading
import time
from contextvars import ContextVar

from . import config

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")
_lock = threading.Lock()


def log_event(**fields) -> None:
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z",
             "trace_id": trace_id_var.get(), **fields}
    with _lock, open(config.REQUEST_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
