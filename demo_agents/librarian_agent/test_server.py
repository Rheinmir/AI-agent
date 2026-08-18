"""Test TẦNG GIAO THỨC (socket newline-JSON, dispatch method, lỗi thiếu param/method lạ/JSON méo)
bằng HANDLER GIẢ — không gọi model thật, cùng tinh thần mcp_tools/test_servers.py. asyncio.run()
bọc ngoài mỗi test (dự án không dùng pytest-asyncio, xem test_harness.py/test_guardrails.py cho
cùng convention)."""
import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from demo_agents.librarian_agent import client as librarian_client
from demo_agents.librarian_agent.server import LibrarianServer


async def _fake_search(library, query):
    return {"status": "done", "answer": f"echo:{library}:{query}"}


async def _fake_ingest(library, title, raw_text):
    return {"status": "done", "rel": f"sources/{title}.md", "raw_rel": f"sources/{title}-raw.md"}


async def _send(sock_path, payload_bytes):
    reader, writer = await asyncio.open_unix_connection(str(sock_path))
    writer.write(payload_bytes)
    await writer.drain()
    line = await reader.readline()
    writer.close()
    await writer.wait_closed()
    return line


async def _request(sock_path, req):
    line = await _send(sock_path, (json.dumps(req) + "\n").encode("utf-8"))
    return json.loads(line)


async def _with_server(coro_fn):
    with tempfile.TemporaryDirectory() as tmp:
        sock_path = Path(tmp) / "test.sock"
        server = LibrarianServer(search_fn=_fake_search, ingest_fn=_fake_ingest, sock_path=sock_path)
        task = asyncio.create_task(server.serve_forever())
        for _ in range(200):
            if sock_path.exists():
                break
            await asyncio.sleep(0.01)
        else:
            raise RuntimeError("server không start kịp")
        try:
            return await coro_fn(sock_path)
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


def test_ping():
    resp = asyncio.run(_with_server(lambda p: _request(p, {"id": "1", "method": "ping", "params": {}})))
    assert resp == {"id": "1", "result": {"type": "pong"}}


def test_library_search_dispatches_to_search_fn():
    req = {"id": "2", "method": "library.search", "params": {"library": "weather", "query": "hanoi"}}
    resp = asyncio.run(_with_server(lambda p: _request(p, req)))
    assert resp["id"] == "2"
    assert resp["result"] == {"status": "done", "answer": "echo:weather:hanoi"}


def test_library_search_missing_params_errors():
    req = {"id": "3", "method": "library.search", "params": {"library": "weather"}}
    resp = asyncio.run(_with_server(lambda p: _request(p, req)))
    assert "error" in resp
    assert "query" in resp["error"]["message"]


def test_library_ingest_dispatches_to_ingest_fn():
    req = {"id": "5", "method": "library.ingest",
           "params": {"library": "devops", "title": "Helm", "raw_text": "some raw text"}}
    resp = asyncio.run(_with_server(lambda p: _request(p, req)))
    assert resp["result"]["status"] == "done"
    assert resp["result"]["rel"] == "sources/Helm.md"


def test_library_ingest_missing_params_errors():
    req = {"id": "6", "method": "library.ingest", "params": {"library": "devops", "title": "Helm"}}
    resp = asyncio.run(_with_server(lambda p: _request(p, req)))
    assert "error" in resp


def test_unknown_method_errors():
    req = {"id": "4", "method": "nope", "params": {}}
    resp = asyncio.run(_with_server(lambda p: _request(p, req)))
    assert "error" in resp
    assert "nope" in resp["error"]["message"]


def test_malformed_json_line_does_not_crash_server():
    async def run(sock_path):
        reader, writer = await asyncio.open_unix_connection(str(sock_path))
        writer.write(b"not json at all\n")
        await writer.drain()
        writer.write((json.dumps({"id": "x", "method": "ping", "params": {}}) + "\n").encode("utf-8"))
        await writer.drain()
        line = await reader.readline()
        writer.close()
        await writer.wait_closed()
        return json.loads(line)

    resp = asyncio.run(_with_server(run))
    assert resp == {"id": "x", "result": {"type": "pong"}}


def test_client_roundtrip_uses_real_sync_socket_module():
    """client.py dùng socket module đồng bộ (không phải asyncio trực tiếp) — verify nó thật sự nói
    chuyện được với server async. PHẢI chạy call đồng bộ qua asyncio.to_thread (không phải
    threading.Thread + join trần) — join trần BLOCK event loop hiện tại, server không bao giờ được
    lên lịch xử lý connection -> client tự timeout (bug thật gặp khi viết test này)."""
    async def run(sock_path):
        return await asyncio.to_thread(
            librarian_client.ask_search, "weather", "hanoi", sock_path=sock_path, timeout=5,
        )

    value = asyncio.run(_with_server(run))
    assert value == {"status": "done", "answer": "echo:weather:hanoi"}


def test_client_raises_librarian_unavailable_when_socket_missing(tmp_path):
    with pytest.raises(librarian_client.LibrarianUnavailable):
        librarian_client.ask_search("weather", "hanoi", sock_path=tmp_path / "nope.sock", timeout=1)
