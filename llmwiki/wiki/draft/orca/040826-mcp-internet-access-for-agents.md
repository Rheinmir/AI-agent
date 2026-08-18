---
type: draft
title: mcp-internet-access-for-agents
status: proposed
tags: [orca-workflow, output-report]
timestamp: 2026-08-04
task: T-260727-01
---

# 040826-mcp-internet-access-for-agents
**Type:** draft
**Status:** proposed
**Tags:** orca-workflow, output-report
**Proposed:** 2026-08-04

## Agent Task Assignment
| Task | Agent | Status |
|------|-------|--------|
| Nghiên cứu Agent-Reach (repo GitHub được yêu cầu) — cài thật, đọc source | Claude Code | done |
| Phát hiện Agent-Reach KHÔNG phải MCP content server, đổi hướng sang mcp-server-fetch | Claude Code | done (xác nhận qua AskUserQuestion) |
| Phát hiện + xử lý blocker Python 3.9 → migrate baseline lên 3.10+ | Claude Code | done (xác nhận qua AskUserQuestion) |
| Wire MCP fetch tool vào devops_agent (agent.py + guardrails.py + run.py + chatdemo.py) | Claude Code | done, verify sống |
| Propagate cùng pattern sang weather_agent (kèm chuyển harness.py sang async) | Claude Code | done, verify sống |
| Mở rộng agent_spec.py + monolith-agent-deploy-converter để bundle MCP khi export standalone | Claude Code | done, verify sống |
| Thêm Exa MCP (search + fetch thật, miễn phí) — trả lời "không tự search được à" | Claude Code | done, verify sống |
| Audit trung thực "full Agent-Reach capability" (`--channels all` thật) | Claude Code | done |

## What
Người dùng: "lên github lấy về repo agent-reach để cho phép agent claim thông tin từ ngoài internet
kết nối dạng mcp". Sau khi cài thật và đọc source, phát hiện Agent-Reach (`Panniantong/agent-reach`,
MIT, v1.5.0) **không phải** 1 MCP content server — nó là bộ cài CLI (twitter-cli/yt-dlp/bili-cli...)
+ 1 file `SKILL.md` dạy agent CÓ BASH TOOL (Claude Code/Cursor) cách tự gọi CLI trực tiếp; MCP server
của chính nó chỉ có 1 tool `get_status` (doctor/health-check). Không khớp `weather_agent`/
`devops_agent` (agent hẹp, chỉ có `@function_tool`, không có Bash). Xác nhận qua AskUserQuestion:
đổi sang **`mcp-server-fetch`** (MCP reference server chính thức, fetch + convert nội dung web sang
markdown) — đúng nghĩa MCP content server.

Phát hiện blocker thứ 2 khi wire: thư viện `mcp` (client, `agents.mcp.server.MCPServerStdio` cần)
pin `Requires-Python >=3.10` ở MỌI phiên bản trên PyPI — không chỉ server mà cả client trong CHÍNH
`agent.py` cũng bị chặn bởi baseline Python 3.9 cũ của project (vốn cần `eval_type_backport` để vá).
Xác nhận qua AskUserQuestion: migrate TOÀN BỘ `demo_agents/*` + `harness/*` lên Python 3.10+ (dùng
3.14 có sẵn qua brew) thay vì tự viết MCP client tối giản để giữ 3.9.

## Output

### Kho MCP tool dùng chung
- `mcp_tools/README.md` + `mcp_tools/fetch_server.py` — `build_fetch_mcp_server()`, 1 nguồn sự thật
  cho cấu hình `MCPServerStdio` trỏ tới `mcp-server-fetch`, dùng chung bởi cả 2 agent.
- `mcp_tools/servers-venv/` (KHÔNG commit, `.gitignore`) — venv Python 3.14 chứa `agent-reach==1.5.0`
  (giữ lại, không dùng làm integration chính) + `mcp-server-fetch==2026.7.10` + `mcp==1.29.0` (PIN —
  bản 2.0.0 vỡ `mcp-server-fetch` vì rename `McpError`→`MCPError` chưa được cập nhật theo).

### Migrate Python 3.9 → 3.10+
- `.venv/` (repo root, không commit) — Python 3.14, `openai-agents==0.8.4` + `openai==2.19.0` +
  `mcp` (client) + `pytest` + `requests`, KHÔNG cần `eval_type_backport` nữa (3.10+ có native
  `X | None`). `.python-version` = `3.14`.
