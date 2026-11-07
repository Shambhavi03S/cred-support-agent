"""Task 5: Precision@3 / Recall@3 at the document level for BOTH collections,
with per-query arithmetic (chunks -> parent docs -> dedup -> top 3 docs).

Set A = the 10 single-gold Task-4 queries (P@3 is capped at 1/3 there).
Set B = 6 multi-gold queries (answer spans 2-3 docs) where the metrics can discriminate.
Also reports a chunk-level supplementary signal: mean top-1 cosine similarity."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config, rag  # noqa: E402
from app.evalsets import IN_SCOPE, MULTI_GOLD  # noqa: E402

rag.ensure_index()
summary, lines = {}, []


def out(s=""):
    print(s)
    lines.append(s)


for set_name, qs in (("A_single_gold", IN_SCOPE), ("B_multi_gold", MULTI_GOLD)):
    out(f"\n################ SET {set_name} ({len(qs)} queries) ################")
    for col in (config.COLLECTION_FIXED, config.COLLECTION_SENTENCE):
        out(f"\n=== {set_name} / {col} ===")
        ps, rs, tops, rows = [], [], [], []
        for q, gold in qs:
            docs = rag.retrieve_docs(q, col, k=3)
            hit = [d for d in docs if d in gold]
            p, r = len(hit) / 3, len(hit) / len(gold)
            top1 = rag.retrieve(q, col, 1)[0]["similarity"]
            ps.append(p); rs.append(r); tops.append(top1)
            rows.append({"query": q, "gold": gold, "retrieved_docs": docs, "hits": len(hit),
                         "precision@3": round(p, 4), "recall@3": round(r, 4), "top1_similarity": top1})
            out(f"Q: {q}\n   gold={gold}\n   top-3 unique docs={docs}\n"
                f"   P@3 = {len(hit)}/3 = {p:.3f}   R@3 = {len(hit)}/{len(gold)} = {r:.3f}   "
                f"top-1 sim = {top1:.4f}")
        n = len(ps)
        out(f"MEAN over {n}: P@3 = {sum(ps)/n:.4f}   R@3 = {sum(rs)/n:.4f}   "
            f"mean top-1 sim = {sum(tops)/n:.4f}")
        summary[f"{set_name}/{col}"] = {
            "mean_precision@3": round(sum(ps) / n, 4), "mean_recall@3": round(sum(rs) / n, 4),
            "mean_top1_similarity": round(sum(tops) / n, 4), "per_query": rows,
            "n_chunks": rag.get_client().get_collection(col).count()}

(config.ARTIFACTS_DIR / "chunking_eval.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
(config.ARTIFACTS_DIR / "chunking_eval.txt").write_text("\n".join(lines), encoding="utf-8")
out("\nChunk counts: " + ", ".join(f"{c}={rag.get_client().get_collection(c).count()}"
                                   for c in (config.COLLECTION_FIXED, config.COLLECTION_SENTENCE)))
