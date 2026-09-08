#!/usr/bin/env python3
"""monolith-agent-deploy-converter — bỏ 1 folder src (agent viết theo quy ước `agent_spec.py`, xem
demo_agents/weather_agent/agent_spec.py + wiki/concepts/agent-portability.md) vào tool này, xuất ra
1 app chat agentic STANDALONE, bốc đi triển khai bất kỳ đâu (Docker image, hoặc bundle Python thuần
không cần Docker).

QUY ƯỚC INPUT (xác nhận qua AskUserQuestion — dựa trên AgentSpec đã xây, không đoán cấu trúc code
tự do): `<src>/agent_spec.py` phải có ĐÚNG 1 hàm tên khớp `build_*_agent_spec` (không tham số bắt
buộc), gọi ra trả về 1 `agent_spec.AgentSpec`. Tool KHÔNG tự suy luận tools/instructions từ code
theo cách nào khác — không tìm thấy hàm này thì fail loud, không đoán mò.

CÁCH "CHUYỂN ĐỔI" KHÔNG VIẾT LẠI IMPORT: thay vì rewrite source (dễ vỡ), bundle giữ NGUYÊN cấu trúc
package gốc (vd `demo_agents/weather_agent/*.py` bên trong thư mục xuất) — mọi `from
demo_agents.weather_agent import X` trong code gốc vẫn resolve đúng, chỉ cần thêm
`sys.path.insert(0, <bundle_root>)` ở entrypoint mới (`standalone_server.py`) sinh ra ở NGOÀI
package đó. Xem --package nếu path suy ra tự động từ --src sai.

Target hỗ trợ (chọn 1 hoặc cả 2, KHÔNG mặc định — người dùng phải chọn tường minh):
  --target python  : bundle chạy trực tiếp bằng `python3 standalone_server.py` (cần pip install
                     requirements.txt, cần Python đúng phiên bản trên máy đích).
  --target docker  : bundle Python (như trên) + Dockerfile — build/run bằng Docker, không cần cài
                     Python trên máy đích. Tool này CHỈ SINH Dockerfile, KHÔNG tự chạy `docker
                     build` (sandbox phát triển công cụ này không có Docker — không giả vờ đã build
                     thành công khi chưa từng chạy qua Docker thật).
  --target both    : sinh cả 2 vào cùng 1 thư mục output.

Ví dụ:
  python3 harness/scripts/monolith_agent_deploy_converter.py \\
    --src demo_agents/weather_agent --out dist/weather-agent-standalone --target both
"""

import argparse
import importlib.util
import shutil
import sys
from pathlib import Path

_EXCLUDE_NAMES = {"__pycache__", ".env", ".pytest_cache"}
_EXCLUDE_MARKERS = (".sqlite3",)  # bắt cả *.sqlite3-wal/*.sqlite3-shm, không chỉ khớp đuôi chính xác
_EXCLUDE_PREFIXES = ("test_",)

