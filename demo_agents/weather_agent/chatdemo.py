"""Chat demo — AGENT THẬT, không phải tool-lookup. Gọi run_with_harness(weather_agent, question,
session=...) qua _MCPBridge (xem bên dưới): LLM (DeepSeek hoặc gpt-4o-mini, xem model_provider.py)
tự đọc câu hỏi tự nhiên, tự quyết định có gọi tool get_weather/fetch (MCP) hay không, tự diễn giải
kết quả theo INSTRUCTIONS — và NHỚ ngữ cảnh hội thoại giữa các lượt nhờ SQLiteSession (agent SDK có
sẵn, không tự chế cơ chế nhớ).

Có DANH SÁCH nhiều cuộc trò chuyện (như ChatGPT): SQLiteSession tự tạo 2 bảng
(agent_sessions, agent_messages) — /api/sessions liệt kê trực tiếp từ agent_sessions (tiêu đề lấy
từ tin nhắn user đầu tiên), /api/history nạp lại toàn bộ hội thoại của 1 session để hiển thị lại
sau khi reload trang hoặc chuyển qua lại giữa các cuộc trò chuyện.

MCP: kết nối `mcp-server-fetch` (xem mcp_tools/README.md) CHỈ 1 LẦN lúc server khởi động qua
_MCPBridge — cùng pattern với demo_agents/devops_agent/chatdemo.py, không viết logic riêng.
`run_with_harness` (harness.py) đã đổi sang `async def` để chạy ĐÚNG trên event loop đã connect MCP
server (Runner.run_sync tự tạo loop riêng, sẽ vỡ kết nối MCP nếu gọi lồng bên trong loop khác).

Cần DEEPSEEK_API_KEY hoặc OPENAI_API_KEY trong demo_agents/weather_agent/.env — xem .env.example.
Chạy: python3 -m demo_agents.weather_agent.chatdemo (YÊU CẦU Python 3.10+ — xem mcp_tools/README.md).

/monitor — dashboard phân tích monitoring.sqlite3 (tổng lượt hỏi, guardrail chặn bao nhiêu lần,
tool nào dùng nhiều, 50 sự kiện gần nhất) + tóm tắt eval. /evaluate — chi tiết từng golden trong
harness/metrics/eval-baseline.json. Xem dashboard.py.

/wiki — trình duyệt wiki memory CỦA RIÊNG agent này (demo_agents/weather_agent/wiki/), khác wiki
cấp dự án (llmwiki/wiki/) — xem data_collector.py và wiki/log.md entry "wiki-per-agent-memory".
Dùng chung llmwiki.wiki_lib CHO PHẦN LOGIC (frontmatter/markdown/wikilink), nhưng KHÔNG dùng
PAGE_SHELL macOS-glass mặc định của nó — trang này phải cùng "khung" design.md đã khoá của
chat.html (--bg/--panel/--accent=#10a37f, font-family, nav bar kiểu dashboard.py), không phải 1
theme rời rạc, nên truyền `shell=wiki_lib.CHAT_THEMED_SHELL` + token riêng qua `_WIKI_SHELL_VARS`.

CRUD thật (không chỉ view): /wiki/new (GET form + POST tạo), /wiki/edit/<rel> (GET form + POST
sửa), /wiki/delete/<rel> (POST xoá). Mọi lần ghi đĩa đều chạy NGAY qua `wiki_lib.save_page` —
validate bằng CHÍNH llmwiki-validate.py (cùng lõi gác cổng Claude Code hook dùng, xem
harness/poc-vendor-neutral/policy.yaml R2/R5/R9) TRƯỚC khi coi là thành công, sai thì rollback +
báo lỗi ngay trên form, không để lại file rác trên đĩa.
"""
import asyncio
import datetime
import json
import queue
import sqlite3
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from agents import SQLiteSession
from agents.exceptions import MaxTurnsExceeded
from agents.mcp import MCPServerManager

from llmwiki import wiki_lib

