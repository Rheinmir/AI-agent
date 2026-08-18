---
type: concept
title: Agent portability — spec trung lập + exporter (converter giữa các framework)
tags: [agent, portability, langchain, langgraph, converter]
timestamp: 2026-08-04
---

# Agent portability — spec trung lập + exporter

Kỹ thuật để "định nghĩa 1 lần, xuất ra nhiều framework" thay vì viết lại toàn bộ agent mỗi khi đổi/
thử framework khác (openai-agents SDK, LangChain, LangGraph, Claude Agent SDK, Azure AI Agent
Service). Áp dụng thật ở `demo_agents/weather_agent/agent_spec.py` + `exporters/`.

## Vì sao KHÔNG phải "converter 2 chiều đầy đủ"

Chuyển đổi đầy đủ hai chiều giữa các framework agent là bài toán rất lớn — mỗi framework có mô hình
khác hẳn nhau:
- **openai-agents SDK**: Agent + Runner + Tool (vòng lặp phẳng, ẩn bên trong `Runner.run`).
- **LangChain**: Chain/AgentExecutor + `StructuredTool` (cần pydantic `args_schema`, không nhận
  JSON schema thô).
- **LangGraph**: StateGraph — mô hình GRAPH/STATE-MACHINE, không phải "1 agent + list tool" phẳng.
- **Claude Agent SDK**: `@tool` decorator kiểu MCP (Model Context Protocol), `input_schema` gần
  giống JSON schema chuẩn hơn hẳn LangChain.
- **Azure AI Agent Service**: `FunctionTool` tự sinh schema từ type hint (giống `@function_tool`),
  nhưng không có input-guardrail runtime hay hook lifecycle native.

Không có 1 cấu trúc trung gian nào biểu diễn được ĐẦY ĐỦ mọi khái niệm của mọi framework (đặc biệt
guardrail và hooks — xem bảng dưới). Cố ép tất cả vào 1 khuôn chung sẽ mất thông tin hoặc phải giả
lập hành vi không có sẵn.

## Cách tiếp cận đã chọn: định nghĩa 1 lần, xuất ra nhiều đích

1. **`AgentSpec`** (`agent_spec.py`) — spec trung lập TỐI THIỂU, đủ cho 1 tool-calling agent đơn
   giản: `name`, `instructions`, `tools` (mỗi tool = tên + description + JSON schema + hàm python
   THUẦN đứng sau, không có gì thuộc riêng 1 framework), `guardrails`, `hooks`.
2. Spec **KHÔNG định nghĩa lại logic** — nó tham chiếu trực tiếp các object thật đã có (
   `FunctionTool` đã dựng qua `@function_tool`, `InputGuardrail` đã dựng qua `@input_guardrail`) —
   một nguồn sự thật duy nhất, tránh 2 chỗ định nghĩa "chức năng của tool X" lệch nhau theo thời
   gian.
3. **Exporter** — 1 hàm nhận `AgentSpec`, dựng agent CHẠY ĐƯỢC trên 1 framework cụ thể:
   - `exporters/openai_agents_exporter.py` — **chạy thật**, round-trip đã kiểm chứng bằng test
     (`test_agent_spec.py`): dựng lại `Agent` từ spec, gọi tool của agent DỰNG LẠI, xác nhận gọi
     đúng logic gốc.
   - `exporters/langchain_exporter.py`, `langgraph_exporter.py`, `claude_agent_sdk_exporter.py`,
     `azure_ai_exporter.py` — **STUB**: sơ đồ ánh xạ field-theo-field viết rõ trong docstring, hàm
     `raise NotImplementedError` (KHÔNG giả vờ chạy được khi chưa cài SDK/chưa test thật — fail loud
     thay vì fail âm thầm). Điền code thật khi project thực sự cần chạy trên framework đó.

## Bảng ánh xạ nhanh (rút gọn — chi tiết ở docstring từng exporter)

| Khái niệm | openai-agents | LangChain | LangGraph | Claude Agent SDK | Azure AI Agent |
|---|---|---|---|---|---|
| Tool | `FunctionTool` | `StructuredTool` (cần pydantic) | dùng chung LangChain Tool | `@tool` (MCP, JSON schema) | `FunctionTool` (tự sinh từ type hint) |
| Input guardrail | `@input_guardrail`, chặn TRƯỚC agent loop | không có tương đương native | node điều kiện trước node "agent" | không có — tự viết lớp kiểm tra trước `query()` | không có — Content Safety là dịch vụ riêng, không phải logic tuỳ biến |
| Hooks/monitoring | `AgentHooks` (callback trực tiếp) | Callbacks (`BaseCallbackHandler`) | event stream (`astream_events`) | hook system riêng (`PreToolUse`...) | polling `run.status` hoặc streaming event handler |