_STANDALONE_SERVER_TEMPLATE = '''"""Standalone entrypoint — sinh tự động bởi monolith-agent-deploy-converter, KHÔNG sửa tay (sửa
agent_spec.py ở package gốc rồi chạy lại converter). Bọc package gốc "{package}" thành 1 app chat
đơn giản, tự chứa: đọc AgentSpec qua "{spec_func}", xuất qua openai_agents_exporter, phục vụ chat UI
(web/chat.html của package nếu có, else trang chat tối giản built-in) + /api/chat.

MCP_TOOL_NAMES = {mcp_tool_names!r} — nếu không rỗng, bundle này có kèm mcp_tools/ (xem
mcp_tools/README.md TRONG BUNDLE để cài servers-venv/ — KHÔNG bundle sẵn venv, machine-specific).
_MCPBridge kết nối 1 LẦN lúc start() (không phải mỗi request) — nếu không kết nối được (chưa chạy
bước setup), agent vẫn chạy KHÔNG có MCP, không crash server.
"""
import asyncio
import json
import os
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents import Runner, SQLiteSession  # noqa: E402
from agents.exceptions import InputGuardrailTripwireTriggered, MaxTurnsExceeded  # noqa: E402

from {package} import agent_spec as _agent_spec_module  # noqa: E402
from {package}.exporters.openai_agents_exporter import build_openai_agent  # noqa: E402

PORT = int(os.environ.get("PORT", "{port}"))
SESSIONS_DB = Path(__file__).parent / "standalone_sessions.sqlite3"
CHAT_HTML = Path(__file__).parent / "{package_path}" / "web" / "chat.html"
MCP_TOOL_NAMES = {mcp_tool_names!r}

_GENERIC_CHAT_HTML = r"""<!doctype html><html><head><meta charset="utf-8">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='{accent_color_urlenc}'/%3E%3C/svg%3E">
<title>{agent_name}</title></head><body style="font-family:-apple-system,sans-serif;max-width:640px;
margin:40px auto;padding:0 16px;line-height:1.6">
<h1 style="color:{accent_color}">{agent_name}</h1>
<style>
  #log table{{border-collapse:collapse;margin:8px 0;font-size:13.5px;width:100%}}
  #log th,#log td{{border:1px solid #ddd;padding:6px 10px;text-align:left;vertical-align:top}}
  #log th{{background:#f4f4f4;font-weight:700}}
  #log code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;
    background:#f4f4f4;border-radius:4px;padding:1px 5px}}
</style>
<div id="log" style="border:1px solid #ddd;border-radius:8px;padding:12px;
min-height:200px;margin-bottom:12px"></div>
<form id="f" style="display:flex;gap:8px">
  <input id="q" style="flex:1;padding:8px;border:1px solid #ddd;border-radius:6px" placeholder="Hỏi..." autofocus>
  <button type="submit" style="background:{accent_color};color:#fff;border:none;border-radius:6px;padding:8px 16px;cursor:pointer">Gửi</button>
</form>
<script>
const sid = crypto.randomUUID();
const log = document.getElementById('log');
// Markdown-lite RÚT GỌN từ demo_agents/*/web/chat.html::renderMarkdownLite (bugfix bảng markdown
// hiện nguyên văn ký tự "|" — Design Feedback thật 10/08/2026, xem wiki/log.md) — port sang trang
// fallback built-in này (dùng khi package KHÔNG có web/chat.html riêng) để agent xuất qua converter
// không lặp lại lỗi tương tự. Chỉ giữ bảng/bold/code/list — đủ cho fallback tối giản, không cần đủ
// heading/blockquote như bản đầy đủ.
function escapeHtml(s) {{ return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }}
function renderInline(s) {{
  s = s.replace(/`([^`]+?)`/g, '<code>$1</code>');
  return s.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
}}
function renderMarkdownLite(s) {{
  const lines = escapeHtml(s).split('\\n');
  const out = [];
  function splitRow(l) {{ return l.trim().replace(/^\\|/, '').replace(/\\|$/, '').split('|').map(c => c.trim()); }}
  function isSep(l) {{
    if (!l || l.indexOf('|') === -1) return false;
    const c = splitRow(l);
    return c.length > 0 && c.every(x => /^:?-+:?$/.test(x));
  }}
  let i = 0;
  while (i < lines.length) {{
    const line = lines[i];
    if (line.indexOf('|') !== -1 && i + 1 < lines.length && isSep(lines[i + 1])) {{
      const head = splitRow(line);
      out.push('<table><thead><tr>' + head.map(c => '<th>' + renderInline(c) + '</th>').join('') + '</tr></thead><tbody>');
      i += 2;
      while (i < lines.length && lines[i].indexOf('|') !== -1 && lines[i].trim() !== '') {{
        out.push('<tr>' + splitRow(lines[i]).map(c => '<td>' + renderInline(c) + '</td>').join('') + '</tr>');
        i++;
      }}
      out.push('</tbody></table>');
      continue;
    }}
    const ul = line.match(/^[-*]\\s+(.*)$/);
    if (ul) {{ out.push('&bull; ' + renderInline(ul[1]) + '<br>'); }}
    else if (line.trim() === '') {{ out.push('<br>'); }}
    else {{ out.push(renderInline(line) + '<br>'); }}
    i++;
  }}
  return out.join('');
}}
document.getElementById('f').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const q = document.getElementById('q');
  const question = q.value.trim();
  if (!question) return;
  log.innerHTML += '<div style="margin:10px 0"><strong>Bạn:</strong> ' + escapeHtml(question) + '</div>';
  q.value = '';
  const res = await fetch('/api/chat', {{method:'POST', headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify({{question, session_id: sid}})}});
  const data = await res.json();
  log.innerHTML += '<div style="margin:10px 0">' + renderMarkdownLite(data.answer || data.error || '(lỗi)') + '</div>';
}});
</script></body></html>"""


def _get_model():
    try:
        from {package} import model_provider  # type: ignore

        return model_provider.get_model()
    except ImportError:
        pass
    if os.environ.get("DEEPSEEK_API_KEY"):
        from agents import AsyncOpenAI, OpenAIChatCompletionsModel

        client = AsyncOpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
        return OpenAIChatCompletionsModel(model="deepseek-chat", openai_client=client)
    if os.environ.get("OPENAI_API_KEY"):
        return "gpt-4o-mini"
    return None


_spec = _agent_spec_module.{spec_func}()


class _MCPBridge:
    """1 event loop asyncio chạy NỀN suốt vòng đời process — connect các MCP tool khai báo trong
    AgentSpec.mcp_tool_names 1 LẦN lúc start() (không phải mỗi request), theo pattern "FastAPI
    lifespan" mà agents.mcp.MCPServerManager khuyến nghị, chuyển sang http.server thuần bằng thread
    nền (xem demo_agents/*/chatdemo.py::_MCPBridge — cùng pattern, sinh ra ở đây cho bundle độc
    lập). Không kết nối được (thiếu servers-venv/, xem mcp_tools/README.md) → agent chạy KHÔNG có
    MCP, không crash server (drop_failed_servers mặc định của MCPServerManager).

    Cố ý ĐƠN GIẢN HOÁ: không cleanup MCP server khi process bị kill — chấp nhận cho demo/standalone
    bundle, không phải production service (subprocess con chết theo khi process cha thoát)."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.agent = build_openai_agent(_spec, model=_get_model())
        self._thread = threading.Thread(target=self._run_loop, daemon=True)

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def start(self):
        self._thread.start()
        if MCP_TOOL_NAMES:
            asyncio.run_coroutine_threadsafe(self._connect(), self.loop).result(timeout=30)

    async def _connect(self):
        try:
            import importlib

            from agents.mcp import MCPServerManager

            servers = []
            for name in MCP_TOOL_NAMES:
                mod = importlib.import_module(f"mcp_tools.{{name}}")
                servers.append(mod.build_mcp_server())
            manager = MCPServerManager(servers)
            await manager.connect_all()
            if manager.active_servers:
                self.agent = build_openai_agent(
                    _spec, model=_get_model(), mcp_servers=manager.active_servers
                )
                print(f"[MCP] Đã kết nối: {{[s.name for s in manager.active_servers]}}")
            else:
                print("[MCP] Không kết nối được — chạy KHÔNG có MCP (xem mcp_tools/README.md).")
        except Exception as e:  # noqa: BLE001 — optional dependency, không crash server vì thiếu nó
            print(f"[MCP] Lỗi setup ({{e}}) — chạy KHÔNG có MCP.")

    def run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()


_bridge = _MCPBridge()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path in ("/", "/chat.html"):
            body = CHAT_HTML.read_bytes() if CHAT_HTML.is_file() else _GENERIC_CHAT_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length) or b"{{}}")
        except json.JSONDecodeError:
            data = {{}}
        question = str(data.get("question", "")).strip()
        session_id = str(data.get("session_id") or uuid.uuid4().hex)
        if not question:
            return self._reply({{"error": "câu hỏi trống"}}, 400)
        try:
            session = SQLiteSession(session_id, db_path=str(SESSIONS_DB))
            result = _bridge.run(Runner.run(_bridge.agent, question, session=session))
            self._reply({{"answer": result.final_output}})
        except InputGuardrailTripwireTriggered:
            # KHÔNG để lộ chuỗi exception thô ("Guardrail InputGuardrail triggered tripwire") ra
            # người dùng cuối — bản gốc (weather_agent/harness.py) có OUT_OF_SCOPE_MESSAGE riêng
            # cho từng agent cụ thể; bản generic này chỉ biết agent CÓ guardrail, không biết nội
            # dung từ chối phù hợp, nên dùng câu chung nhưng vẫn KHÔNG rò rỉ chi tiết kỹ thuật.
            self._reply({{"answer": "Câu hỏi này ngoài phạm vi agent được cấu hình để trả lời."}})
        except MaxTurnsExceeded:
            self._reply({{"answer": "Agent lặp quá nhiều bước cho câu hỏi này — thử hỏi ngắn gọn hơn."}})
        except Exception as e:  # noqa: BLE001 — app standalone, báo lỗi rõ thay vì sập server
            self._reply({{"error": str(e)}}, 502)

    def _reply(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    _bridge.start()
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"{agent_name} — standalone — http://0.0.0.0:{{PORT}}")
    server.serve_forever()


if __name__ == "__main__":
    main()
'''

