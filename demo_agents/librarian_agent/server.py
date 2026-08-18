"""Librarian socket server — giao thức THAM KHẢO `herdrdev/herdr` (đọc README + herdr.dev/docs/
socket-api/ thật, không tự chế): **newline-delimited JSON qua Unix domain socket**, request
`{"id","method","params"}` → response `{"id","result"}` hoặc `{"id","error":{"message"}}`. Đây là
bản RÚT GỌN của pattern đó — chỉ request/response đồng bộ, KHÔNG làm event-subscribe/`agent.wait`
đầy đủ (herdr dùng cho orchestrate NHIỀU pane/terminal, ngoài scope 1 tool-call đơn ở đây).

Methods hỗ trợ:
- `ping` → `{"type":"pong"}`
- `library.search` params `{library,query}` → `{"status":"done","answer"}`
- `library.ingest` params `{library,title,raw_text}` → `{"status":"done","rel","raw_rel"}`

`LibrarianServer` nhận `search_fn`/`ingest_fn` qua constructor (không hardcode gọi thẳng
`agent.py`) — để test_server.py verify được TẦNG GIAO THỨC (dispatch, lỗi thiếu param, JSON méo...)
bằng handler giả, không tốn gọi model thật mỗi lần chạy test (cùng tinh thần
mcp_tools/test_servers.py)."""
import asyncio
import json
from pathlib import Path

DEFAULT_SOCK_PATH = Path(__file__).parent / "librarian.sock"


class LibrarianServer:
    def __init__(self, search_fn, ingest_fn, sock_path=DEFAULT_SOCK_PATH):
        """search_fn(library, query) -> dict Awaitable, ingest_fn(library, title, raw_text) ->
        dict Awaitable — CÙNG shape với demo_agents.librarian_agent.agent.search/ingest_raw."""
        self.search_fn = search_fn
        self.ingest_fn = ingest_fn
        self.sock_path = Path(sock_path)

    async def dispatch(self, method, params):
        if method == "ping":
            return {"type": "pong"}
        if method == "library.search":
            library, query = params.get("library"), params.get("query")
            if not library or not query:
                raise ValueError("thiếu 'library' hoặc 'query'")
            return await self.search_fn(library, query)
        if method == "library.ingest":
            library, title, raw_text = params.get("library"), params.get("title"), params.get("raw_text")
            if not library or not title or not raw_text:
                raise ValueError("thiếu 'library'/'title'/'raw_text'")
            return await self.ingest_fn(library, title, raw_text)
        raise ValueError(f"method lạ '{method}'")

    async def _handle_line(self, line: bytes):
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            return None  # dòng méo — bỏ qua, không có id để trả lỗi về đâu
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}
        try:
            result = await self.dispatch(method, params)
            return {"id": req_id, "result": result}
        except Exception as e:  # noqa: BLE001 — trả lỗi qua giao thức, không để lộ traceback thô
            return {"id": req_id, "error": {"message": str(e)}}

    async def _handle_conn(self, reader, writer):
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                resp = await self._handle_line(line)
                if resp is not None:
                    writer.write((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
                    await writer.drain()
        finally:
            writer.close()

    async def serve_forever(self):
        if self.sock_path.exists():
            self.sock_path.unlink()
        server = await asyncio.start_unix_server(self._handle_conn, path=str(self.sock_path))
        print(f"[librarian] listening on {self.sock_path}")
        async with server:
            await server.serve_forever()


def _real_server():
    from demo_agents.librarian_agent.agent import ingest_raw, search

    return LibrarianServer(search_fn=search, ingest_fn=ingest_raw)


def main():
    asyncio.run(_real_server().serve_forever())


if __name__ == "__main__":
    main()
