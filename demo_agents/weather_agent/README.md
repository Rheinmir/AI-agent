# Weather agent

Agent thật minh hoạ 3 yếu tố nền tảng của OpenAI Agents SDK (xem `llmwiki/wiki/concepts/agent.md`),
mở rộng thêm 3/7 layer từng thiếu trong `llmwiki/wiki/concepts/agent-7-layers.md`:

| Yếu tố | Ở đâu trong code |
|---|---|
| Model | `agent.py` — `model_provider.get_model()`: DeepSeek (`deepseek-chat`) nếu có `DEEPSEEK_API_KEY`, else `gpt-4o-mini` nếu có `OPENAI_API_KEY` |
| Tools | `agent.py` — `get_weather` (`@function_tool`), gọi API thật **Open-Meteo** (geocoding + forecast), không mock, hoạt động cho bất kỳ thành phố nào trên thế giới |
| Instructions | `agent.py` — biến `INSTRUCTIONS`: luôn gọi tool trước khi trả lời, không bịa số liệu, báo rõ khi không có dữ liệu (`NO_DATA:`) |
| Memory (trong phiên) | `chatdemo.py` — `SQLiteSession` (Agents SDK), nhớ trong 1 cuộc trò chuyện |
| Memory (dài hạn, xuyên phiên) | `memory.py` — `remember_last_city`/`recall_last_city`, SQLite riêng, nhớ thành phố tra cứu thành công gần nhất kể cả sau khi mở cuộc trò chuyện mới hoặc restart server. Tool `recall_last_city` trong `agent.py` — CHỈ dùng để gợi ý, agent luôn hỏi xác nhận lại chứ không tự ý coi là đúng |
| Data Collector | `data_collector.py` — `lookup_city_note`, tập ghi chú thu thập sẵn (múi giờ, đặc điểm khí hậu chung) cho một số thành phố tiêu biểu, index bằng dict từ khoá (không phải vector DB đầy đủ). Tool `get_city_note` trong `agent.py` |
| Harness | `harness.py` — `run_with_harness`, bọc `Runner.run_sync` với `max_turns` tường minh (6, thay vì mặc định ẩn 10 của SDK) + retry có backoff cho lỗi mạng tạm thời (không retry `MaxTurnsExceeded` vì đó là lỗi tất định). Câu hỏi kiểu "bạn làm được gì" được Harness bắt và trả lời TẤT ĐỊNH (`_CAPABILITY_REPORT`, không qua model) — liệt kê đủ tên từng layer, tránh việc model tự diễn giải rồi bỏ sót từ khoá |
| Input guardrail | `guardrails.py` — `weather_scope_guardrail` (`@input_guardrail` thật của Agents SDK, không phải văn bản mô tả trong INSTRUCTIONS), chạy 1 agent phân loại riêng SONG SONG với model chính. Câu hỏi ngoài phạm vi (địa lý, lịch sử, hỏi về chính kiến trúc code của agent...) trip tất định → `harness.py` bắt `InputGuardrailTripwireTriggered` và trả `OUT_OF_SCOPE_MESSAGE` cố định, model chính không tự "sáng tác" cách từ chối mỗi lần nữa. Output văn bản thuần (không dùng `output_type=<pydantic>`) vì DeepSeek — provider chính của sandbox — không hỗ trợ structured output kiểu SDK dùng, lỗi 400 |
| Monitoring / hooks | `monitoring.py` — `WeatherAgentHooks` (`AgentHooks` thật của Agents SDK, gắn qua `Agent(hooks=...)`), ghi mỗi sự kiện vòng đời (bắt đầu lượt, gọi tool, gọi LLM, kết thúc lượt) vào `monitoring.sqlite3` local — không cần đổi sang LangChain/LangGraph để có observability, SDK đang dùng đã có sẵn hook, chỉ cần gắn logger |
| Agent portability (converter) | `agent_spec.py` — `AgentSpec` trung lập framework (tên, instructions, tools, guardrail, `mcp_tool_names`) dựng TỪ chính object thật trong `agent.py`/`guardrails.py`. `exporters/openai_agents_exporter.py` dựng lại 1 `Agent` CHẠY THẬT từ spec (round-trip đã kiểm chứng — tool rebuild gọi đúng logic gốc). `exporters/{langchain,langgraph,claude_agent_sdk,azure_ai}_exporter.py` là STUB có sơ đồ ánh xạ rõ ràng, raise `NotImplementedError` (chưa cài SDK tương ứng — không giả vờ chạy được) |
| MCP (internet thật) | `agent.py::build_agent_with_mcp` — gắn tool `fetch` (`mcp-server-fetch`, xem `mcp_tools/README.md`) qua `agents.mcp.MCPServerManager`. Đọc-only 1 URL cụ thể, chỉ cho phép nếu liên quan thời tiết (`guardrails.py`). `harness.py::run_with_harness` đã đổi sang `async def` để chạy đúng trên event loop đã connect MCP |

