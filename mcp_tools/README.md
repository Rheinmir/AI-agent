# mcp_tools — kho MCP server dùng chung cho mọi agent

Theo yêu cầu: "cho 1 kho tool riêng để chứa [MCP tool], và khi chạy xuất bản standalone thì kéo
kèm bản tool mcp ấy" — thư mục này là nơi DUY NHẤT chứa các MCP server thật mà `demo_agents/*`
kết nối tới, KHÔNG copy/duplicate cấu hình MCP riêng cho từng agent.

## Vì sao KHÔNG dùng Agent-Reach làm MCP server (dù được yêu cầu ban đầu)

Đã cài thật `github.com/Panniantong/agent-reach` (MIT, v1.5.0) vào `servers-venv/` và đọc trực tiếp
source code — MCP server CỦA CHÍNH agent-reach (`agent_reach/integrations/mcp_server.py`) chỉ expose
**1 tool duy nhất: `get_status`** (doctor/health-check "channel nào đã cài"). Docstring của chính
file đó nói rõ: *"Agent Reach is an installer + doctor tool. For actual reading/searching, agents
should call upstream tools directly (twitter-cli, yt-dlp, mcporter, etc.)"* — nghĩa là agent-reach
THẬT SỰ hoạt động bằng cách cài 1 loạt CLI riêng (twitter-cli, yt-dlp, bili-cli...) + 1 file
`SKILL.md` dạy agent CÓ BASH TOOL (như Claude Code/Cursor) cách tự gọi các CLI đó — không phải dạng
"1 MCP server phục vụ nội dung" mà `weather_agent`/`devops_agent` (agent hẹp, chỉ có `@function_tool`
Python, không có Bash tool) có thể dùng qua kết nối MCP.

→ Quyết định (xác nhận qua AskUserQuestion): dùng **`mcp-server-fetch`** — MCP reference server
chính thức của Model Context Protocol, chuyên fetch + convert nội dung trang web sang markdown,
đúng nghĩa "nội dung thật qua MCP". `agent-reach` vẫn giữ lại trong `servers-venv/` (cài thật, không
xoá — công sức đã verify, và `get_status`/`doctor` vẫn có thể hữu ích sau này), nhưng KHÔNG phải
integration chính.

## Exa search — trả lời "sao không tự search được?"

`mcp-server-fetch` CHỈ đọc 1 URL cụ thể, không tìm kiếm. Người dùng hỏi thẳng "ý là không tự search
được à" → thêm **Exa MCP** (`mcp.exa.ai`, remote HTTP MCP server, MIỄN PHÍ — không cần API key) qua
`exa_server.py`, expose `web_search_exa` (tìm kiếm ngữ nghĩa thật) + `web_fetch_exa` (đọc nhiều URL 1
lần). Verify sống qua `mcporter call exa.web_search_exa query="..."` TRƯỚC khi wire vào agent (đúng
nguyên tắc "verify sống trước khi cam kết"), sau đó verify lại qua `agents.mcp.server.
MCPServerStreamableHttp` + `Runner.run` thật.

## "Full Agent-Reach capability" — đã cài thật `--channels all`, kết quả trung thực

Người dùng: "thêm full khả năng của agent reach đi đừng thiến". Đã chạy
`agent-reach install --channels all` thật (không dry-run) và kiểm tra TỪNG kênh — kết quả trung
thực, không phóng đại:

**Hoạt động ngay, đã wire vào agent (`fetch_server.py` + `exa_server.py`):**
- ✅ Web fetch (bất kỳ trang nào, qua Jina Reader/mcp-server-fetch)
- ✅ Web search + fetch (Exa, miễn phí, không cần key)

**ĐÃ wire tiếp (theo yêu cầu "wire hết đi chứ") — `channels.py`, KHÔNG PHẢI MCP, plain
subprocess/thư viện, xem mục riêng bên dưới:**
- `gh` CLI (GitHub search) — ĐÃ authenticated sẵn trên máy này (account thật).
- `yt-dlp` (YouTube transcript) — binary ở `servers-venv/bin/yt-dlp`.
- `feedparser` (RSS/Atom) — thư viện Python thuần.

**KHÔNG THỂ bật — chặn bởi nhu cầu đăng nhập THẬT, không phải lựa chọn né tránh:**
- Twitter/X, Reddit, Facebook, Instagram, LinkedIn, XiaoHongShu, Xueqiu — cần **OpenCLI + cài
  extension Chrome + đăng nhập tài khoản CÁ NHÂN thật trong trình duyệt** (`opencli doctor` xác
  nhận kết nối) — sandbox này không có GUI browser, và đây là hành động chỉ CHỦ TÀI KHOẢN mới nên
  làm, không phải việc agent tự động hoá được.
