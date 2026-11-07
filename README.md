# Cred Domain Support Agent (LangGraph)

> **Track completed: Cred (Banking & FinTech).**
> Everything runs under `MOCK_LLM` with **zero API keys and zero network access** (after the one-time download of the free `all-MiniLM-L6-v2` embedding model, which is then cached; verified with `HF_HUB_OFFLINE=1`).

## Part 1 / Task 1 — exact dataset-design choices (reproduce with `python dataset.py`)

| Choice | Value |
|---|---|
| Seed | `SEED = 7` (`random.Random(7)`), `N_RECORDS = 60` |
| Category weights | Personal 0.28 · Home 0.18 · Auto 0.20 · Education 0.14 · Business 0.20 |
| Status weights | Submitted 0.22 · Under Review 0.26 · Approved 0.20 · Rejected 0.14 · Disbursed 0.18 |
| Amount range (INR, per category, rounded to 5,000) | Personal 50k–15L · Home 15L–1.5Cr · Auto 3L–25L · Education 2L–30L · Business 5L–1Cr |
| Amount reasoning (one sentence) | Ranges mirror typical retail-bank ticket sizes, from small unsecured personal loans to large secured home loans, so amounts differ realistically by product. |
| `days_since_created` | uniform integer 0–30 |
| Fraud-review probability | 0.20 per record (Bernoulli) |

Measured output of the generator (seed 7, nothing hand-edited):
categories: Personal 19, Home 7, Auto 10, Education 8, Business 16 (all ≥ 3) ·
statuses: Submitted 15, Under Review 10, Approved 15, Rejected 7, Disbursed 13 (all ≥ 1) ·
fraud-flagged: 11/60 = **18.33 %** (band 10–30 %). `validate()` raises if any threshold is violated.
Extra fabricated fields: `customer_id`, `applicant_name`, `created_date` (relative to fixed `REFERENCE_DATE`). Applicant name / income are not masked (out of scope per the brief); PAN, Aadhaar and bank-account numbers are.