from demo_agents.weather_agent.agent import build_agent_with_mcp, weather_agent
from demo_agents.weather_agent.dashboard import render_evaluate_page, render_monitor_page
from demo_agents.weather_agent.harness import run_with_harness, run_with_harness_streamed
from demo_agents.weather_agent.memory import consolidate_if_due
from demo_agents.weather_agent.model_provider import has_any_key

HTML_PATH = Path(__file__).parent / "web" / "chat.html"
SESSIONS_DB = Path(__file__).parent / "chat_sessions.sqlite3"
WIKI_ROOT = Path(__file__).parent / "wiki"
WIKI_BRAND = "Weather Agent Wiki"
WIKI_ACCENT_HEX = "10a37f"
# Cùng token hệ design.md đã khoá của chat.html (:root { --sidebar-bg/--main-bg/--accent... }) —
# xem web/chat.html — để /wiki đọc như 1 view khác của CÙNG app, không phải trang rời rạc.
_WIKI_NAV = (
    '<nav><a href="/">← Chat</a><a href="/monitor">Monitor</a>'
    '<a href="/evaluate">Evaluate</a><a class="active" href="/wiki">Wiki</a></nav>'
)
_WIKI_SHELL_VARS = dict(
    bg="#fbfefc", panel="#f5f5f7", text="#0d0d0d", dim="#6e6e80", border="#e5e5e5",
    accent="#10a37f", topbar=_WIKI_NAV,
)
WIKI_ICON = "🌦️"
PORT = 8767
TITLE_MAX_LEN = 48