_DOCKERFILE_TEMPLATE = """FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
ENV PORT={port}
EXPOSE {port}
CMD ["python3", "standalone_server.py"]
"""

_DOCKERIGNORE = "__pycache__/\n*.sqlite3*\n.env\n.git/\n"

_MCP_README_SECTION = """
## MCP (đọc trang web qua internet thật)

Agent này khai báo dùng MCP tool (`AgentSpec.mcp_tool_names`) — bundle đã kèm thư mục `mcp_tools/`
(code + README) nhưng KHÔNG kèm `servers-venv/` (venv Python 3.10+ chứa MCP server thật — machine-
specific, quá nặng để bundle). PHẢI tự tạo venv này TRƯỚC khi chạy `standalone_server.py` để có tool
fetch — không làm bước này thì agent vẫn chạy được, chỉ THIẾU khả năng đọc web (tự phát hiện, không
crash):

```bash
cd mcp_tools
python3.10 -m venv servers-venv   # hoặc python3.11/3.12/3.14 — bất kỳ 3.10+
./servers-venv/bin/python3.10 -m pip install "mcp==1.29.0" mcp-server-fetch
cd ..
```

Xem `mcp_tools/README.md` (trong bundle này) cho chi tiết + bug thật gặp lúc build (version pin,
shebang vỡ khi đổi tên thư mục venv...).

**Bản thân `standalone_server.py` cũng cần Python 3.10+** (thư viện `mcp` client — MỌI phiên bản
trên PyPI pin `Requires-Python >=3.10`) — không chỉ riêng bước setup trên.
"""

