"""Task 4: standalone grounded generation over a chosen collection (used by the demo,
the chunk comparison and the RAG-triad evaluation)."""
from __future__ import annotations

from . import config, rag
from .guardrails import support_ratio
from .llm import get_llm

FALLBACK = ("I don't know based on the information available to me. "
            "I couldn't find this in our knowledge base, so please contact Cred support.")


def grounded_answer(query: str, collection: str | None = None, k: int = config.TOP_K,
                    llm=None) -> dict:
    collection = collection or config.AGENT_COLLECTION
    llm = llm or get_llm()
    hits = rag.retrieve(query, collection, k)
    thr = config.similarity_threshold(collection)
    top1 = hits[0]["similarity"] if hits else 0.0
    if not hits or top1 < thr:
        return {"query": query, "answer": FALLBACK, "fallback": True, "top1": top1,
                "threshold": thr, "hits": hits, "supported": 1.0}
    answer = llm.generate_answer(query, [h["text"] for h in hits])
    supported = support_ratio(answer, [h["text"] for h in hits])
    if supported < 0.7:
        return {"query": query, "answer": FALLBACK, "fallback": True, "top1": top1,
                "threshold": thr, "hits": hits, "supported": supported}
    return {"query": query, "answer": answer, "fallback": False, "top1": top1,
            "threshold": thr, "hits": hits, "supported": supported}
