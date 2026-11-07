"""Task 4: grounded generation on >=5 in-scope queries + 1 out-of-scope query (must fall back)."""
import os
import sys
from pathlib import Path

os.environ["LLM_MODE"] = "MOCK_LLM"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config  # noqa: E402
from app.grounded import grounded_answer  # noqa: E402

QUERIES = ["What is the minimum monthly income needed for a personal loan?",
           "How do I dispute an unauthorised card transaction?",
           "What is the process to close my savings account?",
           "Is there a penalty for prepaying a fixed-rate loan?",
           "Can a non-resident Indian open an NRE account?",
           "What KYC documents do I need to submit?",
           "Who won the cricket world cup final?"]  # <- deliberately out of scope
col = config.AGENT_COLLECTION
print(f"collection={col}  calibrated threshold={config.similarity_threshold(col)}\n")
for q in QUERIES:
    r = grounded_answer(q, col)
    print(f"Q: {q}\n   top-1 similarity = {r['top1']:.4f}  (threshold {r['threshold']})  "
          f"-> {'FALLBACK' if r['fallback'] else 'ANSWER'}")
    print(f"   sources: {sorted({h['doc_id'] for h in r['hits']})}")
    print(f"   A: {r['answer']}\n")