_README_TEMPLATE = """# {agent_name} — standalone bundle

Sinh tự động bởi `monolith-agent-deploy-converter` từ `{src}`. Đừng sửa tay `standalone_server.py`
— sửa `agent_spec.py` ở package gốc rồi chạy lại converter.

## Chạy trực tiếp (không Docker)

```bash
pip install -r requirements.txt
export DEEPSEEK_API_KEY=sk-...   # hoặc OPENAI_API_KEY
python3 standalone_server.py
# mở http://localhost:{port}
```
{mcp_setup}
## Chạy bằng Docker (nếu có Dockerfile trong bundle này)

```bash
docker build -t {image_tag} .
docker run -p {port}:{port} -e DEEPSEEK_API_KEY=sk-... {image_tag}
```

**Lưu ý:** Dockerfile được sinh THEO ĐÚNG BEST PRACTICE (python:3.11-slim, COPY + pip install +
CMD) nhưng CHƯA được `docker build` thử thật — sandbox sinh ra bundle này không có Docker cài sẵn.
Kiểm tra kỹ trước khi triển khai production thật. **Nếu agent dùng MCP: Dockerfile hiện KHÔNG tự
tạo `mcp_tools/servers-venv/` bên trong image** — cần tự thêm bước cài vào Dockerfile trước khi
dùng MCP qua Docker (giới hạn CHỦ Ý, chưa làm — image target đường dùng trực tiếp `python3
standalone_server.py` đã verify sống, Docker+MCP thì chưa)."""


def _find_spec_function(module):
    """Tìm ĐÚNG 1 hàm build_*_agent_spec trong module — nhiều hơn 1 hoặc 0 đều fail loud, không
    đoán cái nào đúng."""
    import re

    candidates = [
        name
        for name, obj in vars(module).items()
        if callable(obj) and re.fullmatch(r"build_.*_agent_spec", name)
    ]
    if not candidates:
        raise SystemExit(
            f"Không tìm thấy hàm build_*_agent_spec nào trong {module.__file__} — "
            "quy ước bắt buộc, xem docstring converter này."
        )
    if len(candidates) > 1:
        raise SystemExit(
            f"Tìm thấy {len(candidates)} hàm build_*_agent_spec ({candidates}) trong "
            f"{module.__file__} — phải có ĐÚNG 1, không đoán cái nào đúng."
        )
    return candidates[0]


