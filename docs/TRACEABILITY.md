# Requirement Traceability Matrix

Source of truth: *Final Capstone — Cred Domain Support Agent (LangGraph)* PDF (11 pages).
Status values: **PASS** = automated test and/or executed transcript exists and passed in this repo. **NOT TESTED** = implemented but no verification run. **PARTIAL** = noted limitation.

## A. Mandatory capstone requirements

| ID | Requirement | Implementation | Verification | Status |
|---|---|---|---|---|
| T1 | Seeded generator, ≥40 `LOAN_APPLICATIONS`, all categories/statuses, required fields, `days_since_created` 0–30 | `dataset.py` | `tests/test_part1…::test_dataset_thresholds`, `::test_dataset_is_deterministic`; `transcripts/dataset_report.txt` | PASS |
| T1b | Print counts per category (≥3) / status (≥1) / fraud % in 10–30 | `dataset.py __main__` | `transcripts/dataset_report.txt` (18.33 %) | PASS |
| T1c | README states seed, weights, amount range + one-sentence reasoning | `README.md` (top) | manual review | PASS |
| T2 | ≥12 KB docs, 2–5 sentences, all 12 required topics | `kb/kb01…kb15` | `::test_kb_has_12_plus_docs_of_2_to_5_sentences` | PASS (topic coverage by manual mapping kb01–kb12) |
| T3 | Fixed-with-overlap AND sentence chunking, MiniLM embeddings, one Chroma collection each | `app/rag.py` | `::test_chunkers_differ_and_overlap`, `::test_two_collections_retrieve_sensibly` | PASS |
| T4 | Grounded generation, empirically calibrated threshold (≥3 in-scope, ≥2 OOS measured), README states values, ≥5 in-scope + 1 OOS demo | `app/grounded.py`, `scripts/calibrate_threshold.py`, `scripts/demo_grounded.py` | `::test_grounded_answer_and_fallback`; `transcripts/threshold_calibration.txt`, `grounded_demo.txt` | PASS |
| T5 | P@3 / R@3 per collection, same ≥5 queries, per-query arithmetic, 2–3 sentence recommendation citing numbers | `scripts/eval_chunking.py` | `transcripts/chunking_eval.txt`; README | PASS (see caveat: small sample) |
| T6 | `check_loan_application_status(record_id)->dict` with status, `loan_amount_inr`, designed `escalation_score`∈[0,1]; formula + threshold justified from data | `app/loan_tool.py` | `::test_loan_tool_lookup_and_score_formula`; README Task 6 | PASS |
| T7 | LangGraph ≥4 nodes, ≥1 conditional edge routing to RAG vs loan tool; both routes demonstrated | `app/agent.py` | `::test_graph_has_4_nodes_and_conditional_edges`, `::test_both_routes_fire`; `transcripts/agent_demo.txt` | PASS |
| T8 | JSON-file persisted memory; multi-turn transcript + separate fresh-conversation transcript | `app/memory.py` | `::test_memory_multi_turn_vs_fresh`, `::test_memory_persists_across_restart`; `agent_demo.txt` parts B, C | PASS |
| T9 | Structured-output JSON Schema validated in code on every response | `app/schemas.py` | `::test_every_response_validates_against_schema` | PASS |
| T10 | Input PII masking (PAN/Aadhaar/account) + injection detection; output groundedness refusal; each demonstrated | `app/guardrails.py`, `app/agent.py` | `::test_pii_masked_and_not_persisted`, `::test_prompt_injection_blocked`, `::test_groundedness_guard_refuses_hallucination`; `agent_demo.txt` part D | PASS |
| T11 | FastAPI ≥2 endpoints with Pydantic models | `app/api.py` (`/ask`, `/add-document`, +more) | `tests/test_part3_api.py` (6 tests); live curl check | PASS |
| T12 | One JSONL log entry/request with trace ID + timing; raw PII never logged | `app/api.py` middleware, `app/logging_setup.py` | `::test_jsonl_log_has_trace_id_and_no_raw_pii` | PASS |
| T13 | 15-query RAG triad under MOCK_LLM, ≥1 per KB topic, ≥2 OOS/edge, 3 scores per query + averages | `app/judge.py`, `scripts/eval_triad.py` | `transcripts/triad_eval.txt`, `artifacts/triad_eval.json` | PASS (executed; proxy metrics — see limitations) |
| T14 | fastmcp server exposing the tool at `/mcp`; separate client calling ≥2 record IDs | `mcp_server.py`, `mcp_client.py` | `::test_mcp_round_trip_two_ids`; `transcripts/mcp_demo.txt` | PASS |
| T15 | `langgraph-checkpoint-sqlite`, thread-id keyed; stop mid-run, resume, completed nodes not re-executed | `app/agent.py`, `scripts/demo_checkpoint.py` | `::test_checkpoint_resume_does_not_reexecute`; `transcripts/checkpoint_demo.txt` | PASS |
| T16 | Per-node + global timeout; exponential-backoff retry with stated params; 3 demonstrations | `app/resilience.py`, `scripts/demo_resilience.py` | `::test_retry_recovers_transient_failure`, `::test_per_node_timeout_clean_error`, `::test_global_timeout_cancels_run`; `transcripts/resilience_demo.txt` | PASS |
| S1 | Single public GitHub repo, README top says Cred track, all runs under MOCK_LLM with no keys | repo layout, `README.md` | MOCK_LLM tests pass with no keys; offline run of grounded demo with `HF_HUB_OFFLINE=1` | PARTIAL — repo not yet pushed/published (user action) |
| S2 | No images/screenshots/PDFs/etc. in submission | `.gitignore` excludes the problem-statement PDF | manual | PASS (PDF excluded from git; delete local copy if desired) |

## B. Additional enterprise features (from the master brief)

| Feature | Implementation | Status |
|---|---|---|
| React/Vite/MUI/Recharts/Axios UI, 10 sections, live backend data | `frontend/` | PARTIAL — compiles (`npm run build`), dev server serves, API/CORS verified by curl; not visually inspected |
| LLM abstraction MOCK_LLM / Ollama / Gemini | `app/llm.py` | MOCK_LLM PASS; Ollama & Gemini NOT TESTED (no server/key) |
| Regulatory registry with versioning/supersede/offline | `app/regulatory.py` | PASS against local HTTP server; NOT TESTED against real official sites |
| Official RBI/MoF/DFS/India Code documents pre-loaded | — | NOT DONE (deliberately: would require verifying provenance/currency; registry is empty by design) |
| Agent Monitor / System Monitor / Analytics endpoints | `/monitor/*`, `/analytics/rag` | implemented; endpoints exercised only indirectly (`/stats`, `/health` in tests) — NOT TESTED individually |

## C. Optional enhancements not implemented

Scheduled regulatory updates; screenshots (not accepted by the brief); Docker packaging.
