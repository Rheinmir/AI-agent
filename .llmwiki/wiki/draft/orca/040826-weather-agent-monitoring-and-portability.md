---
type: draft
title: weather-agent-monitoring-and-portability
status: proposed
tags: [orca-workflow, output-report]
timestamp: 2026-08-04
task: T-260727-01
---

# 040826-weather-agent-monitoring-and-portability
**Type:** draft
**Status:** proposed
**Tags:** orca-workflow, output-report
**Proposed:** 2026-08-04

## Agent Task Assignment
| Task | Agent | Status |
|------|-------|--------|
| Lifecycle hooks thật (monitoring hành vi agent) | Claude Code | done |
| AgentSpec trung lập + exporter openai-agents chạy thật | Claude Code | done |
| Exporter stub LangChain/LangGraph/Claude Agent SDK/Azure AI | Claude Code | done |

## What
Người dùng hỏi "cần có gì để monitoring hành vi agent — LangChain/LangGraph có giải được không,
thêm /monitor /evaluate" rồi làm rõ hướng: KHÔNG đổi framework (rewrite toàn bộ), mà (1) dùng
lifecycle hooks có sẵn của SDK đang chạy để log hành vi, và (2) 1 "bộ converter chuyển đổi linh
hoạt giữa các cấu trúc" — xác nhận qua AskUserQuestion 2 vòng: cách tiếp cận "định nghĩa 1 lần, xuất
ra nhiều framework" (không phải converter đọc-ngược 2 chiều từ code thật), và hook nghĩa là
lifecycle hooks (`on_tool_start`/`on_tool_end`...), thêm cả kiến trúc Microsoft Azure vào danh sách
đích cần hỗ trợ.

## Output
- **Monitoring (`monitoring.py`):** `WeatherAgentHooks(AgentHooks)` — hook THẬT của Agents SDK,
  gắn qua `Agent(hooks=...)`. Mỗi sự kiện (agent_start, llm_start, tool_start, tool_end, llm_end,
  agent_end) ghi vào `monitoring.sqlite3` local qua `log_event()`, đọc lại qua `recent_events()`.
  Verify thật: gọi `Runner.run_sync` qua HTTP `/api/chat` thật, xác nhận đủ 7 sự kiện ghi đúng thứ
  tự, kể cả 1 lần Open-Meteo trả lỗi tạm thời (network blip thật, không phải giả lập) — hooks vẫn
  ghi đúng `tool_end` với `NO_DATA`, chứng minh monitoring bắt được cả case lỗi thật.
- **Agent portability (`agent_spec.py` + `exporters/`):** `AgentSpec` trung lập dựng TỪ object thật
  trong `agent.py`/`guardrails.py` (không định nghĩa lại logic — 1 nguồn sự thật). Exporter
  `openai_agents_exporter.py` CHẠY THẬT: dựng lại `Agent` từ spec, verify round-trip bằng cách gọi
  trực tiếp tool của agent DỰNG LẠI, xác nhận trả đúng kết quả như tool gốc. 4 exporter còn lại
  (`langchain`, `langgraph`, `claude_agent_sdk`, `azure_ai`) là STUB có sơ đồ ánh xạ field-theo-field
  chi tiết trong docstring, `raise NotImplementedError` — không giả vờ chạy được khi chưa cài SDK
  tương ứng.
- **Quyết định phạm vi quan trọng:** từ chối converter 2 chiều đầy đủ (đọc code LangChain/LangGraph
  thật rồi suy ngược ra spec) — quá lớn, mỗi framework có mô hình khác hẳn nhau (LangGraph là graph/
  state-machine, không phải agent+tool phẳng). Chọn "định nghĩa 1 lần, xuất N chiều" — khả thi, đã
  chứng minh được với đích thật (openai-agents), có sơ đồ rõ ràng cho 4 đích còn lại.
- **Tài liệu mới:** `wiki/concepts/agent-portability.md` — giải thích kỹ thuật + bảng ánh xạ nhanh
  4 framework, quy tắc rút ra (chỉ convert phần trung lập được, fail loud khi chưa test thật, giữ 1
  nguồn sự thật).

## Files
| File | Action |
|------|--------|
| `demo_agents/weather_agent/monitoring.py`, `test_monitoring.py` | created |
| `demo_agents/weather_agent/agent_spec.py`, `test_agent_spec.py` | created |
| `demo_agents/weather_agent/exporters/__init__.py` | created |
| `demo_agents/weather_agent/exporters/openai_agents_exporter.py` | created |
| `demo_agents/weather_agent/exporters/langchain_exporter.py` | created |
| `demo_agents/weather_agent/exporters/langgraph_exporter.py` | created |
| `demo_agents/weather_agent/exporters/claude_agent_sdk_exporter.py` | created |
| `demo_agents/weather_agent/exporters/azure_ai_exporter.py` | created |
| `demo_agents/weather_agent/agent.py` | edited (wire `hooks=WeatherAgentHooks()`) |
| `demo_agents/weather_agent/README.md` | edited (2 hàng mới) |
| `.gitignore` | edited (2 dòng mới cho sqlite runtime state) |
| `wiki/concepts/agent-portability.md` | created |
| `wiki/concepts/agent-7-layers.md` | edited (link chéo) |
| `wiki/index.md`, `wiki/log.md` | updated |

## Notes
- Invoked via: chuỗi hỏi-đáp trực tiếp của người dùng, xác nhận phạm vi qua AskUserQuestion 2 lần
  trước khi viết code (tránh đoán sai 1 khối lượng công việc lớn).
- pytest 42 → 50 (8 test mới), tất cả hermetic — monitoring test dùng `tmp_path` cô lập DB, exporter
  test mock network cho tool thật + assert 4 stub raise đúng `NotImplementedError`.
- Chưa làm: điền code thật cho 4 exporter stub (cần cài SDK tương ứng — không thêm dependency chỉ để
  "trông xong"), chưa có `/monitor` CLI/skill đọc `monitoring.sqlite3` ra bảng tóm tắt (mới có
  `recent_events()` hàm trần) — có thể làm tiếp nếu người dùng cần.

## Origin
- **Draft:** `wiki/draft/orca/040826-weather-agent-monitoring-and-portability.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