def _load_agent_spec_module(src, package, repo_root):
    """Import ĐÚNG như cách agent_spec.py THẬT được import trong project gốc (qua dotted package
    path, không phải file-location load trần) — agent_spec.py của weather_agent tự import
    `from demo_agents.weather_agent import agent` (absolute), cần `repo_root` nằm trên sys.path và
    cần load qua đúng package context thì import nội bộ đó mới resolve được."""
    spec_path = src / "agent_spec.py"
    if not spec_path.is_file():
        raise SystemExit(f"Không tìm thấy {spec_path} — quy ước bắt buộc, xem docstring converter này.")
    repo_root_str = str(repo_root.resolve())
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    import importlib

    return importlib.import_module(f"{package}.agent_spec")


def _derive_package(src, repo_root):
    try:
        rel = src.resolve().relative_to(repo_root.resolve())
    except ValueError:
        raise SystemExit(
            f"--src {src} không nằm trong repo root {repo_root} — truyền --package tường minh."
        )
    return ".".join(rel.parts)


def _should_copy(path):
    if path.name in _EXCLUDE_NAMES:
        return False
    if any(marker in path.name for marker in _EXCLUDE_MARKERS):
        return False
    if path.is_file() and any(path.name.startswith(pre) for pre in _EXCLUDE_PREFIXES):
        return False
    return True


def _copy_package_tree(src, dest_pkg_dir):
    """Copy TOÀN BỘ cây file .py + web/ của src vào dest, GIỮ NGUYÊN cấu trúc — không rewrite
    import nào. Loại test_*.py/.env/__pycache__/*.sqlite3* — không copy secret hay rác runtime."""
    dest_pkg_dir.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if not _should_copy(item):
            continue
        if item.is_dir():
            shutil.copytree(
                item,
                dest_pkg_dir / item.name,
                ignore=lambda d, names: [n for n in names if not _should_copy(Path(d) / n)],
            )
        else:
            shutil.copy2(item, dest_pkg_dir / item.name)


_MCP_EXCLUDE_NAMES = _EXCLUDE_NAMES | {"servers-venv"}  # venv machine-specific, KHÔNG bundle


def _copy_mcp_tools(repo_root, out):
    """Copy mcp_tools/ (repo_root/mcp_tools, xem README.md ở đó) vào bundle — TRỪ servers-venv/
    (venv Python 3.10+ chứa mcp-server-fetch, machine-specific/nặng, không bundle được — bundle chỉ
    kèm code + README.md hướng dẫn recipient tự tạo venv riêng, xem _README_TEMPLATE)."""
    src = Path(repo_root) / "mcp_tools"
    if not src.is_dir():
        raise SystemExit(
            f"AgentSpec khai báo mcp_tool_names nhưng không tìm thấy {src} — "
            "kho MCP tool dùng chung phải tồn tại ở repo root."
        )
    dest = out / "mcp_tools"
    shutil.copytree(
        src,
        dest,
        ignore=lambda d, names: [
            n
            for n in names
            if n in _MCP_EXCLUDE_NAMES
            or any(m in n for m in _EXCLUDE_MARKERS)
            or any(n.startswith(pre) for pre in _EXCLUDE_PREFIXES)
        ],
    )


def _ensure_init_chain(bundle_root, package_parts):
    """Tạo __init__.py rỗng cho từng cấp package CHA (vd demo_agents/__init__.py) — cấp package
    CUỐI (weather_agent/) đã copy nguyên vẹn từ src nên có __init__.py thật nếu src có."""
    cur = bundle_root
    for part in package_parts[:-1]:
        cur = cur / part
        cur.mkdir(parents=True, exist_ok=True)
        init = cur / "__init__.py"
        if not init.is_file():
            init.write_text("", encoding="utf-8")


