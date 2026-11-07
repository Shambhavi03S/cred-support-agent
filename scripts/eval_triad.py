"""Task 13: RAG-triad evaluation over 15 queries under MOCK_LLM (actually executed; nothing hard-coded)."""
import json
import os
import sys
from pathlib import Path

os.environ["LLM_MODE"] = "MOCK_LLM"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config, rag  # noqa: E402
from app.evalsets import TRIAD_QUERIES  # noqa: E402
from app.grounded import grounded_answer  # noqa: E402
from app.judge import JUDGE_PROMPT, judge  # noqa: E402

rag.ensure_index()
col = config.AGENT_COLLECTION
print(f"collection={col}  threshold={config.similarity_threshold(col)}  llm={config.LLM_MODE}\n")
rows = []
print(f"{'#':>2} {'ctx_rel':>7} {'ground':>7} {'ans_rel':>7}  {'fallback':<8} query")
for i, (q, gold, oos) in enumerate(TRIAD_QUERIES, 1):
    r = grounded_answer(q, col)
    s = judge(q, r["hits"], r["answer"], r["fallback"], oos, col)
    top_docs = [h["doc_id"] for h in r["hits"]]
    rows.append({"n": i, "query": q, "out_of_scope": oos, "gold": gold, "retrieved": top_docs,
                 "answer": r["answer"], "fallback": r["fallback"], "top1_similarity": r["top1"], **s})
    print(f"{i:>2} {s['context_relevance']:>7.3f} {s['groundedness']:>7.3f} "
          f"{s['answer_relevance']:>7.3f}  {str(r['fallback']):<8} {q}")
avg = {k: round(sum(r[k] for r in rows) / len(rows), 4)
       for k in ("context_relevance", "groundedness", "answer_relevance")}
print(f"\nAVERAGES over {len(rows)} queries: {avg}")
wrong = [r["query"] for r in rows if r["fallback"] != r["out_of_scope"]]
print("fallback behaviour mismatches (fallback != expected):", wrong or "none")
(config.ARTIFACTS_DIR / "triad_eval.json").write_text(
    json.dumps({"collection": col, "judge_prompt": JUDGE_PROMPT, "averages": avg,
                "mismatches": wrong, "rows": rows}, indent=2), encoding="utf-8")
