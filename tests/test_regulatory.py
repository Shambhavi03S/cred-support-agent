"""Optional enhancement: regulatory registry (local HTTP server stands in for an official source)."""
import functools
import http.server
import threading

import pytest

from app import rag, regulatory

TEXT_V1 = ("<html><body><p>" + "Illustrative circular text for testing only. " * 12 + "</p></body></html>")
TEXT_V2 = TEXT_V1.replace("testing only", "testing only, revised")


@pytest.fixture()
def server(tmp_path):
    (tmp_path / "circ.html").write_text(TEXT_V1, encoding="utf-8")
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    handler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield tmp_path, f"http://127.0.0.1:{srv.server_address[1]}/circ.html"
    srv.shutdown()


def test_register_update_version_supersede_and_offline(server):
    path, url = server
    regulatory.register("test_circ", "Test Circular", "Test Authority", url)
    r1 = regulatory.update("test_circ")
    assert r1["result"] == "updated" and r1["version"] == 1 and r1["chunks_indexed"] > 0
    assert regulatory.update("test_circ")["result"] == "unchanged"
    (path / "circ.html").write_text(TEXT_V2, encoding="utf-8")
    assert regulatory.update("test_circ")["version"] == 2
    doc = regulatory.list_documents()[0]
    assert [v["status"] for v in doc["versions"]] == ["superseded", "latest"]
    assert "Unverified" in doc["status"]  # never claims "in force"
    assert rag.retrieve("revised circular", regulatory.COLLECTION, 1)  # separate collection indexed
    # offline / unreachable source: existing copy untouched, no crash
    regulatory.register("dead", "Dead", "X", "http://127.0.0.1:9/none")
    assert regulatory.update("dead")["result"] == "fetch_failed"