- Twitter-cli/bili-cli — đã `pip install` xong (binary có ở `servers-venv/bin/{twitter,bili}`),
  nhưng thử gọi `twitter tweet <id>` KHÔNG cookie → treo (hang) vô thời hạn, không fail nhanh —
  xác nhận X/Twitter hiện yêu cầu auth cho MỌI thao tác, kể cả đọc 1 tweet công khai.
- Xiaoyuzhou (podcast transcription) — cần `ffmpeg` (chưa cài) + Groq API key (free, nhưng cần
  người dùng tự đăng ký lấy key tại console.groq.com, không phải thứ tôi có sẵn).
- V2EX — lỗi SSL certificate trong sandbox này (`CERTIFICATE_VERIFY_FAILED`), không phải lỗi
  credential — có thể sửa được (cấu hình cert) nhưng chưa điều tra do platform ít liên quan DevOps/
  weather.

Nếu người dùng MUỐN các kênh cần đăng nhập ở trên, cần tự làm bước đăng nhập (Chrome extension/
cookie) — sau đó có thể quay lại yêu cầu wire thành tool thật.

## `channels.py` — GitHub/YouTube/RSS, KHÔNG PHẢI MCP

Khác `fetch_server.py`/`exa_server.py` (MCP server thật, kết nối qua `agents.mcp`), `channels.py`
là 3 hàm Python THUẦN (`github_search_impl`, `youtube_transcript_impl`, `rss_read_impl`) — shell ra
CLI đã cài (`gh`, `servers-venv/bin/yt-dlp`) hoặc dùng thư viện (`feedparser`) trực tiếp, wrap bởi
`@function_tool` NGAY TRONG `agent.py` của từng agent (KHÔNG qua `mcp_servers=[...]`/
`build_agent_with_mcp` — không cần Python 3.10+ hay kết nối async nào, LUÔN có trong agent gốc).

**Bug thật gặp lúc build:**
1. `yt-dlp` bị dính lại đúng bug "shebang vỡ khi đổi tên venv" (xem mục Bug bên dưới) — dù đã chạy
   `pip install -U` sau khi rename, pip coi version đã đủ mới nên KHÔNG regenerate console-script,
   giữ nguyên shebang cũ trỏ `agent-reach-venv` (đã không còn tồn tại). Sửa: `--force-reinstall`.
2. `feedparser.parse(url)` (đưa thẳng URL) tự fetch bằng `urllib` — dính đúng lỗi SSL
   `CERTIFICATE_VERIFY_FAILED` như channel V2EX của agent-reach (thiếu liên kết cert `certifi` trên
   Python 3.14 cài qua Homebrew). Sửa: fetch bằng `requests` (đã verify ổn định qua weather_agent)
   rồi đưa RAW BYTES cho `feedparser.parse()` — không để feedparser tự làm network I/O.

## Blocker Python version — lý do project migrate baseline lên 3.10+

Thư viện `mcp` (client SDK chính thức, `agents.mcp.server.MCPServerStdio` cần nó) — **MỌI phiên bản
trên PyPI đều pin `Requires-Python >=3.10`**, không có bản nào chạy được Python 3.9 (baseline cũ của
project, cần `eval_type_backport` để vá cú pháp `X | None`). Không chỉ MCP SERVER (`mcp-server-fetch`,
chạy trong venv riêng ở đây) mà cả MCP CLIENT (import trong CHÍNH `agent.py`) đều bị chặn. → Migrate
toàn bộ `demo_agents/*` + `harness/*` sang Python 3.10+ (dùng 3.14 có sẵn qua `brew`), bỏ hẳn
`eval_type_backport` (3.10+ có native `X | None`). Xem `wiki/log.md` "python-3.10-migration-for-mcp".

## Cấu trúc

```
mcp_tools/
├── servers-venv/       # venv Python 3.14 RIÊNG cho MCP server (KHÔNG commit — .gitignore)
│                        #   - mcp-server-fetch==2026.7.10 + mcp==1.29.0 (server-side, xem ghi chú
│                        #     version pin bên dưới)
│                        #   - agent-reach==1.5.0 (giữ lại, chưa dùng làm integration chính)
├── fetch_server.py      # module Python (3.10+) — build_fetch_mcp_server() (+ alias build_mcp_server,
│                        #   xem § quy ước tên hàm), dùng chung weather_agent VÀ devops_agent
├── exa_server.py        # build_exa_mcp_server() (+ alias build_mcp_server) — search + fetch qua
│                        #   Exa MCP remote (mcp.exa.ai), miễn phí, không cần setup servers-venv
├── channels.py           # KHÔNG PHẢI MCP — github_search_impl/youtube_transcript_impl/rss_read_impl,
│                        #   wrap trực tiếp bởi @function_tool trong agent.py, xem mục riêng ở trên
├── test_servers.py       # 5 test hermetic (fetch_server.py/exa_server.py)
├── test_channels.py      # 9 test hermetic (channels.py)
└── README.md            # file này
```