So với `agent-7-layers.md`, phần còn thiếu: Context/Instruction (vẫn dựa hoàn toàn vào assembly
ngầm của Agents SDK, chưa có logic tự viết) và Evaluation nằm ở `harness/scripts/wikieval.py`
(ngoài thư mục này, chạy offline — xem `llmwiki/wiki/sources/evals/agent-*.md`).

## Cài đặt (Python 3.10+ bắt buộc)

**Baseline runtime đã migrate từ Python 3.9 lên 3.10+** — thư viện `mcp` client (cần cho MCP fetch
tool) pin `Requires-Python >=3.10` ở MỌI phiên bản trên PyPI, không có ngoại lệ. Xem
`mcp_tools/README.md` cho chi tiết đầy đủ + bug thật gặp lúc migrate.

```bash
python3.10 -m venv .venv   # hoặc 3.11/3.12/3.14 — bất kỳ 3.10+
./.venv/bin/pip install -r demo_agents/weather_agent/requirements.txt

# (Optional nhưng khuyến nghị) cài MCP server để có tool fetch
cd mcp_tools && python3.10 -m venv servers-venv && \
  ./servers-venv/bin/python3.10 -m pip install "mcp==1.29.0" mcp-server-fetch && cd ..
```

## Cấu hình key (để chạy agent thật)

Copy `.env.example` thành `.env` (đã `.gitignore`, không commit) và điền **một** trong hai key:

```
DEEPSEEK_API_KEY=sk-...
# hoặc
OPENAI_API_KEY=sk-...
```

## Chạy test offline (không cần key, không gọi mạng thật — mock `requests.get`/MCP server giả)

```bash
./.venv/bin/python -m pytest demo_agents/weather_agent/ -q
```

## Demo 1 — Tool thật, không qua LLM (port 8766)

Gọi trực tiếp `_get_weather_impl()` (Open-Meteo thật), không cần key model:

```bash
./.venv/bin/python -m demo_agents.weather_agent.webdemo
# mở http://127.0.0.1:8766
```

## Demo 2 — Chatbot agent thật, nhớ hội thoại (port 8767)

Giao diện chat kiểu ChatGPT, gọi `Runner.run_sync(weather_agent, question, session=...)` — model thật
tự quyết định gọi tool, tự nhớ ngữ cảnh hội thoại qua nhiều lượt (`SQLiteSession` của Agents SDK):

```bash
./.venv/bin/python -m demo_agents.weather_agent.chatdemo
# mở http://127.0.0.1:8767
```

Thử hỏi "Đọc giúp tôi bài viết thời tiết ở https://..." để test tool `fetch` (MCP) — chỉ hoạt động
nếu đã cài `mcp_tools/servers-venv/` (xem § Cài đặt); nếu chưa, agent tự phát hiện và trả lời không
có MCP, không crash.

Cùng server còn có 2 trang dashboard (`dashboard.py`, server-render, không JS framework):
- **`/monitor`** — phân tích `monitoring.sqlite3`: tổng lượt hỏi, guardrail chặn bao nhiêu lần, tool
  nào dùng nhiều, latency trung bình (theo lượt/theo lần gọi LLM, ghép cặp qua `run_id`), tỉ lệ lỗi
  trong 20 lượt gần nhất (cảnh báo nếu >30%), theo từng session, xu hướng 14 ngày, 50 sự kiện gần
  nhất, tự dọn dữ liệu >30 ngày mỗi lần tải trang + tóm tắt eval kèm cảnh báo nếu code đã sửa sau
  khi baseline được sinh.
- **`/evaluate`** — chi tiết từng golden trong `harness/metrics/eval-baseline.json` (pass/fail,
  asserts, chấm bởi tier nào).

## Chạy CLI một câu hỏi

```bash
./.venv/bin/python -m demo_agents.weather_agent.run "Thời tiết ở Hà Nội thế nào?"
```

(Không chạy trực tiếp `python demo_agents/weather_agent/run.py` — sẽ lỗi `ModuleNotFoundError` vì
repo root không tự vào `sys.path` khi gọi file trực tiếp kiểu đó.)

## Giới hạn đã biết

- Geocoding của Open-Meteo đôi khi không nhận ra tên gọi cũ/thông tục (vd "Sài Gòn" thay vì
  "Ho Chi Minh City") — đây là giới hạn của bộ dữ liệu geocoding, không phải bug logic.
- Không triển khai multi-agent hay guardrails nâng cao — vẫn tập trung đúng 3 yếu tố nền tảng.
- `chat_sessions.sqlite3` (bộ nhớ hội thoại) là state runtime, không commit vào git.
- Tool `fetch` (MCP) chỉ đọc-only 1 URL cụ thể do người dùng cung cấp — KHÔNG phải search engine,
  không tự tìm kiếm. Guardrail chỉ cho fetch URL được nêu rõ là liên quan thời tiết.
- `mcp_tools/servers-venv/` KHÔNG tự cài — phải chạy tay bước setup (xem trên) trước khi tool fetch
  hoạt động; thiếu bước này agent vẫn chạy được, chỉ thiếu khả năng đọc web (tự phát hiện, in log
  `[MCP] Không kết nối được...`, không crash).