- `demo_agents/{weather,devops}_agent/requirements.txt` — bỏ `eval_type_backport`, thêm `mcp`.
- 103 test cũ pass KHÔNG SỬA GÌ dưới Python 3.14 (verify trước khi làm gì thêm) — migrate an toàn.

### Wire MCP vào 2 agent
- `agent.py` (cả 2): thêm `dataclasses`, `build_agent_with_mcp(mcp_servers)` — TRẢ VỀ BẢN SAO của
  agent gốc (`dataclasses.replace`) có gắn `mcp_servers` + instructions nối thêm
  `_MCP_INSTRUCTIONS_ADDENDUM` (mô tả tool `fetch`, đọc-only 1 URL cụ thể — KHÔNG PHẢI search
  engine). Agent GỐC (`devops_agent`/`weather_agent`) KHÔNG đổi — vẫn chạy không cần MCP, giữ tương
  thích ngược cho test/import trực tiếp.
- `guardrails.py` (cả 2): thêm nhánh TRONG PHẠM VI cho "đọc/tóm tắt 1 trang web CỤ THỂ (URL rõ
  ràng)" — devops_agent: bất kỳ URL nào (miễn không phải "thực thi hành động trên hệ thống nội bộ");
  weather_agent: CHỈ nếu URL được nêu là liên quan thời tiết (giữ đúng phạm vi hẹp gốc). **Bug thật
  gặp lúc verify sống:** ban đầu quên thêm nhánh này cho weather_agent — mọi yêu cầu fetch bị guardrail
  chặn dù INSTRUCTIONS đã mô tả tool tồn tại, phát hiện qua test `curl` trực tiếp, không phải đọc code.
- `run.py` (cả 2): đổi từ `Runner.run_sync` sync sang `async def _run_async()` + `agents.mcp.
  MCPServerManager` (`async with manager: ... await Runner.run(...)`) — `drop_failed_servers=True`
  mặc định nên MCP không cài được KHÔNG crash CLI, chỉ thiếu tool fetch.
- `chatdemo.py` (cả 2): thêm `_MCPBridge` — 1 event loop asyncio chạy NỀN suốt vòng đời process,
  connect MCP 1 LẦN lúc `start()` (không phải mỗi tin nhắn), theo đúng pattern "FastAPI lifespan"
  mà `agents.mcp.MCPServerManager` khuyến nghị trong docstring, chuyển sang `http.server` thuần
  bằng thread nền + `run_coroutine_threadsafe`. `weather_agent/harness.py::run_with_harness` đổi
  `def`→`async def`, `Runner.run_sync`→`await Runner.run`, `time.sleep`→`await asyncio.sleep` (bug
  thật: blocking `time.sleep` trong 1 loop async sẽ đóng băng CẢ kết nối MCP đang chạy trên loop đó).

### Deploy-converter — bundle MCP khi export standalone
- `AgentSpec.mcp_tool_names: list[str]` (cả 2 `agent_spec.py`) — cả 2 agent set
  `["fetch_server"]`, đồng thời spec xuất ra LUÔN gồm `_MCP_INSTRUCTIONS_ADDENDUM` (khớp hành vi
  mặc định của `chatdemo.py`/`run.py`, không phải 2 hành vi khác nhau giữa chạy-tại-chỗ và đóng-gói).
- `exporters/openai_agents_exporter.py` (cả 2) — `build_openai_agent()` thêm tham số
  `mcp_servers=None`, truyền qua `Agent(mcp_servers=...)`.
- `harness/scripts/monolith_agent_deploy_converter.py` — `_copy_mcp_tools()` (bundle `mcp_tools/`
  TRỪ `servers-venv/`, machine-specific/quá nặng); `standalone_server.py` sinh ra có `_MCPBridge`
  y hệt pattern `chatdemo.py`; `README.md` sinh thêm `_MCP_README_SECTION` (hướng dẫn tự tạo
  `servers-venv/`) khi agent khai `mcp_tool_names`.

