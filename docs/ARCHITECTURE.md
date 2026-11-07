# Architecture

```
React UI (5173) ──axios──▶ FastAPI (8000) ──▶ SupportAgent (LangGraph + SqliteSaver)
                                                  │            │
                                     rag.py ◀─────┘            └──▶ loan_tool.py ◀── dataset.py
                        ChromaDB: kb_fixed_overlap | kb_sentence | regulatory_docs
                        SentenceTransformers all-MiniLM-L6-v2 (local)

mcp_client.py ──MCP/HTTP──▶ mcp_server.py (8001/mcp) ──▶ loan_tool.py     (separate processes)
```

## Graph state flow
`guard_input` masks PII/detects injection/validates → conditional edge → `refuse` | `classify_intent`.
`classify_intent` (rule-based, memory-aware) → conditional edge → `rag_retrieve` | `loan_lookup` | `clarify`.
`generate_answer` (RAG: LLM over retrieved chunks, or fallback if top-1 similarity < calibrated threshold; loan: templated from tool output only) → `groundedness_check` (support ratio ≥ 0.7, else fallback; PII re-masked) → `finalize` (schema validation, memory write).

## Persistence
* `data/checkpoints.sqlite` — LangGraph checkpoints keyed by `thread_id` = conversation id.
* `data/conversations.json` — conversation memory (masked text only).
* `data/chroma/` — vector indexes (rebuilt automatically if missing).
* `logs/requests.jsonl` — request log. All of `data/` and `logs/` are git-ignored.

## Design decisions
* Intent routing is deterministic rules so MOCK_LLM exercises the real workflow and routes are reproducible.
* Warm-up of the embedding model happens at agent construction so cold model loading cannot trip the per-node timeout (found and fixed during testing).
* Retry applies only to `TransientError`/`ConnectionError`; timeouts are surfaced, not retried.
* Fixed-size chunks can cut sentences; the extractive generator prefers whole sentences.
