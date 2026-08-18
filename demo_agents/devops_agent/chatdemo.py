"""Chat demo — AGENT THẬT, không phải tool-lookup. Gọi Runner.run(agent, question, session=...) qua
_MCPBridge (xem bên dưới): LLM tự đọc câu hỏi tự nhiên, tự quyết định có gọi tool ask_librarian/
fetch (MCP) hay không, tự diễn giải kết quả theo INSTRUCTIONS — và NHỚ ngữ cảnh hội thoại giữa các
lượt nhờ SQLiteSession.

UI (`web/chat.html`) là COPY NGUYÊN VĂN từ demo_agents/weather_agent/web/chat.html (chỉ đổi nội
dung/branding, không đổi 1 token CSS nào) — dùng thẳng UI đã hoàn thiện/kiểm chứng thay vì viết lại
hay dùng trang built-in tối giản của monolith-agent-deploy-converter (tool đó dành cho ĐÓNG GÓI đem
đi triển khai, không phải cho test cục bộ có sẵn UI đầy đủ).

MCP: kết nối `mcp-server-fetch` (xem mcp_tools/README.md) CHỈ 1 LẦN lúc server khởi động (không phải
mỗi tin nhắn — tốn, chậm), theo đúng pattern "FastAPI lifespan" mà agents.mcp.MCPServerManager
khuyến nghị (docstring), chuyển sang http.server thuần bằng 1 event loop chạy nền suốt vòng đời
process (_MCPBridge) — mỗi request submit coroutine Runner.run qua run_coroutine_threadsafe, không
mở subprocess MCP mới mỗi lần hỏi. Nếu mcp-server-fetch không cài/không connect được, tự dùng lại
devops_agent KHÔNG có MCP (drop_failed_servers mặc định của MCPServerManager) — không crash server.

Khác weather_agent/chatdemo.py: KHÔNG có harness.py (chưa xây max_turns/retry riêng cho agent này)
nên tự bắt InputGuardrailTripwireTriggered ở đây, trả đúng OUT_OF_SCOPE_MESSAGE của devops_agent
thay vì để lộ exception thô. KHÔNG có /monitor /evaluate (chưa xây monitoring.py/dashboard.py cho
agent này — thêm khi được yêu cầu, giống cách các layer đó được thêm dần vào weather_agent).

/api/chat stream NDJSON (`_run_streamed` bên dưới) — RÚT GỌN của
weather_agent/harness.py::run_with_harness_streamed (agent này chưa có harness.py nên viết trực
tiếp ở đây), dùng CÙNG `Runner.run_streamed()` + event shape đã verify sống lúc build tính năng
này (xem wiki/log.md). Client (chat.html) đọc stream để hiện bubble trạng thái theo tool (đặc biệt
`ask_librarian`) + text chạy theo chunk thay vì chờ xong hẳn.

Cần DEEPSEEK_API_KEY hoặc OPENAI_API_KEY trong demo_agents/devops_agent/.env — xem .env.example.
Chạy: python3 -m demo_agents.devops_agent.chatdemo (YÊU CẦU Python 3.10+ — xem mcp_tools/README.md).

/wiki — trình duyệt wiki memory CỦA RIÊNG agent này (demo_agents/devops_agent/wiki/), khác wiki
cấp dự án (llmwiki/wiki/) — xem data_collector.py và wiki/log.md entry "wiki-per-agent-memory".
Dùng chung llmwiki.wiki_lib CHO PHẦN LOGIC, nhưng KHÔNG dùng PAGE_SHELL macOS-glass mặc định —
trang này cùng "khung" design.md đã khoá của chat.html (--bg/--panel/--accent=#326CE5 Kubernetes
blue, font-family, nav bar kiểu dashboard.py bên weather_agent), qua `shell=wiki_lib.CHAT_THEMED_SHELL`
+ `_WIKI_SHELL_VARS`.

CRUD thật (không chỉ view): /wiki/new (GET form + POST tạo), /wiki/edit/<rel> (GET form + POST
sửa), /wiki/delete/<rel> (POST xoá) — cùng cơ chế validate-trước-khi-ghi với weather_agent/
chatdemo.py (xem docstring ở đó), qua `wiki_lib.save_page` gọi CHÍNH llmwiki-validate.py.
"""
import asyncio
import dataclasses
import datetime
import json
import queue
import re
import sqlite3
import threading
import urllib.parse
import uuid
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from agents import Runner, SQLiteSession
from agents.exceptions import InputGuardrailTripwireTriggered, MaxTurnsExceeded
from agents.mcp import MCPServerManager
from openai.types.responses import ResponseTextDeltaEvent

