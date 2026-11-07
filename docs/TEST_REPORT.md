# Test Report

Executed on 2026-11-07, Windows 11, Python 3.12.10, `LLM_MODE=MOCK_LLM`, no API keys.

Command: `.\.venv\Scripts\python.exe -m pytest tests -v` → **30 passed, 0 failed** (full output: `docs/pytest_output.txt`).

| File | Tests | Result |
|---|---|---|
| tests/test_part1_dataset_rag.py | 6 | PASS |
| tests/test_part2_agent.py | 11 | PASS |
| tests/test_part3_api.py | 6 | PASS |
| tests/test_part4_mcp_resilience.py | 6 | PASS |
| tests/test_regulatory.py | 1 | PASS |

Additional executed checks (see `transcripts/`): dataset report, threshold calibration, grounded demo (6 in-scope + 1 OOS fallback), chunking P@3/R@3, agent demo (routes, memory, fresh conversation, guardrails), 15-query RAG triad, MCP round trip (4 IDs incl. one unknown), checkpoint resume, retry/timeouts, and a grounded demo with `HF_HUB_OFFLINE=1`.
Live smoke test (uvicorn + curl): `/health`, `/ask` with a PAN in the query, `/stats`, `/docs`, `/openapi.json`, CORS preflight from `http://localhost:5173` — all OK; PAN absent from `logs/requests.jsonl`.

## Defects found and fixed during testing
1. Cold embedding-model load inside a timed node exceeded the 20 s node timeout in standalone scripts → model/index warmed in `SupportAgent.__init__`.
2. Chunk comparison on single-gold queries was a degenerate tie → added multi-gold query set B and reported both sets.
3. Fixed-size chunks produced answers ending mid-sentence → generator prefers complete sentences.

## NOT TESTED
* Ollama and Gemini providers (no local server / key).
* Regulatory update against real official URLs.
* Frontend in a real browser (build + dev server + API calls verified only).
* Concurrent-load behaviour; production deployment.
