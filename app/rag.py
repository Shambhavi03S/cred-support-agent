"""Part 1: ingestion, two chunking strategies, embeddings, ChromaDB indexes, retrieval."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import config
from .guardrails import sentences

_model = None
_client = None


def get_embedder():
    """Lazy-load the local SentenceTransformer (free, offline once cached)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(config.EMBED_MODEL)
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    return get_embedder().encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


def get_client():
    global _client
    if _client is None:
        import chromadb
        config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return _client


@dataclass
class Doc:
    doc_id: str
    title: str
    topic: str
    text: str
    meta: dict


# ---------------------------------------------------------------- ingestion
def parse_kb_file(path: Path) -> Doc:
    lines = path.read_text(encoding="utf-8").splitlines()
    title = lines[0].lstrip("# ").strip()
    topic = lines[1].split(":", 1)[1].strip() if len(lines) > 1 and lines[1].startswith("topic:") else title
    body = " ".join(l.strip() for l in lines[2:] if l.strip())
    return Doc(path.stem, title, topic, body, {"source": "bank_policy", "file": path.name})


def load_kb_documents() -> list[Doc]:
    return [parse_kb_file(p) for p in sorted(config.KB_DIR.glob("*.md"))]


# ------------------------------------------------------- chunking strategies
def chunk_fixed(text: str, size: int = config.FIXED_CHUNK_CHARS,
                overlap: int = config.FIXED_OVERLAP_CHARS) -> list[str]:
    """Strategy A: fixed-size character windows with overlap (snapped to word edges)."""
    words, chunks, cur = text.split(), [], ""
    i = 0
    while i < len(words):
        cur = ""
        j = i
        while j < len(words) and len(cur) + len(words[j]) + 1 <= size:
            cur = f"{cur} {words[j]}".strip()
            j += 1
        if j == i:  # single very long word
            cur, j = words[i], i + 1
        chunks.append(cur)
        if j >= len(words):
            break
        # step back so ~`overlap` characters are shared with the next chunk
        back, k = 0, j
        while k > i + 1 and back < overlap:
            k -= 1
            back += len(words[k]) + 1
        i = max(k, i + 1)
    return chunks


def chunk_sentences(text: str, per_chunk: int = config.SENTENCES_PER_CHUNK) -> list[str]:
    """Strategy B: sentence-based chunks (groups of `per_chunk` whole sentences)."""
    sents = sentences(text)
    return [" ".join(sents[i:i + per_chunk]) for i in range(0, len(sents), per_chunk)]


STRATEGIES = {config.COLLECTION_FIXED: chunk_fixed, config.COLLECTION_SENTENCE: chunk_sentences}


# ---------------------------------------------------------------- indexing
def index_documents(docs: list[Doc], reset: bool = False) -> dict[str, int]:
    client = get_client()
    counts = {}
    for name, chunker in STRATEGIES.items():
        if reset:
            try:
                client.delete_collection(name)
            except Exception:
                pass
        col = client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})
        ids, texts, metas = [], [], []
        for d in docs:
            for i, ch in enumerate(chunker(d.text)):
                ids.append(f"{d.doc_id}::{i}")
                texts.append(f"{d.title}. {ch}")
                metas.append({"doc_id": d.doc_id, "title": d.title, "chunk_index": i,
                              "strategy": name, "raw": ch,
                              **{k: str(v) for k, v in d.meta.items()}})
        if ids:
            col.upsert(ids=ids, embeddings=embed(texts), documents=texts, metadatas=metas)
        counts[name] = col.count()
    return counts


def ensure_index() -> None:
    """Build the index on first use (idempotent)."""
    client = get_client()
    names = {c.name for c in client.list_collections()}
    if not all(n in names for n in STRATEGIES) or any(
            client.get_collection(n).count() == 0 for n in STRATEGIES):
        index_documents(load_kb_documents(), reset=True)


def add_document(doc_id: str, title: str, text: str, meta: dict | None = None) -> dict[str, int]:
    """Task 11 /add-document: persist to kb/ and index into both collections."""
    safe = re.sub(r"[^A-Za-z0-9_\-]", "_", doc_id)
    path = config.KB_DIR / f"{safe}.md"
    body = " ".join(text.split())
    path.write_text(f"# {title}\ntopic: {title}\n\n{body}\n", encoding="utf-8")
    d = Doc(safe, title, title, body, {"source": "user_added", **(meta or {})})
    ensure_index()
    return index_documents([d], reset=False)


# --------------------------------------------------------------- retrieval
def retrieve(query: str, collection: str | None = None, k: int = config.TOP_K) -> list[dict]:
    """Top-k chunks by cosine similarity (similarity = 1 - cosine distance)."""
    ensure_index()
    col = get_client().get_collection(collection or config.AGENT_COLLECTION)
    res = col.query(query_embeddings=embed([query]), n_results=min(k, col.count()),
                    include=["documents", "metadatas", "distances"])
    out = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        out.append({"doc_id": meta["doc_id"], "title": meta["title"],
                    "text": meta.get("raw", doc), "similarity": round(1.0 - dist, 4),
                    "chunk_index": meta["chunk_index"]})
    return out


def retrieve_docs(query: str, collection: str, k: int = 3, pool: int = 20) -> list[str]:
    """Document-level ranking: map chunks to parent docs, dedup, keep first k docs."""
    seen: list[str] = []
    for h in retrieve(query, collection, k=pool):
        if h["doc_id"] not in seen:
            seen.append(h["doc_id"])
        if len(seen) == k:
            break
    return seen


def list_documents() -> list[dict]:
    return [{"doc_id": d.doc_id, "title": d.title, "topic": d.topic, "chars": len(d.text),
             "sentences": len(sentences(d.text)), **d.meta} for d in load_kb_documents()]