def convert(src, out, target, package=None, port=8080, repo_root=None):
    src = Path(src)
    out = Path(out)
    repo_root = Path(repo_root) if repo_root else Path.cwd()
    package = package or _derive_package(src, repo_root)
    package_parts = package.split(".")

    module = _load_agent_spec_module(src, package, repo_root)
    spec_func = _find_spec_function(module)
    built_spec = getattr(module, spec_func)()
    agent_name = getattr(built_spec, "name", src.name)
    # Màu thương hiệu của agent (quy ước: màu công nghệ xương sống của domain agent theo, vd
    # Kubernetes blue cho agent DevOps — xem AgentSpec.accent_color) — dùng cho trang chat BUILT-IN
    # tối giản khi package không có web/chat.html riêng. Fallback #0a84ff (xanh trung tính) nếu
    # agent chưa khai báo accent_color, KHÔNG hardcode màu của 1 agent cụ thể nào làm mặc định chung.
    accent_color = getattr(built_spec, "accent_color", None) or "#0a84ff"
    # Tên các module mcp_tools/*.py agent này cần (vd ["fetch_server"]) — xem AgentSpec.mcp_tool_names.
    # Rỗng = agent không dùng MCP, converter bỏ qua toàn bộ bước bundle/wiring MCP bên dưới.
    mcp_tool_names = list(getattr(built_spec, "mcp_tool_names", []) or [])

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    _ensure_init_chain(out, package_parts)
    dest_pkg_dir = out.joinpath(*package_parts)
    _copy_package_tree(src, dest_pkg_dir)

    if mcp_tool_names:
        _copy_mcp_tools(repo_root, out)

    package_path = "/".join(package_parts)
    server_code = _STANDALONE_SERVER_TEMPLATE.format(
        package=package,
        spec_func=spec_func,
        port=port,
        package_path=package_path,
        agent_name=agent_name,
        accent_color=accent_color,
        accent_color_urlenc=accent_color.replace("#", "%23"),
        mcp_tool_names=mcp_tool_names,
    )
    (out / "standalone_server.py").write_text(server_code, encoding="utf-8")

    req_src = src / "requirements.txt"
    reqs = req_src.read_text(encoding="utf-8") if req_src.is_file() else "openai-agents\n"
    (out / "requirements.txt").write_text(reqs, encoding="utf-8")

    image_tag = agent_name.lower().replace(" ", "-")
    mcp_setup_note = (
        _MCP_README_SECTION if mcp_tool_names else ""
    )
    (out / "README.md").write_text(
        _README_TEMPLATE.format(
            agent_name=agent_name, src=src, port=port, image_tag=image_tag, mcp_setup=mcp_setup_note
        ),
        encoding="utf-8",
    )

    if target in ("docker", "both"):
        (out / "Dockerfile").write_text(_DOCKERFILE_TEMPLATE.format(port=port), encoding="utf-8")
        (out / ".dockerignore").write_text(_DOCKERIGNORE, encoding="utf-8")

    return {
        "out": out,
        "agent_name": agent_name,
        "package": package,
        "spec_func": spec_func,
        "tools": [t.name for t in built_spec.tools],
        "target": target,
        "accent_color": accent_color,
        "mcp_tool_names": mcp_tool_names,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--src", required=True, help="Folder chứa agent_spec.py (vd demo_agents/weather_agent)")
    parser.add_argument("--out", required=True, help="Thư mục xuất bundle")
    parser.add_argument(
        "--target", required=True, choices=("python", "docker", "both"),
        help="Đích triển khai — KHÔNG có mặc định, phải chọn tường minh",
    )
    parser.add_argument("--package", default=None, help="Ghi đè package path tự suy ra từ --src (vd demo_agents.weather_agent)")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--repo-root", default=".", help="Root dùng để tự suy ra --package từ --src")
    args = parser.parse_args()

    result = convert(args.src, args.out, args.target, args.package, args.port, args.repo_root)
    print(f"[monolith-agent-deploy-converter] '{result['agent_name']}' -> {result['out']}")
    print(f"  package: {result['package']} (hàm spec: {result['spec_func']})")
    print(f"  tools: {', '.join(result['tools'])}")
    print(f"  target: {result['target']}")
    print(f"  accent_color (trang chat built-in, dùng khi package không có web/chat.html riêng): {result['accent_color']}")
    if result["mcp_tool_names"]:
        print(f"  mcp_tool_names: {', '.join(result['mcp_tool_names'])} (đã bundle mcp_tools/ — "
              f"xem README.md § MCP trong bundle để cài servers-venv/ trước khi chạy)")
    print(f"  Chạy: cd {result['out']} && pip install -r requirements.txt && python3 standalone_server.py")


if __name__ == "__main__":
    main()
