---
type: draft
title: first-agent-weather-build
status: proposed
tags: [orca-workflow, output-report]
timestamp: 2026-07-27
task: T-260727-01
---

# 270726-first-agent-weather-build
**Type:** draft
**Status:** proposed
**Tags:** orca-workflow, output-report
**Proposed:** 2026-07-27

## Agent Task Assignment
| Task | Agent | Status |
|------|-------|--------|
| Task 1 — Scaffold `demo_agents/weather_agent/` + manifest | Claude Code | done |
| Task 2 — Implement `agent.py` (model/tools/instructions) | Claude Code | done |
| Task 3 — Unit test offline cho tool | Claude Code | done |
| Task 4 — README + `run.py` + test nhánh lỗi thiếu key | Claude Code | done |

## What
Build agent Python đầu tiên của dự án (weather MVP) hiện thực đúng 3 yếu tố nền tảng — Model, Tools,
Instructions — từ tài liệu đã ingest, dùng OpenAI Agents SDK; 4/4 test tự động pass offline.

## Output
- `demo_agents/weather_agent/agent.py` — `weather_agent` (model `gpt-4o-mini`, tool `get_weather`,
  instructions xử lý edge case "không có dữ liệu").
- `pytest demo_agents/weather_agent/` → **4 passed** (không cần `OPENAI_API_KEY`).
- Ba lỗi thật phát hiện lúc build (không phải giả định trước) và đã sửa ngay:
  1. **Đụng tên package** — SPEC ban đầu đặt `agents/weather_agent/`, nhưng `agents` chính là tên import
     của package `openai-agents` → đổi thư mục container thành `demo_agents/` (ghi rõ trong PLAN, mục
     "Điều chỉnh so với SPEC").
  2. **Python 3.9 thiếu union syntax `X | None`** mà SDK dùng nội bộ → thêm dependency
     `eval_type_backport` vào `requirements.txt`.
  3. **`.lower()` không bỏ dấu tiếng Việt** — key dict thời tiết ban đầu không dấu ("ha noi") không khớp
     input có dấu đã normalize ("hà nội") → sửa key dict có dấu, sửa lại test tương ứng.
  4. **`python demo_agents/weather_agent/run.py` bị `ModuleNotFoundError`** vì Python không tự thêm repo
     root vào `sys.path` khi chạy file trực tiếp → đổi cách gọi chuẩn sang `python -m
     demo_agents.weather_agent.run`, cập nhật README + test tương ứng.
- **Chưa chạy live thật** (gọi LLM qua `Runner.run_sync`) vì sandbox không có `OPENAI_API_KEY` — đã ghi rõ
  giới hạn này trong README, người dùng tự thêm key riêng để chạy full vòng lặp.

## Files
| File | Action |
|------|--------|
| `demo_agents/__init__.py` | created |
| `demo_agents/weather_agent/__init__.py` | created |
| `demo_agents/weather_agent/agent.py` | created |
| `demo_agents/weather_agent/requirements.txt` | created |
| `demo_agents/weather_agent/.env.example` | created |
| `demo_agents/weather_agent/test_tool.py` | created |
| `demo_agents/weather_agent/run.py` | created |
| `demo_agents/weather_agent/test_run_cli.py` | created |
| `demo_agents/weather_agent/README.md` | created |
| `wiki/sources/draft/270726-first-agent-weather.md` | created (SPEC) |
| `html/270726-first-agent-weather-seq.html` | created (sequence diagram) |
| `wiki/sources/draft/270726-first-agent-weather-PLAN.md` | created + edited (3 lần, khớp phát hiện lúc build) |
| `wiki/index.md` | modified |
| `wiki/log.md` | modified |

## Notes
- Invoked via: `/orca-workflow` skill (query → propose → gate qua AskUserQuestion → plan → build, toàn bộ
  do Claude Code, không dispatch CLI khác vì đây là quyết định kiến trúc + code nền tảng đầu tiên của repo).
  Trụ 3 lifecycle: task `T-260727-01` → `dispatched` → (đề xuất set `done` bên dưới).
- **Bỏ qua bước 4 (sync push `rheinmir/setup`)** của mẫu output-report `orca-workflow`: repo này không có
  quan hệ với `rheinmir/setup`, không có skill nào bị sửa trong phiên này — bước đó không áp dụng.
- **Chưa commit** — theo quy tắc an toàn chung (chỉ commit khi user yêu cầu rõ ràng); các lệnh `git commit`
  trong PLAN từng task chưa được chạy, đang chờ user xác nhận.

## Origin
- **Draft:** `wiki/draft/orca/270726-first-agent-weather-build.md`
- **SPEC:** `wiki/sources/draft/270726-first-agent-weather.md`
- **PLAN:** `wiki/sources/draft/270726-first-agent-weather-PLAN.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