## Quy ước tên hàm — `build_mcp_server()` chung cho MỌI module

Mỗi module `mcp_tools/*_server.py` PHẢI expose `build_mcp_server()` (alias của hàm tên riêng, vd
`build_fetch_mcp_server`) — `monolith_agent_deploy_converter.py` gọi ĐÚNG tên chung này khi bundle,
không đoán tên hàm riêng của từng module. Thêm module MCP mới PHẢI theo đúng quy ước này.

## Version pin quan trọng — KHÔNG tự ý nâng cấp `mcp` trong servers-venv

`mcp-server-fetch==2026.7.10` bị vỡ với `mcp==2.0.0` (rename `McpError`→`MCPError` giữa 2 bản mcp
mà mcp-server-fetch chưa theo kịp — bug thật gặp lúc build, `ImportError: cannot import name
'McpError'`). Server-side (`servers-venv/`) PIN `mcp==1.29.0`. Client-side (`.venv/` ở repo root,
dùng bởi `agents.mcp.server.MCPServerStdio`) dùng `mcp==2.0.0` mới nhất — 2 bên KHÔNG cần khớp version
nhau vì giao tiếp qua stdio JSON-RPC (wire protocol), không import chéo code Python.

## Setup (máy dev mới)

```bash
# 1. Cài Python 3.10+ nếu chưa có (project dùng 3.14 qua brew)
brew install python@3.14

# 2. Venv cho agent (client-side) — repo root
python3.14 -m venv .venv
./.venv/bin/pip install -r demo_agents/devops_agent/requirements.txt

# 3. Venv cho MCP server (server-side) — mcp_tools/
cd mcp_tools
python3.14 -m venv servers-venv
./servers-venv/bin/python3.14 -m pip install "mcp==1.29.0" mcp-server-fetch
```

## Bug thật gặp khi build (không phải giả định)

1. **Rename venv làm vỡ shebang** — venv ban đầu tên `agent-reach-venv`, đổi tên thành
   `servers-venv` SAU KHI đã cài package → mọi console-script (`pip`, `mcp-server-fetch`,
   `agent-reach`) có shebang trỏ đường dẫn CŨ, exec lỗi `FileNotFoundError` (dễ nhầm là thiếu file,
   thật ra là shebang interpreter không tồn tại). Sửa: reinstall qua `python3.14 -m pip` (không dùng
   script `pip` đã vỡ), console-script tự sinh lại đúng path mới.
2. **Nhầm package trùng tên trên PyPI** — `pip install agent-reach` (không kèm URL GitHub) cài nhầm
   1 package KHÁC HẲN, cùng tên "agent-reach" nhưng tác giả khác (`jgalea/agent-reach`, v0.1.0, mô tả
   gần giống nên dễ nhầm). Phát hiện qua `pip show` thấy sai `Home-page`/`Author`. Sửa: LUÔN cài từ
   URL GitHub tường minh (`pip install https://github.com/Panniantong/agent-reach/archive/main.zip`),
   không cài theo tên trần khi biết trước tên đó có thể trùng.
3. **`mcp-server-fetch` vỡ với `mcp` mới nhất** — xem mục Version pin ở trên.
4. **Noise không phải lỗi**: lần đầu chạy `mcp-server-fetch` in ra vài dòng non-JSON lẫn vào stdout
   (giống log `npm`, không rõ nguồn — không phải từ chính `mcp_server_fetch` source, có thể từ 1
   process khác trên máy). MCP client (`mcp.client.stdio`) tự log "Failed to parse JSONRPC message"
   cho các dòng đó rồi BỎ QUA, không crash — verify sống 2 lần liên tiếp đều ra kết quả đúng
   (`https://example.com` → "Example Domain") dù có noise này. Chưa xác định gốc rễ 100%, không
   chặn chức năng nên chưa điều tra sâu thêm.

## Origin
- **Log:** `wiki/log.md` — "python-3.10-migration-for-mcp", "wire-mcp-fetch-into-agents"
