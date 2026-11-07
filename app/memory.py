"""Task 8: persisted conversation memory in a JSON file (atomic writes, thread-safe)."""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

from . import config


class ConversationStore:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path or config.CONVERSATIONS_JSON)
        self._lock = threading.Lock()

    def _load(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}  # corrupt file -> start clean rather than crash the agent

    def _save(self, data: dict) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)  # atomic on Windows and POSIX

    def get(self, conversation_id: str) -> list[dict]:
        with self._lock:
            return self._load().get(conversation_id, {}).get("messages", [])

    def append(self, conversation_id: str, role: str, content: str, **meta) -> None:
        with self._lock:
            data = self._load()
            conv = data.setdefault(conversation_id, {"created": time.time(), "messages": []})
            conv["messages"].append({"role": role, "content": content,
                                     "ts": round(time.time(), 3), **meta})
            self._save(data)

    def list_conversations(self) -> list[dict]:
        with self._lock:
            data = self._load()
        return [{"conversation_id": k, "turns": len(v["messages"]), "created": v["created"],
                 "last_message": v["messages"][-1]["content"][:80] if v["messages"] else ""}
                for k, v in data.items()]

    def last_record_id(self, conversation_id: str) -> str | None:
        for m in reversed(self.get(conversation_id)):
            if m.get("record_id"):
                return m["record_id"]
        return None

    def last_user_query(self, conversation_id: str) -> str | None:
        for m in reversed(self.get(conversation_id)):
            if m["role"] == "user":
                return m["content"]
        return None
