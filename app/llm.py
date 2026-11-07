"""LLM abstraction: MOCK_LLM (default, deterministic, offline) + optional Ollama / Gemini.

Intent classification and the judge are rule-based for every mode so the graph
routing is deterministic; only *answer generation* is swapped for real models.
"""
from __future__ import annotations

import re

from . import config
from .guardrails import content_tokens, sentences

RECORD_ID_RE = re.compile(r"\bLA-\d{3,6}\b", re.I)
_STATUS_WORDS = re.compile(r"\b(status|escalat\w*|fraud|flag\w*|amount|how old|days|stuck|delay\w*|"
                           r"approved|rejected|disbursed|pending|under review|submitted|score)\b", re.I)
_PERSONAL = re.compile(r"\b(my|this|that|its?|same|the)\b", re.I)
_LOAN_NOUN = re.compile(r"\b(application|loan|request|record|case)\b", re.I)
_PRONOUN = re.compile(r"\b(it|its|this|that|same|there)\b", re.I)


def classify_intent(query: str, memory_record_id: str | None = None) -> tuple[str, str | None]:
    """Return (intent, record_id). Deterministic rules shared by all LLM modes."""
    m = RECORD_ID_RE.search(query)
    if m:
        return "loan_status", m.group(0).upper()
    if memory_record_id and _PRONOUN.search(query) and _STATUS_WORDS.search(query):
        return "loan_status", memory_record_id
    if (re.search(r"\bmy\b", query, re.I) and _LOAN_NOUN.search(query)
            and _STATUS_WORDS.search(query)):
        return "clarification", None
    if memory_record_id is None and _PRONOUN.search(query) and _STATUS_WORDS.search(query) \
            and re.search(r"\b(is|has|was|should)\s+it\b", query, re.I):
        return "clarification", None
    return "policy_question", None


class MockLLM:
    name = "MOCK_LLM"

    def generate_answer(self, query: str, contexts: list[str]) -> str:
        """Deterministic extractive 'generation': return the context sentences that
        best overlap the query (never anything outside the retrieved context)."""
        q = content_tokens(query)
        scored = []
        for ci, ctx in enumerate(contexts):
            sents = sentences(ctx)
            # fixed-size chunks can cut a sentence at either edge: prefer complete sentences
            whole = [s for s in sents if s[:1].isupper() and s[-1:] in ".!?"] or sents
            for si, s in enumerate(whole):
                overlap = len(q & content_tokens(s))
                scored.append((overlap, -ci, -si, s))
        if not scored:
            return ""
        scored.sort(reverse=True)
        best = [s for ov, _, _, s in scored[:2] if ov > 0] or [scored[0][3]]
        out: list[str] = []
        for s in best:
            if s not in out:
                out.append(s)
        return " ".join(out)


class _PromptedLLM(MockLLM):
    def _prompt(self, query: str, contexts: list[str]) -> str:
        ctx = "\n".join(f"- {c}" for c in contexts)
        return ("You are a bank support assistant. Answer ONLY using the context. If the context "
                "does not contain the answer, reply exactly: I don't know.\n"
                f"Context:\n{ctx}\n\nQuestion: {query}\nAnswer:")


class OllamaLLM(_PromptedLLM):
    name = f"OLLAMA:{config.OLLAMA_MODEL}"

    def generate_answer(self, query, contexts):
        import httpx
        r = httpx.post(f"{config.OLLAMA_URL}/api/generate", timeout=config.NODE_TIMEOUT_S,
                       json={"model": config.OLLAMA_MODEL, "prompt": self._prompt(query, contexts),
                             "stream": False})
        r.raise_for_status()
        return r.json()["response"].strip()


class GeminiLLM(_PromptedLLM):
    name = f"GEMINI:{config.GEMINI_MODEL}"

    def generate_answer(self, query, contexts):
        import httpx
        if not config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set")
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{config.GEMINI_MODEL}:generateContent")
        r = httpx.post(url, headers={"x-goog-api-key": config.GEMINI_API_KEY},
                       timeout=config.NODE_TIMEOUT_S,
                       json={"contents": [{"parts": [{"text": self._prompt(query, contexts)}]}]})
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def get_llm():
    mode = config.LLM_MODE
    if mode == "OLLAMA":
        return OllamaLLM()
    if mode == "GEMINI":
        return GeminiLLM()
    return MockLLM()