from llmwiki import wiki_lib

from demo_agents.devops_agent.agent import build_agent_with_mcp, devops_agent
from demo_agents.devops_agent.dashboard import render_monitor_page
from demo_agents.devops_agent.guardrails import OUT_OF_SCOPE_MESSAGE, build_uncertain_hint, classify_scope
from demo_agents.devops_agent.memory import consolidate_if_due
from demo_agents.devops_agent.model_provider import has_any_key
from demo_agents.devops_agent.monitoring import log_event
from demo_agents.devops_agent.retrieval_gate import should_retrieve

# Tên tool TRA DỮ LIỆU ĐÃ THU THẬP — gate chỉ ẩn NHÓM NÀY khi retrieve=False, cùng quy ước
# weather_agent/harness.py::_RETRIEVAL_TOOL_NAMES. Chỉ còn ask_librarian — get_cheatsheet đã bị bỏ
# hẳn khỏi agent.py (user yêu cầu: chỉ librarian được quyền đọc wiki/cheatsheet, xem agent.py).
_RETRIEVAL_TOOL_NAMES = {"ask_librarian"}

HTML_PATH = Path(__file__).parent / "web" / "chat.html"
SESSIONS_DB = Path(__file__).parent / "chat_sessions.sqlite3"
WIKI_ROOT = Path(__file__).parent / "wiki"
WIKI_BRAND = "DevOps Agent Wiki"
WIKI_ACCENT_HEX = "326CE5"
# Cùng token hệ design.md đã khoá của chat.html — devops_agent KHÔNG có /monitor /evaluate (chưa
# xây dashboard.py riêng, xem docstring module) nên nav chỉ còn "← Chat" + "Wiki".
_WIKI_NAV = '<nav><a href="/">← Chat</a><a href="/monitor">Monitor</a><a class="active" href="/wiki">Wiki</a></nav>'
_WIKI_SHELL_VARS = dict(
    bg="#fbfefc", panel="#f5f5f7", text="#0d0d0d", dim="#6e6e80", border="#e5e5e5",
    accent="#326CE5", topbar=_WIKI_NAV,
)
WIKI_ICON = "⚙️"
PORT = 8768
TITLE_MAX_LEN = 48