## monolith-agent-deploy-converter — đóng gói thành app chat standalone

Công cụ RIÊNG dùng ĐÚNG quy ước `AgentSpec` ở trên để làm việc khác: không chuyển đổi FRAMEWORK,
mà đóng gói 1 agent (bất kỳ folder nào có `agent_spec.py` đúng quy ước, không chỉ weather_agent)
thành 1 app chat standalone — "bỏ folder src vào, bốc đi triển khai bất kỳ đâu".

`harness/scripts/monolith_agent_deploy_converter.py --src <folder> --out <dir> --target
{python,docker,both}` (không có target mặc định — phải chọn tường minh):

1. Tìm ĐÚNG 1 hàm `build_*_agent_spec` trong `<src>/agent_spec.py` — 0 hoặc >1 đều fail loud, không
   đoán cái nào đúng.
2. Copy TOÀN BỘ cây file của `<src>` vào bundle, **GIỮ NGUYÊN cấu trúc package gốc** (vd
   `demo_agents/weather_agent/*.py` bên trong thư mục xuất, kèm `__init__.py` rỗng cho các cấp cha)
   — nhờ vậy mọi `from demo_agents.weather_agent import X` trong code gốc vẫn resolve đúng, KHÔNG
   cần rewrite import nào (kỹ thuật rewrite dễ vỡ hơn hẳn so với giữ nguyên cấu trúc). Loại trừ
   `.env` (secret thật), `*.sqlite3*` (rác runtime), `test_*.py`.
3. Sinh `standalone_server.py` NGOÀI package đó — `sys.path.insert()` rồi gọi đúng hàm spec, export
   qua `openai_agents_exporter.build_openai_agent()`, phục vụ `web/chat.html` của package nếu có
   (else trang chat tối giản built-in) + `/api/chat`. Bắt riêng `InputGuardrailTripwireTriggered`/
   `MaxTurnsExceeded` (không rò rỉ chuỗi exception thô ra người dùng cuối), fallback
   `except Exception` chung cho phần còn lại.
4. `--target docker`/`both` sinh thêm `Dockerfile` best-practice — **chỉ sinh, không tự `docker
   build`** (sandbox phát triển tool này không có Docker cài sẵn, không giả vờ đã build/test thật).

Đã verify THẬT (không chỉ đọc code): convert `demo_agents/weather_agent` → chạy
`standalone_server.py` trong 1 process HOÀN TOÀN TÁCH BIỆT (thư mục khác, port khác) → hỏi thời
tiết thật (trả lời đúng qua Open-Meteo) VÀ hỏi câu ngoài phạm vi (guardrail trip đúng, trả message
sạch không lộ chi tiết kỹ thuật).

**Cố ý KHÔNG làm:** không tự động `docker build`/`docker run` (cần Docker, sandbox không có — sinh
Dockerfile đúng best-practice nhưng CHƯA build thử thật, nói rõ trong `README.md` sinh kèm bundle).

## Quy tắc rút ra

- Chỉ nên viết converter cho phần **thực sự trung lập được** (tool logic, schema cơ bản) — đừng cố
  chuyển đổi máy móc những khái niệm framework-specific (guardrail, hooks) khi đích không có tương
  đương native; thà viết lại logic đó riêng cho từng đích còn hơn giả lập sai hành vi.
- Exporter chưa test thật phải **fail loud** (`NotImplementedError` + sơ đồ ánh xạ), không được trả
  về 1 object "trông giống chạy được" nhưng chưa từng chạy qua SDK thật — dễ gây ảo tưởng đã xong.
- Giữ 1 nguồn sự thật (object thật trong `agent.py`) — spec chỉ là VIEW phái sinh, không phải bản
  sao độc lập dễ lệch theo thời gian.

## Origin
- **Source:** [[040826-weather-agent-3-layers]]
- **Code:** `demo_agents/weather_agent/agent_spec.py`, `demo_agents/weather_agent/exporters/`,
  `harness/scripts/monolith_agent_deploy_converter.py`