## Quick start (Windows / PowerShell, Python 3.12, Node 18+)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\start_backend.ps1        # FastAPI  http://127.0.0.1:8000   (Swagger: /docs)
.\start_frontend.ps1       # React UI http://127.0.0.1:5173
.\start_mcp_server.ps1     # MCP      http://127.0.0.1:8001/mcp   then: python mcp_client.py LA-1001 LA-1005
.\run_all_demos.ps1        # regenerates every transcript + artifact + runs the tests
.\.venv\Scripts\python.exe -m pytest tests -v
```
Optional real LLMs (never needed): copy `.env.example`, set `LLM_MODE=OLLAMA` or `GEMINI` (+ `GEMINI_API_KEY`). Only answer *generation* is swapped; routing, guardrails and evaluation stay deterministic.

## Repository map

| Path | Purpose |
|---|---|
| `dataset.py` | Seeded `LOAN_APPLICATIONS` generator + validation (Task 1) |
| `kb/*.md` | 15 hand-written KB documents (Task 2) |
| `app/rag.py` | ingestion, **two chunkers**, MiniLM embeddings, two ChromaDB collections, retrieval (Tasks 3, 5) |
| `app/grounded.py`, `app/llm.py` | grounded generation, MOCK_LLM / Ollama / Gemini abstraction (Task 4) |
| `app/loan_tool.py` | `check_loan_application_status` + escalation score (Task 6) |
| `app/agent.py` | LangGraph graph, SQLite checkpointer (Tasks 7, 15) |
| `app/memory.py` | JSON-file conversation memory (Task 8) |
| `app/schemas.py`, `schemas/agent_response.schema.json` | structured output schema + validation (Task 9) |
| `app/guardrails.py` | PII masking, injection detection, groundedness support check (Task 10) |
| `app/api.py`, `app/logging_setup.py` | FastAPI + JSON-Lines logging (Tasks 11, 12) |
| `app/judge.py`, `scripts/eval_triad.py` | RAG-triad judge + 15-query evaluation (Task 13) |
| `mcp_server.py`, `mcp_client.py` | fastmcp server (`/mcp`) + separate client (Task 14) |
| `app/resilience.py`, `scripts/demo_resilience.py` | retry / per-node / global timeouts (Task 16) |
| `app/regulatory.py` | optional regulatory registry with manual update + versioning |
| `frontend/` | React + Vite + MUI + Recharts + Axios UI (10 sections) |
| `transcripts/` | **executed** output of every demo (see below) · `artifacts/` JSON results · `docs/` |

## Task 4 — empirically calibrated "I don't know" threshold

Top-1 cosine similarity measured with `all-MiniLM-L6-v2` (`scripts/calibrate_threshold.py`, `transcripts/threshold_calibration.txt`):

| Collection | In-scope (10 queries) min – max | Out-of-scope (5 queries) max | **Chosen threshold** (midpoint) |
|---|---|---|---|
| `kb_fixed_overlap` | 0.631 – 0.798 | 0.159 | **0.3952** |
| `kb_sentence` | 0.619 – 0.806 | 0.164 | 0.3912 |

The two clusters are cleanly separated, so the threshold sits in the empty gap rather than at a tutorial default (0.5/0.6/0.7). Caveat: the out-of-scope queries are *blatantly* unrelated (cricket, recipes…); banking-adjacent questions that the KB does not cover could score higher, and a gap that wide may not hold on a larger KB. Demonstration: 6 in-scope queries answered with sources, 1 out-of-scope query → fallback (`transcripts/grounded_demo.txt`).

## Task 5 — chunking strategies compared (document level, `transcripts/chunking_eval.txt`)

Procedure: top chunks → parent document → dedup → first 3 unique docs; `P@3 = hits/3`, `R@3 = hits/|gold|`. Per-query arithmetic is printed in the transcript. Collections: `kb_fixed_overlap` (300-char windows, 60-char overlap, 34 chunks) vs `kb_sentence` (2 sentences/chunk, 31 chunks).

| Query set | Fixed + overlap P@3 / R@3 | Sentence P@3 / R@3 |
|---|---|---|
| A: 10 single-gold queries (P@3 capped at 0.333) | 0.333 / 1.000 | 0.333 / 1.000 (tie) |
| B: 6 multi-gold queries | **0.722 / 0.917** | 0.667 / 0.861 |

**Recommendation:** deploy the fixed-size-with-overlap collection. It tied on the single-gold set (both 0.333/1.000) and was ahead on the multi-gold set (P@3 0.722 vs 0.667, R@3 0.917 vs 0.861), with slightly higher mean top-1 similarity (0.596 vs 0.573). Honest caveat: the set-B gap comes from one extra document found in two of six queries, and the KB docs are only 2–5 sentences, so the strategies differ little; this is weak evidence, not a decisive win. The agent therefore uses `AGENT_COLLECTION = kb_fixed_overlap` (changeable by env var). Set A was kept in the report because it shows why the single-gold set could not discriminate.

## Task 6 — escalation score

`escalation_score = 0.5 · flagged_for_fraud_review + 0.5 · (days_since_created / 30)`, clipped to [0, 1]. **Escalate if score ≥ 0.70.**
Justification from this dataset (seed 7): 0.70 is the **90th percentile of all 60 escalation scores** (exactly 6 records = 10 %, which is a workable daily review load). It is reached by fraud-flagged applications aged ≥ 12 days (12 days ≈ the 45th percentile of `days_since_created`; the 80th percentile is 24 days). Of 11 fraud-flagged records, 6 escalate. An unflagged application tops out at 0.50, so age alone only means “monitor”, and a fraud flag alone (0.5) needs some ageing before it escalates; this is deliberately not a boolean OR.

## Part 2 — LangGraph agent (9 nodes, 2 conditional edges)

```
START → guard_input ─(injection/invalid)→ refuse ───────────────────────┐
              │                                                          │
              └→ classify_intent ─(policy)──→ rag_retrieve ─┐            │
                      ├─(loan_status)→ loan_lookup ─────────┴→ generate_answer → groundedness_check ─┐
                      └─(needs record id)→ clarify ──────────────────────────────────────────────────┤
                                                                                                      └→ finalize → END
```
`rag_retrieve` and `generate_answer` carry the retry policy and per-node timeout; `finalize` validates the response against the JSON Schema and writes memory. Transcript: `transcripts/agent_demo.txt` (both routes firing, multi-turn memory, a **separate fresh conversation** where the same follow-up correctly gets “which record ID?”, schema validation per response, every guardrail firing).

* **Memory (Task 8):** `data/conversations.json` (atomic writes). A pronoun follow-up (“is it flagged…?”) resolves to the last record in the same conversation id only. Verified to survive an agent “restart” (`test_memory_persists_across_restart`).
* **Structured output (Task 9):** Pydantic `AgentResponse` → `schemas/agent_response.schema.json`; `jsonschema.validate` runs on every response in `finalize`.
* **Guardrails (Task 10):** input side — PAN / Aadhaar / bank-account regex masking (applied before the model, memory and logs), prompt-injection patterns, length/empty validation; output side — retrieval-similarity threshold **and** a sentence-level support check against the retrieved context. The output check is demonstrated against a deliberately hallucinating generator (`transcripts/agent_demo.txt`, end).

## Part 3 — API, logging, evaluation

* Endpoints (Swagger at `/docs`): `POST /ask`, `POST /add-document`, `GET /health`, `GET /loans`, `GET /loans/{id}`, `GET /conversations[/{id}]`, `GET /knowledge/documents`, `GET /knowledge/search`, `GET /stats`, `/monitor/*`, `/analytics/rag`, `/regulatory/*`. All with Pydantic models; 422 on invalid bodies, 404/504/500 JSON errors.
* Logging: one JSON-Lines entry per request in `logs/requests.jsonl` (`ts, trace_id, method, path, status, duration_ms, query_masked`); `X-Trace-Id` response header. The query is masked *before* logging; test asserts the raw PAN/account never reaches disk.
* **RAG triad (Task 13)** over 15 queries (13 in-scope covering all 12 required topics + escalation policy, 2 out-of-scope): `transcripts/triad_eval.txt`, `artifacts/triad_eval.json`.

| Score (MOCK_LLM judge) | Average over 15 |
|---|---|
| Context relevance | **0.7556** |
| Groundedness | **1.0000** |
| Answer relevance | **0.6378** |

Judge definitions are in `app/judge.py` (context relevance = share of retrieved chunks above the calibrated threshold; groundedness = share of answer sentences ≥70 % lexically supported by context; answer relevance = query↔answer embedding cosine; correct abstention on out-of-scope queries scores 1 for groundedness and answer relevance). **Limitations, stated plainly:** the mock generator is extractive, so groundedness is 1.0 by construction and mainly shows nothing leaked outside the context; the context-relevance average is capped near 0.67–0.75 because top-3 retrieval returns two off-topic chunks for single-document questions. These are proxy metrics, not a real LLM judge. All 15 queries behaved correctly on the fallback decision (no mismatches).

## Part 4 — Resilience & MCP

* **MCP (Task 14):** `mcp_server.py` (fastmcp, tool has a docstring, streamable HTTP at `/mcp`, port 8001 so it does not clash with FastAPI on 8000) and a separate `mcp_client.py` that lists tools and calls the tool for LA-1001, LA-1005, LA-1009 and LA-9999 (unknown ID). `transcripts/mcp_demo.txt`.
* **Checkpointing (Task 15):** `SqliteSaver` (`data/checkpoints.sqlite`) keyed by thread id. `scripts/demo_checkpoint.py`: run stops before `generate_answer` after 3 nodes; a **new agent object and new SQLite connection** resumes the same thread; execution counters prove `guard_input`, `classify_intent`, `rag_retrieve` ran 0 times on resume and the remaining three ran once. `transcripts/checkpoint_demo.txt`.
* **Timeouts & retries (Task 16):** `RetryPolicy(max_attempts=4, initial_interval=0.2 s, backoff_factor=2.0, max_interval=1.0 s, jitter=True)`; demo node fails twice then succeeds on attempt 3; per-node timeout (0.5 s on a 3 s node) raises a clean `NodeTimeoutError` after 0.51 s; global timeout (1 s on a 10 s run) raises `GlobalTimeoutError` and the running node is genuinely cancelled (async path). `transcripts/resilience_demo.txt`. Limitation: for *synchronous* nodes (as in the live API) a timeout abandons the worker thread rather than killing it.

## Regulatory Centre (optional enhancement)

No regulatory text is bundled and nothing is claimed to be in force. An operator registers an official source URL, runs a manual **Update** while online; the text is hashed, versions are kept on disk, older versions marked superseded, and the latest is indexed into a separate `regulatory_docs` collection. Status stays *Unverified* until a human confirms. Offline, the last indexed copy keeps working. Tested against a local HTTP server (`tests/test_regulatory.py`); **not yet exercised against a real RBI/India Code URL** (HTML/PDF extraction is generic and may need tuning per site). Scheduled auto-updates are not implemented.

## Known limitations / assumptions

* KB policy figures (fees, rates, income limits) are **fictional bank policy** written for this exercise, not real Cred terms or RBI regulations.
* PII masking is regex-based; Aadhaar/account patterns can over- or under-match (e.g. any 9–18-digit number is masked as an account number).
* Intent classification is rule-based (deterministic) for every LLM mode.
* The frontend was built and compiled (`npm run build`) and its backend calls were verified with curl/CORS; it was **not** visually inspected in a browser in this session (screenshots are not part of this submission per the brief).
* Full requirement mapping: `docs/TRACEABILITY.md`; test results: `docs/TEST_REPORT.md`; architecture: `docs/ARCHITECTURE.md`.