class _MCPBridge:
    """1 event loop asyncio chạy NỀN, SUỐT VÒNG ĐỜI process — kết nối MCP server 1 LẦN lúc start()
    (không phải mỗi request), rồi expose `run(coro)` để handler đồng bộ (http.server thuần, không
    async) submit coroutine qua run_coroutine_threadsafe và block chờ kết quả. HTTPServer ở main()
    đơn luồng (không phải ThreadingHTTPServer) nên tại một thời điểm chỉ có 1 request gọi run() —
    không có rủi ro tranh chấp trên _manager.

    Cố ý ĐƠN GIẢN HOÁ: không có shutdown handler đóng MCP server sạch (cleanup_all()) khi process bị
    kill — subprocess mcp-server-fetch sẽ chết theo khi process cha thoát (không phải orphan thật
    sự nguy hiểm), chấp nhận đánh đổi cho 1 demo server, không phải production service."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.agent = devops_agent  # fallback tới khi connect() thành công (nếu có)
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
        """CÙNG pattern với demo_agents/weather_agent/chatdemo.py::_MCPBridge.stream — xem
        docstring ở đó cho giải thích đầy đủ (bắc cầu async generator chạy trên self.loop sang
        iterator đồng bộ ở thread xử lý HTTP request, qua queue.Queue thread-safe)."""
        q = queue.Queue()
        _SENTINEL = object()

        async def _pump():
            try:
                async for item in async_gen_factory():
                    q.put(item)
            except Exception as e:  # noqa: BLE001
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
        """CÙNG pattern weather_agent/chatdemo.py::_MCPBridge.fire_and_forget — xem docstring ở đó."""
        asyncio.run_coroutine_threadsafe(coro, self.loop)


_bridge = _MCPBridge()


@dataclass
class RunMeta:
    """CÙNG pattern weather_agent/harness.py::RunMeta — truyền qua Runner.run_streamed(context=...)
    để DevOpsAgentHooks (monitoring.py) đọc lại session_id/run_id, ghép đúng sự kiện của 1 lượt
    chat khi tính latency/xem trace."""

    session_id: str
    run_id: str


# CÙNG pattern weather_agent/harness.py::_is_greeting_only/_GREETING_REPLY — xem docstring ở đó
# (fast-path tối giản, regex tất định, KHÔNG gọi LLM, fail-open về full loop nếu không khớp rõ).
_GREETING_ONLY_RE = re.compile(
    r"^(xin\s+)?(chào|hi|hello|hey|cảm ơn|cám ơn|thanks|thank you|ok|oke|okay|được rồi|ừ|ừm)"
    r"[\s,.!?]*(bạn|nhé|nha|nhá)?[\s,.!?]*$",
    re.IGNORECASE,
)
_GREETING_REPLY = (
    "Chào bạn! Mình là DevOps Q&A agent — hỏi mình về Kubernetes, container, CI/CD, pattern triển "
    "khai, hay promote môi trường dev/uat/stage/prod nhé."
)


def _is_greeting_only(question):
    return bool(_GREETING_ONLY_RE.match(question.strip()))


async def _run_streamed(agent, question, session, session_id=None):
    """Bản RÚT GỌN của weather_agent/harness.py::run_with_harness_streamed (đọc docstring ở đó cho
    giải thích đầy đủ event shape/cạnh khó) — devops_agent chưa có harness.py riêng (chưa xây
    max_turns/retry, xem docstring module) nên không có bước retry/capability-shortcut.

    Phạm vi 3 mức (guardrails.py::classify_scope, xem docstring ở đó + weather_agent/harness.py cho
    lý do đầy đủ đổi từ @input_guardrail nhị phân sang phân loại thủ công 3 mức) chạy TRƯỚC retrieval
    gate: OUT_OF_SCOPE tự tin → chặn cứng ngay (trả OUT_OF_SCOPE_MESSAGE), UNCERTAIN → không chặn,
    chỉ nối hint vào instructions của bản sao agent. `except InputGuardrailTripwireTriggered` bên
    dưới giữ lại làm lớp dự phòng (guardrail vẫn gắn trên `agent`, xem agent.py) — hiếm khi trip khi
    đã qua bước phân loại thủ công này.

    Ghi `tool_call`/`tool_result` (tên tool + args ĐẦY ĐỦ + số iteration) vào monitoring.sqlite3 qua
    `log_event` — cùng "loop transparency" đã thêm ở weather_agent/harness.py, xem wiki/log.md.

    Retrieval gate (retrieval_gate.py) chạy SAU — nếu KHÔNG cần tra wiki/cheatsheet, ẩn HẲN
    ask_librarian (TOOL DUY NHẤT đọc wiki, xem agent.py) khỏi agent cho lượt này (dựng bản sao qua
    dataclasses.replace, agent gốc KHÔNG đổi) — cùng cơ chế đã thêm ở weather_agent/harness.py."""
    run_id = uuid.uuid4().hex[:12]
    meta = RunMeta(session_id=session_id or "", run_id=run_id)
    if _is_greeting_only(question):
        log_event(agent.name, "harness_greeting_shortcut", session_id=session_id, run_id=run_id)
        yield ("done", _GREETING_REPLY)
        return
    scope = await classify_scope(question, context=meta)
    log_event(
        agent.name, "scope_check", {"verdict": scope.verdict, "reason": scope.reason}, session_id, run_id
    )
    if scope.verdict == "out_of_scope":
        log_event(agent.name, "harness_guardrail_tripped", session_id=session_id, run_id=run_id)
        yield ("done", OUT_OF_SCOPE_MESSAGE)
        return
    run_agent = agent
    if scope.verdict == "uncertain":
        run_agent = dataclasses.replace(agent, instructions=agent.instructions + build_uncertain_hint(scope.reason))
    retrieve, gate_reason = await should_retrieve(question)
    log_event(agent.name, "retrieval_gate", {"retrieve": retrieve, "reason": gate_reason}, session_id, run_id)
    if not retrieve:
        filtered_tools = [t for t in run_agent.tools if getattr(t, "name", None) not in _RETRIEVAL_TOOL_NAMES]
        run_agent = dataclasses.replace(run_agent, tools=filtered_tools)
    iteration = 0
    try:
        result = Runner.run_streamed(run_agent, question, context=meta, session=session)
        async for event in result.stream_events():
            if event.type == "run_item_stream_event" and event.name == "tool_called":
                raw_item = getattr(getattr(event, "item", None), "raw_item", None)
                name = getattr(raw_item, "name", None)
                if name:
                    iteration += 1
                    args = getattr(raw_item, "arguments", None)
                    log_event(
                        agent.name, "tool_call",
                        {"tool": name, "args": args, "iteration": iteration},
                        session_id, run_id,
                    )
                    yield ("tool_start", name)
            elif event.type == "run_item_stream_event" and event.name == "tool_output":
                output = getattr(getattr(event, "item", None), "output", None)
                log_event(
                    agent.name, "tool_result",
                    {"output": str(output)[:500] if output is not None else None, "iteration": iteration},
                    session_id, run_id,
                )
            elif event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                yield ("text_delta", event.data.delta)
        yield ("done", result.final_output)
    except InputGuardrailTripwireTriggered:
        log_event(agent.name, "harness_guardrail_tripped", session_id=session_id, run_id=run_id)
        yield ("done", OUT_OF_SCOPE_MESSAGE)


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
            # no-store — file này sửa liên tục lúc dev (CSS/JS demo tự chứa trong 1 file), không có
            # cơ chế bust cache nào khác (không hash filename) — thiếu header này, browser có thể
            # phục vụ bản HTML cũ từ cache dù server luôn đọc file MỚI NHẤT từ đĩa mỗi request (đã
            # xác nhận thật: user report UI "vẫn lệch" nhiều lượt liên tiếp sau khi đã fix, khả năng
            # cao do tab cũ/cache, không phải code sai).
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
                lambda: _run_streamed(_bridge.agent, question, session, session_id=session_id)
            ):
                self._write_line({"type": kind, "value": payload})
            _bridge.fire_and_forget(consolidate_if_due(session, session_id))
        except MaxTurnsExceeded:
            self._write_line({
                "type": "error",
                "message": "Agent lặp quá nhiều bước cho câu hỏi này — thử hỏi ngắn gọn/cụ thể hơn.",
            })
        except Exception as e:  # lỗi gọi model thật (mạng, key sai, quota...)
            self._write_line({"type": "error", "message": f"Lỗi gọi model: {e}"})

    def _start_ndjson_stream(self):
        """CÙNG pattern weather_agent/chatdemo.py::_start_ndjson_stream — xem docstring ở đó."""
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
    print(f"DevOps agent CHAT demo (LLM thật, nhớ hội thoại, danh sách session) — http://127.0.0.1:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