## Verify SỐNG (không chỉ đọc code — theo đúng kỷ luật của project)
1. **Bug thật lúc setup `servers-venv/`** (3 bug liên tiếp, không phải giả định):
   - Đổi tên thư mục venv SAU khi đã cài package → mọi console-script vỡ shebang
     (`FileNotFoundError` gây hiểu nhầm là thiếu file) — sửa bằng `python3.14 -m pip` thay vì script
     `pip` đã vỡ.
   - `pip install agent-reach` (không kèm URL) cài NHẦM 1 package KHÁC cùng tên trên PyPI (tác giả
     `jgalea`, v0.1.0) — phát hiện qua `pip show` sai `Home-page`/`Author`, sửa bằng cài từ URL
     GitHub tường minh.
   - `mcp-server-fetch==2026.7.10` vỡ với `mcp==2.0.0` mới nhất (`ImportError: McpError`) — pin
     `mcp==1.29.0` cho server-side (client-side `.venv/` vẫn dùng `mcp==2.0.0`, 2 bên không cần
     khớp version vì giao tiếp qua stdio JSON-RPC).
2. **`agents.mcp.MCPServerStdio` + `Runner.run` thật** — script độc lập, `async with server:`, hỏi
   agent thật fetch `https://example.com`, model trả lời đúng nội dung trang thật (không hallucinate).
3. **`run.py` cả 2 agent** — CLI hỏi câu cần fetch (trả lời đúng dùng tool `fetch`), câu hỏi thường
   (không đổi hành vi so với trước MCP), câu hỏi ngoài phạm vi (guardrail vẫn chặn đúng).
4. **`chatdemo.py` cả 2 agent, qua HTTP thật** (`curl` vào server chạy nền, không phải gọi hàm Python
   trực tiếp) — `/api/chat` fetch URL thật, câu hỏi thường, guardrail off-topic, guardrail "thực thi
   hành động" (devops), capability short-circuit (`_is_capability_question`, weather — xác nhận
   KHÔNG bị lẫn với guardrail dù dùng câu hỏi không dấu ban đầu gây hiểu nhầm, rồi test lại đúng
   dấu xác nhận hành vi cũ không đổi), `/api/sessions`/`/api/history`/`/api/reset` đều còn đúng.
5. **Zombie process thật gây hiểu nhầm kết quả test** — sau khi sửa guardrail weather_agent và
   restart server, `curl` vẫn trả kết quả CŨ suốt nhiều lần thử — hoá ra 1 process Python 3.9 CŨ
   (chạy từ đầu phiên làm việc, ~6 tiếng trước) vẫn giữ port 8767, các lần "restart" của tôi bind
   port thất bại và exit âm thầm, `curl` luôn hit process cũ. Phát hiện qua `lsof -i :8767` xem
   ĐÚNG PID nào đang LISTEN — quy tắc rút ra: khi hành vi sống "không đổi dù đã sửa code", kiểm tra
   xem có đúng process nào đang phục vụ request trước khi nghi ngờ code.
6. **Deploy-converter — bundle THẬT, chạy trong process HOÀN TOÀN TÁCH BIỆT** — convert
   `devops_agent` với `--target python`, tự tạo `mcp_tools/servers-venv/` + `.venv/` MỚI trong thư
   mục bundle (đúng như README sinh ra hướng dẫn, không dùng lại venv của repo gốc), chạy
   `standalone_server.py` trên port khác hẳn (8770) → `/api/chat` fetch URL thật, câu hỏi thường,
   guardrail off-topic đều đúng — chứng minh 1 recipient THẬT làm đúng theo README sẽ có agent hoạt
   động đầy đủ MCP, không chỉ code "trông có vẻ đúng".
7. `pytest demo_agents/ harness/scripts` → **118 passed** (109 trước MCP → +6 test
   `build_agent_with_mcp` mỗi agent hermetic → +3 test converter MCP-bundling) trên Python 3.14.

