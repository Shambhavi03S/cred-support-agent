"""Task 13: deterministic MOCK_LLM-as-judge for the RAG triad.

JUDGE_PROMPT is the rubric a real LLM judge would receive. Under MOCK_LLM no model is
available, so the same three rubric questions are answered by transparent, deterministic
scorers (each returns a value in [0, 1]):

  context_relevance : share of retrieved chunks that are on-topic for the query
                      (query-chunk cosine similarity >= calibrated threshold).
  groundedness      : share of answer sentences whose content words are >=70 % present
                      in the retrieved context (lexical entailment proxy).
  answer_relevance  : cosine similarity between query and answer embeddings, floored at 0.

Abstention handling: when the agent declines (fallback) on a query that IS out of scope,
that is the correct behaviour -> groundedness = 1 (no unsupported claims) and
answer_relevance = 1; context_relevance is still computed honestly from retrieval. A
fallback on an in-scope query scores answer_relevance = 0.
"""
from __future__ import annotations

import numpy as np

from . import config, rag
from .guardrails import support_ratio

JUDGE_PROMPT = """You are an impartial judge of a retrieval-augmented banking assistant.
Given QUESTION, CONTEXT (retrieved chunks) and ANSWER, score each from 0 to 1:
1. context_relevance - are the retrieved chunks relevant to the QUESTION?
2. groundedness      - is every claim in the ANSWER supported by the CONTEXT?
3. answer_relevance  - does the ANSWER address the QUESTION?
Return JSON: {"context_relevance": x, "groundedness": y, "answer_relevance": z}"""


def _cos(a: str, b: str) -> float:
    ea, eb = rag.embed([a, b])
    return float(np.dot(ea, eb))


def judge(question: str, contexts: list[dict], answer: str, fallback: bool,
          out_of_scope: bool, collection: str | None = None) -> dict:
    thr = config.similarity_threshold(collection)
    cr = (sum(1 for c in contexts if c["similarity"] >= thr) / len(contexts)) if contexts else 0.0
    if fallback:
        gr = 1.0
        ar = 1.0 if out_of_scope else 0.0
    else:
        gr = support_ratio(answer, [c["text"] for c in contexts])
        ar = max(0.0, _cos(question, answer))
    return {"context_relevance": round(cr, 4), "groundedness": round(gr, 4),
            "answer_relevance": round(ar, 4)}