class _MCPBridge:
    """Cùng pattern với demo_agents/devops_agent/chatdemo.py::_MCPBridge — xem docstring ở đó cho
    giải thích đầy đủ (1 event loop nền suốt vòng đời process, connect MCP 1 lần lúc start())."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.agent = weather_agent
        self._manager = None
        self._thread = threading.Thread(target=self._run_loop, daemon=True)

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def start(self):
        self._thread.start()
        asyncio.run_coroutine_threadsafe(self._connect(), self.loop).result(timeout=30)

    async def _connect(self):
        from mcp_tools.exa_server import build_exa_mcp_server
        from mcp_tools.fetch_server import build_fetch_mcp_server

        servers = [build_fetch_mcp_server(), build_exa_mcp_server()]
        self._manager = MCPServerManager(servers)
        await self._manager.connect_all()
        if self._manager.active_servers:
            self.agent = build_agent_with_mcp(self._manager.active_servers)
            print(f"[MCP] Đã kết nối: {[s.name for s in self._manager.active_servers]}")
        else:
            print("[MCP] Không kết nối được server nào — chạy KHÔNG có tool fetch/search "
                  "(xem mcp_tools/README.md để cài).")

    def run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()

    def stream(self, async_gen_factory):
        """Bắc cầu 1 async generator (chạy TRÊN self.loop — event loop nền đã connect MCP) sang
        1 iterator ĐỒNG BỘ (đọc từ thread xử lý HTTP request) — dùng cho streaming chat, khác `run`
        (chặn tới khi coroutine xong hẳn). Sản xuất trên loop nền qua `_pump`, đẩy từng item vào
        `queue.Queue` thread-safe, tiêu thụ bằng vòng lặp `while` chặn ở thread gọi — KHÔNG chặn
        loop nền (put() không await), KHÔNG cần đổi kiến trúc _MCPBridge hiện có."""
        q = queue.Queue()
        _SENTINEL = object()

        async def _pump():
            try:
                async for item in async_gen_factory():
                    q.put(item)
            except Exception as e:  # noqa: BLE001 — đẩy lỗi qua hàng đợi để raise lại ở thread gọi
                q.put(("__error__", e))
            finally:
                q.put(_SENTINEL)

        asyncio.run_coroutine_threadsafe(_pump(), self.loop)
        while True:
            item = q.get()
            if item is _SENTINEL:
                return
            if isinstance(item, tuple) and len(item) == 2 and item[0] == "__error__":
                raise item[1]
            yield item

    def fire_and_forget(self, coro):
        """Submit `coro` lên loop nền, KHÔNG chờ kết quả (khác `run`/`stream` đều block tới khi
        xong) — dùng cho việc phụ không ảnh hưởng response ĐÃ GỬI XONG (vd consolidation, xem
        memory.py::consolidate_if_due), để HTTPServer đơn luồng không phải chờ nó chạy xong mới
        nhận request kế tiếp. Lỗi bên trong `coro` PHẢI tự nuốt (không raise ra ngoài) — không ai
        đọc kết quả Future này cả."""
        asyncio.run_coroutine_threadsafe(coro, self.loop)


_bridge = _MCPBridge()


def _wiki_values_from_form(form):
    return {
        "type": form.get("type", "source"),
        "title": form.get("title", "").strip(),
        "tags": form.get("tags", ""),
        "aliases": form.get("aliases", ""),
        "body": form.get("body", ""),
    }


def _extract_transcript(items):
    """Rút gọn output thô của SQLiteSession.get_items() thành list {role, text} hiển thị được —
    bỏ qua function_call/function_call_output (lời gọi tool nội bộ), chỉ giữ lời thoại thấy được."""
    messages = []
    for it in items:
        role = it.get("role")
        if role == "user" and isinstance(it.get("content"), str):
            messages.append({"role": "user", "text": it["content"]})
        elif role == "assistant" and it.get("type") == "message":
            parts = [
                c.get("text", "")
                for c in (it.get("content") or [])
                if isinstance(c, dict) and c.get("type") == "output_text"
            ]
            text = "".join(parts)
            if text:
                messages.append({"role": "assistant", "text": text})
    return messages


def _list_sessions():
    if not SESSIONS_DB.is_file():
        return []
    con = sqlite3.connect(str(SESSIONS_DB))
    try:
        cur = con.cursor()
        cur.execute("SELECT session_id, updated_at FROM agent_sessions ORDER BY updated_at DESC")
        rows = cur.fetchall()
        sessions = []
        for sid, updated_at in rows:
            cur.execute(
                "SELECT message_data FROM agent_messages WHERE session_id=? ORDER BY id ASC LIMIT 3",
                (sid,),
            )
            title = sid
            for (raw,) in cur.fetchall():
                try:
                    item = json.loads(raw)
                except (TypeError, json.JSONDecodeError):
                    continue
                if item.get("role") == "user" and isinstance(item.get("content"), str):
                    text = item["content"].strip()
                    title = (text[:TITLE_MAX_LEN] + "…") if len(text) > TITLE_MAX_LEN else text
                    break
            sessions.append({"session_id": sid, "title": title, "updated_at": updated_at})
        return sessions
    finally:
        con.close()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path in ("/", "/chat.html"):
            body = HTML_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            # no-store — CÙNG lý do đã thêm ở devops_agent/chatdemo.py::do_GET, xem comment ở đó.
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == "/api/sessions":
            self._reply({"sessions": _list_sessions()})
        elif parsed.path == "/api/history":
            qs = urllib.parse.parse_qs(parsed.query)
            session_id = (qs.get("session_id") or [""])[0].strip()
            self._handle_history(session_id)
        elif parsed.path == "/monitor":
            self._reply_html(render_monitor_page())
        elif parsed.path == "/evaluate":
            self._reply_html(render_evaluate_page())
        elif parsed.path == "/wiki":
            self._reply_html(wiki_lib.render_index_page(
                WIKI_ROOT, WIKI_BRAND, "/wiki", WIKI_ACCENT_HEX, WIKI_ICON,
                shell=wiki_lib.CHAT_THEMED_SHELL, crud=True, **_WIKI_SHELL_VARS,
            ))
        elif parsed.path == "/wiki/new":
            self._handle_wiki_new_get()
        elif parsed.path.startswith("/wiki/edit/"):
            self._handle_wiki_edit_get(parsed.path[len("/wiki/edit/"):])
        elif parsed.path.startswith("/wiki/"):
            self._handle_wiki_page(parsed.path[len("/wiki/"):])
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_wiki_page(self, rel):
        target = wiki_lib.resolve_safe_path(WIKI_ROOT, rel)
        if target is None:
            self.send_response(403)
            self.end_headers()
            return
        status, body = wiki_lib.render_wiki_page(
            WIKI_ROOT, rel, WIKI_BRAND, "/wiki", WIKI_ACCENT_HEX, WIKI_ICON,
            shell=wiki_lib.CHAT_THEMED_SHELL, crud=True, **_WIKI_SHELL_VARS,
        )
        self._reply_html(body, status)

    def _handle_wiki_new_get(self):
        body = wiki_lib.render_form_page(
            "new", WIKI_ROOT, WIKI_BRAND, "/wiki", WIKI_ACCENT_HEX, WIKI_ICON,
            shell=wiki_lib.CHAT_THEMED_SHELL, **_WIKI_SHELL_VARS,
        )
        self._reply_html(body)

    def _handle_wiki_edit_get(self, rel):
        if wiki_lib.resolve_safe_path(WIKI_ROOT, rel) is None:
            self.send_response(403)
            self.end_headers()
            return
        values = wiki_lib.load_page_values(WIKI_ROOT, rel)
        if values is None:
            self.send_response(404)
            self.end_headers()
            return
        body = wiki_lib.render_form_page(
            "edit", WIKI_ROOT, WIKI_BRAND, "/wiki", WIKI_ACCENT_HEX, WIKI_ICON,
            shell=wiki_lib.CHAT_THEMED_SHELL, rel=rel, values=values, **_WIKI_SHELL_VARS,
        )
        self._reply_html(body)

    def _wiki_form_error(self, mode, rel, values, error):
        body = wiki_lib.render_form_page(
            mode, WIKI_ROOT, WIKI_BRAND, "/wiki", WIKI_ACCENT_HEX, WIKI_ICON,
            shell=wiki_lib.CHAT_THEMED_SHELL, rel=rel, error=error, values=values, **_WIKI_SHELL_VARS,
        )
        self._reply_html(body, 400)

    def _handle_wiki_new_post(self):
        form = self._read_form()
        values = _wiki_values_from_form(form)
        if not values["title"]:
            return self._wiki_form_error("new", None, values, "Tiêu đề không được để trống.")
        slug = wiki_lib.slugify(values["title"])
        rel = f"sources/{slug}.md"
        if (WIKI_ROOT / rel).is_file():
            return self._wiki_form_error("new", None, values, f"Trang 'sources/{slug}.md' đã tồn tại — sửa tên hoặc vào trang đó để edit.")
        meta = {
            "type": values["type"], "title": values["title"],
            "tags": wiki_lib.split_csv(values["tags"]),
            "aliases": wiki_lib.split_csv(values["aliases"]),
            "timestamp": datetime.date.today().isoformat(),
        }
        content = wiki_lib.compose_page(meta, values["body"], "Tạo qua /wiki UI.")
        ok, err = wiki_lib.save_page(WIKI_ROOT, rel, content)
        if not ok:
            return self._wiki_form_error("new", None, values, err)
        self._redirect(f"/wiki/{rel}")

    def _handle_wiki_edit_post(self, rel):
        target = wiki_lib.resolve_safe_path(WIKI_ROOT, rel)
        if target is None or not target.is_file():
            self.send_response(404)
            self.end_headers()
            return
        form = self._read_form()
        values = _wiki_values_from_form(form)
        if not values["title"]:
            return self._wiki_form_error("edit", rel, values, "Tiêu đề không được để trống.")
        original_meta, _ = wiki_lib.parse_frontmatter(target.read_text(encoding="utf-8"))
        meta = {
            "type": values["type"], "title": values["title"],
            "tags": wiki_lib.split_csv(values["tags"]),
            "aliases": wiki_lib.split_csv(values["aliases"]),
            "timestamp": original_meta.get("timestamp") or datetime.date.today().isoformat(),
        }
        content = wiki_lib.compose_page(meta, values["body"], "Sửa qua /wiki UI.")
        ok, err = wiki_lib.save_page(WIKI_ROOT, rel, content)
        if not ok:
            return self._wiki_form_error("edit", rel, values, err)
        self._redirect(f"/wiki/{rel}")

    def _handle_wiki_delete_post(self, rel):
        wiki_lib.delete_page(WIKI_ROOT, rel)
        self._redirect("/wiki")

    def _redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def _read_form(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        parsed = urllib.parse.parse_qs(raw.decode("utf-8"))
        return {k: v[0] for k, v in parsed.items()}

    def _reply_html(self, html_str, status=200):
        body = html_str.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return {}

    def _reply(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_history(self, session_id):
        if not session_id:
            return self._reply({"error": "thiếu session_id"}, 400)
        session = SQLiteSession(session_id, db_path=str(SESSIONS_DB))
        items = _bridge.run(session.get_items())
        self._reply({"messages": _extract_transcript(items)})

    def do_POST(self):
        if self.path == "/api/chat":
            return self._handle_chat()
        if self.path == "/api/reset":
            return self._handle_reset()
        if self.path == "/wiki/new":
            return self._handle_wiki_new_post()
        if self.path.startswith("/wiki/edit/"):
            return self._handle_wiki_edit_post(self.path[len("/wiki/edit/"):])
        if self.path.startswith("/wiki/delete/"):
            return self._handle_wiki_delete_post(self.path[len("/wiki/delete/"):])
        self.send_response(404)
        self.end_headers()

    def _handle_chat(self):
        data = self._read_json()
        question = str(data.get("question", "")).strip()
        session_id = str(data.get("session_id", "")).strip()
        if not question:
            return self._reply({"error": "câu hỏi trống"}, 400)
        if not session_id:
            return self._reply({"error": "thiếu session_id"}, 400)
        if not has_any_key():
            return self._reply(
                {"error": "thiếu DEEPSEEK_API_KEY / OPENAI_API_KEY — xem .env.example"}, 400
            )
        session = SQLiteSession(session_id, db_path=str(SESSIONS_DB))
        self._start_ndjson_stream()
        try:
            for kind, payload in _bridge.stream(
                lambda: run_with_harness_streamed(
                    _bridge.agent, question, session=session, session_id=session_id
                )
            ):
                self._write_line({"type": kind, "value": payload})
            # Consolidation (memory.py) — FIRE-AND-FORGET SAU KHI response đã gửi xong, không chặn
            # request kế tiếp (HTTPServer đơn luồng) chờ 1 lượt gọi model tóm tắt phụ.
            _bridge.fire_and_forget(consolidate_if_due(session, session_id))
        except MaxTurnsExceeded:
            self._write_line({
                "type": "error",
                "message": "Agent lặp quá nhiều bước cho câu hỏi này — thử hỏi ngắn gọn/cụ thể hơn.",
            })
        except Exception as e:  # lỗi gọi model thật (mạng, key sai, quota...)
            self._write_line({"type": "error", "message": f"Lỗi gọi model: {e}"})

    def _start_ndjson_stream(self):
        """Header response 1 LẦN, KHÔNG gửi Content-Length (chưa biết trước độ dài — đang stream) —
        `close_connection=True` để client (fetch().body.getReader()) đọc tới khi kết nối đóng, cách
        hoạt động cơ bản của HTTP/1.1 khi không có Content-Length/chunked encoding thật."""
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.close_connection = True
        self.end_headers()

    def _write_line(self, payload):
        try:
            self.wfile.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass  # client đóng tab giữa chừng — không phải lỗi cần báo

    def _handle_reset(self):
        data = self._read_json()
        session_id = str(data.get("session_id", "")).strip()
        if not session_id:
            return self._reply({"error": "thiếu session_id"}, 400)
        session = SQLiteSession(session_id, db_path=str(SESSIONS_DB))
        _bridge.run(session.clear_session())
        self._reply({"ok": True})


def main():
    _bridge.start()
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Weather agent CHAT demo (LLM thật, nhớ hội thoại, danh sách session) — http://127.0.0.1:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
