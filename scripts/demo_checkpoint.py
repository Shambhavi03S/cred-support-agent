"""Task 15: SQLite checkpointing -- stop mid-run, resume the SAME thread id, show that
completed nodes were NOT re-executed (loaded from the checkpoint)."""
import os
import sys
from pathlib import Path

os.environ["LLM_MODE"] = "MOCK_LLM"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config  # noqa: E402
from app.agent import SupportAgent  # noqa: E402
from app.memory import ConversationStore  # noqa: E402
from app.resilience import EXEC_COUNTS  # noqa: E402

db = config.DATA_DIR / "demo_ckpt_only.sqlite"
db.unlink(missing_ok=True)
THREAD = "ckpt-thread-001"
store = ConversationStore(config.DATA_DIR / "demo_ckpt_conversations.json")
cfg = {"configurable": {"thread_id": THREAD}}
inputs = {"query": "What is the prepayment penalty on a fixed-rate loan?",
          "conversation_id": THREAD, "trace_id": "ckpt-demo"}

print("(a)+(b) RUN 1: graph stops BEFORE 'generate_answer' (simulated interruption)")
a1 = SupportAgent(str(db), store, interrupt_before=["generate_answer"])
a1.graph.invoke(inputs, cfg)
snap = a1.state(THREAD)
print("   nodes completed so far :", snap.values["nodes"])
print("   next node(s) pending   :", list(snap.next))
print("   execution counters     :", dict(EXEC_COUNTS))
assert snap.next == ("generate_answer",)
done_before = dict(EXEC_COUNTS)
a1.conn.close()  # simulate process death: connection gone, only checkpoints.sqlite remains

print("\n(c) RUN 2: NEW agent object + NEW sqlite connection, resume SAME thread id")
EXEC_COUNTS.clear()
a2 = SupportAgent(str(db), store, interrupt_before=["generate_answer"])
loaded = a2.state(THREAD)
print("   state loaded from checkpoint -> nodes:", loaded.values["nodes"],
      "| retrieved chunks:", len(loaded.values["hits"]))
final = a2.graph.invoke(None, cfg)  # resume
print("   final nodes_executed   :", final["response"]["nodes_executed"])
print("   executions during resume:", dict(EXEC_COUNTS))
for n in ("guard_input", "classify_intent", "rag_retrieve"):
    assert EXEC_COUNTS[n] == 0, f"{n} was re-executed!"
for n in ("generate_answer", "groundedness_check", "finalize"):
    assert EXEC_COUNTS[n] == 1, f"{n} should run exactly once on resume"
print("   answer:", final["response"]["answer"])
print("\nPASS: guard_input, classify_intent, rag_retrieve ran once before the stop "
      f"({done_before}); on resume they were loaded from the checkpoint and NOT re-executed.")
