import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp(prefix="cred_test_")
os.environ["CRED_DATA_DIR"] = str(Path(_tmp) / "data")
os.environ["CRED_LOG_DIR"] = str(Path(_tmp) / "logs")
os.environ["LLM_MODE"] = "MOCK_LLM"
(Path(_tmp) / "data").mkdir()
(Path(_tmp) / "logs").mkdir()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
