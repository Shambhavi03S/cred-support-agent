"""Task 4: measure top-1 cosine similarity for in-scope vs out-of-scope queries and
set the "I don't know" threshold between the two observed clusters."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config, rag  # noqa: E402
from app.evalsets import IN_SCOPE, OUT_OF_SCOPE  # noqa: E402

rag.index_documents(rag.load_kb_documents(), reset=True)
result = {}
for col in (config.COLLECTION_FIXED, config.COLLECTION_SENTENCE):
    print(f"\n=== {col} ===")
    ins = [(q, rag.retrieve(q, col, 1)[0]["similarity"]) for q, _ in IN_SCOPE]
    oos = [(q, rag.retrieve(q, col, 1)[0]["similarity"]) for q in OUT_OF_SCOPE]
    print("in-scope top-1 similarity:")
    for q, s in ins:
        print(f"   {s:.4f}  {q}")
    print("out-of-scope top-1 similarity:")
    for q, s in oos:
        print(f"   {s:.4f}  {q}")
    lo_in, hi_oos = min(s for _, s in ins), max(s for _, s in oos)
    separated = lo_in > hi_oos
    thr = round((lo_in + hi_oos) / 2, 4)
    print(f"min(in-scope)={lo_in:.4f}  max(out-of-scope)={hi_oos:.4f}  "
          f"separated={separated}  -> threshold={thr}")
    result[col] = {"threshold": thr, "min_in_scope": lo_in, "max_out_of_scope": hi_oos,
                   "clusters_separated": separated,
                   "in_scope": {q: s for q, s in ins}, "out_of_scope": {q: s for q, s in oos}}

(config.ARTIFACTS_DIR / "calibration.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print("\nsaved artifacts/calibration.json")
