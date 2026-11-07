"""Central configuration. Everything is overridable by environment variables."""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "kb"
DATA_DIR = Path(os.getenv("CRED_DATA_DIR", ROOT / "data"))  # tests point this at a temp dir
ARTIFACTS_DIR = ROOT / "artifacts"
LOG_DIR = Path(os.getenv("CRED_LOG_DIR", ROOT / "logs"))
for _d in (DATA_DIR, ARTIFACTS_DIR, LOG_DIR):
    _d.mkdir(exist_ok=True)

# --- LLM -----------------------------------------------------------------
# MOCK_LLM (default, no keys, no network) | OLLAMA | GEMINI (optional)
LLM_MODE = os.getenv("LLM_MODE", "MOCK_LLM").upper()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # never hardcode
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# --- RAG -----------------------------------------------------------------
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", DATA_DIR / "chroma"))
COLLECTION_FIXED = "kb_fixed_overlap"
COLLECTION_SENTENCE = "kb_sentence"
# Part 2 uses the recommended strategy's collection (set after Task 5 analysis).
AGENT_COLLECTION = os.getenv("AGENT_COLLECTION", COLLECTION_FIXED)
TOP_K = int(os.getenv("TOP_K", "3"))
FIXED_CHUNK_CHARS = 300
FIXED_OVERLAP_CHARS = 60
SENTENCES_PER_CHUNK = 2

_CAL = ARTIFACTS_DIR / "calibration.json"
_DEFAULT_THRESHOLD = 0.30  # only used if calibration has not been run yet


def similarity_threshold(collection: str | None = None) -> float:
    """"I don't know" threshold, set empirically by scripts/calibrate_threshold.py
    (one value per collection because chunk sizes shift the similarity scale)."""
    if "SIM_THRESHOLD" in os.environ:
        return float(os.environ["SIM_THRESHOLD"])
    if _CAL.exists():
        cal = json.loads(_CAL.read_text())
        return float(cal[collection or AGENT_COLLECTION]["threshold"])
    return _DEFAULT_THRESHOLD


# --- Escalation (Task 6) --------------------------------------------------
W_FRAUD = 0.5
W_AGE = 0.5
MAX_DAYS = 30
ESCALATION_THRESHOLD = 0.70

# --- Resilience -----------------------------------------------------------
NODE_TIMEOUT_S = float(os.getenv("NODE_TIMEOUT_S", "20"))
GLOBAL_TIMEOUT_S = float(os.getenv("GLOBAL_TIMEOUT_S", "60"))
RETRY_MAX_ATTEMPTS = 3
RETRY_INITIAL_INTERVAL = 0.2
RETRY_MAX_INTERVAL = 2.0
RETRY_BACKOFF = 2.0
RETRY_JITTER = True

# --- Persistence ----------------------------------------------------------
CHECKPOINT_DB = str(DATA_DIR / "checkpoints.sqlite")
CONVERSATIONS_JSON = DATA_DIR / "conversations.json"
REQUEST_LOG = LOG_DIR / "requests.jsonl"
MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:8001/mcp")
