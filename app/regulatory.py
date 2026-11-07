"""Optional enhancement: regulatory document registry with a manual update mechanism.

Nothing is shipped pre-populated: no regulation text or "in force" claim is invented.
An operator registers an OFFICIAL source URL (RBI, MoF/DFS, India Code ...) and clicks
"update" while online. The fetcher stores the text, hashes it, bumps the version when the
content changed, keeps previous versions on disk, flags the older one as superseded and
indexes the latest text into a SEPARATE Chroma collection. Offline, the previously
indexed copy keeps working. Status is always "Unverified" until a human verifies it.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import time

import httpx

from . import config, rag

COLLECTION = "regulatory_docs"
REG_DIR = config.DATA_DIR / "regulatory"
MANIFEST = REG_DIR / "manifest.json"
REG_DIR.mkdir(parents=True, exist_ok=True)


def _load() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}


def _save(m: dict) -> None:
    MANIFEST.write_text(json.dumps(m, indent=2), encoding="utf-8")


def list_documents() -> list[dict]:
    return list(_load().values())


def register(doc_id: str, title: str, authority: str, source_url: str,
             publication_date: str | None = None, effective_date: str | None = None) -> dict:
    if not re.match(r"^[A-Za-z0-9_\-]{1,64}$", doc_id):
        raise ValueError("doc_id must be alphanumeric/underscore/hyphen")
    m = _load()
    m.setdefault(doc_id, {
        "doc_id": doc_id, "title": title, "authority": authority, "source_url": source_url,
        "publication_date": publication_date, "effective_date": effective_date,
        "version": 0, "status": "Not yet fetched", "doc_type": "regulation (external source)",
        "last_indexed": None, "content_hash": None, "versions": []})
    _save(m)
    return m[doc_id]


def _extract_text(resp: httpx.Response) -> str:
    ctype = resp.headers.get("content-type", "")
    if "pdf" in ctype or resp.url.path.lower().endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(resp.content)).pages)
    html = resp.text
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", html)).strip()


def _index(doc: dict, text: str) -> int:
    col = rag.get_client().get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    old = col.get(where={"doc_id": doc["doc_id"]})
    if old["ids"]:
        col.delete(ids=old["ids"])
    chunks = rag.chunk_fixed(text)
    if not chunks:
        return 0
    col.add(ids=[f"{doc['doc_id']}::{i}" for i in range(len(chunks))],
            embeddings=rag.embed([f"{doc['title']}. {c}" for c in chunks]),
            documents=chunks,
            metadatas=[{"doc_id": doc["doc_id"], "title": doc["title"], "chunk_index": i,
                        "raw": c, "authority": doc["authority"], "source_url": doc["source_url"],
                        "version": str(doc["version"])} for i, c in enumerate(chunks)])
    return len(chunks)


def update(doc_id: str, timeout: float = 30.0) -> dict:
    """Fetch -> extract -> hash -> (version bump + re-index) if changed."""
    m = _load()
    if doc_id not in m:
        raise KeyError(doc_id)
    doc = m[doc_id]
    try:
        resp = httpx.get(doc["source_url"], timeout=timeout, follow_redirects=True,
                         headers={"User-Agent": "cred-support-agent/1.0"})
        resp.raise_for_status()
    except Exception as e:  # offline or blocked -> keep the existing indexed copy
        return {"doc_id": doc_id, "result": "fetch_failed", "detail": type(e).__name__,
                "note": "Existing indexed version (if any) is unchanged."}
    text = _extract_text(resp)
    if len(text) < 200:
        return {"doc_id": doc_id, "result": "extraction_failed", "chars": len(text)}
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if h == doc["content_hash"]:
        return {"doc_id": doc_id, "result": "unchanged", "version": doc["version"]}
    if doc["versions"]:
        doc["versions"][-1]["status"] = "superseded"  # preserve the old file, mark superseded
    doc["version"] += 1
    fname = f"{doc_id}_v{doc['version']}.txt"
    (REG_DIR / fname).write_text(text, encoding="utf-8")
    doc["versions"].append({"version": doc["version"], "hash": h, "file": fname,
                            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "status": "latest"})
    doc.update(content_hash=h, status="Unverified - fetched, not confirmed in force",
               last_indexed=doc["versions"][-1]["fetched_at"])
    chunks = _index(doc, text)
    _save(m)
    return {"doc_id": doc_id, "result": "updated", "version": doc["version"], "chunks_indexed": chunks}
