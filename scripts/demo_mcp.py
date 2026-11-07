"""Task 14 demo: launch the private MCP server as a subprocess, then run the separate
client script against http://127.0.0.1:8001/mcp (a real client/server round trip)."""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
env = {**os.environ, "MCP_PORT": "8001"}
server = subprocess.Popen([sys.executable, str(ROOT / "mcp_server.py")], cwd=ROOT, env=env,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", 8001), timeout=0.5).close()
            break
        except OSError:
            time.sleep(0.5)
    else:
        raise SystemExit("MCP server did not start")
    print("MCP server up at http://127.0.0.1:8001/mcp\n")
    rc = subprocess.call([sys.executable, str(ROOT / "mcp_client.py"), "LA-1001", "LA-1005", "LA-1009",
                          "LA-9999"], cwd=ROOT, env=env)
    print("\nclient exit code:", rc)
    sys.exit(rc)
finally:
    server.terminate()