## Files
| File | Action |
|------|--------|
| `mcp_tools/README.md`, `mcp_tools/fetch_server.py`, `mcp_tools/__init__.py` | created |
| `.venv/`, `mcp_tools/servers-venv/` | created (không commit) |
| `.python-version` | created |
| `.gitignore` | edited (thêm `.venv/`, `servers-venv/`, `__pycache__/`, `devops_agent/chat_sessions.sqlite3*`) |
| `demo_agents/{weather,devops}_agent/requirements.txt` | edited (bỏ eval_type_backport, thêm mcp) |
| `demo_agents/{weather,devops}_agent/agent.py` | edited (build_agent_with_mcp + addendum) |
| `demo_agents/{weather,devops}_agent/guardrails.py` | edited (carve-out cho fetch URL) |
| `demo_agents/{weather,devops}_agent/run.py` | edited (async + MCPServerManager) |
| `demo_agents/{weather,devops}_agent/chatdemo.py` | edited (_MCPBridge) |
| `demo_agents/weather_agent/harness.py` | edited (async def, Runner.run, asyncio.sleep) |
| `demo_agents/weather_agent/test_harness.py` | edited (async-compatible mocks) |
| `demo_agents/{weather,devops}_agent/test_agent_mcp.py` | created |
| `demo_agents/{weather,devops}_agent/agent_spec.py` | edited (mcp_tool_names, addendum instructions) |
| `demo_agents/{weather,devops}_agent/exporters/openai_agents_exporter.py` | edited (mcp_servers param) |
| `harness/scripts/monolith_agent_deploy_converter.py` | edited (_copy_mcp_tools, _MCPBridge template, README §MCP) |
| `harness/scripts/test_monolith_agent_deploy_converter.py` | edited (+3 test MCP bundling) |
| `demo_agents/{weather,devops}_agent/README.md` | edited (Python 3.10+, MCP setup, demo commands) |
| `mcp_tools/exa_server.py` | created (search + fetch thật, miễn phí, remote HTTP MCP) |
| `mcp_tools/test_servers.py` | created (5 test hermetic) |
| `demo_agents/{weather,devops}_agent/{agent,guardrails,run,chatdemo,agent_spec}.py` | edited lần 2 (thêm exa_server) |
| `wiki/index.md`, `wiki/log.md` | updated |

## Notes
- Invoked via: yêu cầu trực tiếp người dùng ("lên github lấy về repo agent-reach..."), 3 vòng
  AskUserQuestion trước/trong khi build (đổi tool MCP thật sau khi phát hiện Agent-Reach không khớp
  mục đích; xử lý blocker Python 3.9; hướng đi devops-color trước đó không liên quan) — tuân đúng
  kỷ luật "xác nhận phạm vi trước khi build lớn" đã áp dụng suốt session, đặc biệt quan trọng ở đây
  vì phát hiện lúc NGHIÊN CỨU (không phải đoán trước) làm thay đổi hẳn hướng kỹ thuật 2 lần liên tiếp.
- **Cố ý KHÔNG làm:** Docker + MCP (Dockerfile sinh ra chưa tự cài `servers-venv/` bên trong image —
  ghi rõ trong README sinh ra, target `python` (không Docker) đã verify sống đầy đủ); cleanup/
  shutdown sạch cho `_MCPBridge` khi process bị kill (chấp nhận cho demo server, không phải
  production service); MCP cho bất kỳ platform nào khác ngoài web fetch (Twitter/Reddit/YouTube của
  Agent-Reach — không phải mục đích chính, `agent-reach` vẫn cài trong `servers-venv/` nếu sau này
  cần dùng CLI trực tiếp qua subprocess, không phải MCP).
- **Bài học lớn nhất:** "MCP compatible" trong marketing/README của 1 tool KHÔNG đảm bảo tool đó
  THẬT SỰ phục vụ nội dung qua MCP — phải đọc source code MCP server thật (không chỉ docs) trước khi
  cam kết tích hợp; ở đây phát hiện MCP server của Agent-Reach chỉ có 1 tool `get_status` bằng cách
  đọc trực tiếp `agent_reach/integrations/mcp_server.py` sau khi cài thật, không phải suy luận từ
  README.
- **Bổ sung sau khi người dùng hỏi "không tự search được à"** — thêm Exa MCP (search+fetch thật,
  miễn phí) — chi tiết đầy đủ ở `wiki/log.md` entry "exa-search-and-agent-reach-full-capability-audit"
  (không lặp lại ở đây). Sau đó người dùng: "thêm full khả năng của agent reach đi đừng thiến" —
  audit trung thực bằng cách chạy `agent-reach install --channels all` THẬT, không suy luận: 2/15
  kênh hoạt động ngay và đã wire (web fetch + Exa search), phần còn lại chặn bởi nhu cầu ĐĂNG NHẬP
  TÀI KHOẢN CÁ NHÂN thật (Twitter/Reddit/Facebook/Instagram/LinkedIn/XiaoHongShu/Xueqiu — cần
  OpenCLI + Chrome extension + browser session của chính người dùng) — đây là RÀNG BUỘC THẬT, không
  phải lựa chọn giới hạn phạm vi, xem `mcp_tools/README.md` § Full Agent-Reach capability cho danh
  sách đầy đủ từng kênh + lý do cụ thể.
- **Chưa commit** — theo quy tắc an toàn chung, chờ user xác nhận rõ ràng.

## Origin
- **Draft:** `wiki/draft/orca/040826-mcp-internet-access-for-agents.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
