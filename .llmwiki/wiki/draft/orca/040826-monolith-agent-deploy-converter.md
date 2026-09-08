---
type: draft
title: monolith-agent-deploy-converter
status: proposed
tags: [orca-workflow, output-report]
timestamp: 2026-08-04
task: T-260727-01
---

# 040826-monolith-agent-deploy-converter
**Type:** draft
**Status:** proposed
**Tags:** orca-workflow, output-report
**Proposed:** 2026-08-04

## Agent Task Assignment
| Task | Agent | Status |
|------|-------|--------|
| CLI converter: agent_spec.py → app chat standalone | Claude Code | done |
| Verify sống end-to-end (process tách biệt, hỏi thật) | Claude Code | done |

## What
Người dùng: "tạo agent theo dạng có thể bỏ folder src vào 1 tool monolith-agent-deploy-converter để
có thể convert ra 1 app agentic dạng chat standalone và bốc đi triển khai bất kỳ đâu được". Xác nhận
phạm vi qua AskUserQuestion trước khi build (2 câu hỏi: đích đóng gói — cả Python bundle lẫn Docker,
người dùng chọn lúc convert; quy ước input — dựa trên `AgentSpec`/`agent_spec.py` vừa xây ở bugfix
trước, không đoán cấu trúc code tự do).

## Output
- `harness/scripts/monolith_agent_deploy_converter.py` — CLI `--src <folder> --out <dir> --target
  {python,docker,both}` (không mặc định target). Tìm đúng 1 hàm `build_*_agent_spec` trong
  `<src>/agent_spec.py`, copy toàn bộ cây file GIỮ NGUYÊN cấu trúc package gốc (không rewrite
  import), loại `.env`/`*.sqlite3*`/`test_*.py`, sinh `standalone_server.py` (bắt riêng
  `InputGuardrailTripwireTriggered`/`MaxTurnsExceeded`, không rò rỉ exception thô) + `README.md` +
  `requirements.txt` + (nếu chọn docker/both) `Dockerfile`+`.dockerignore` best-practice.
- **Cố ý KHÔNG làm:** không tự `docker build`/`docker run` — sandbox này không có Docker cài sẵn,
  chỉ sinh Dockerfile đúng chuẩn, không giả vờ đã build/test thật qua Docker.
- 3 bug thật gặp khi build (không phải giả định, phát hiện qua verify sống):
  1. Load `agent_spec.py` bằng `spec_from_file_location` không đặt repo root lên `sys.path` trước
     → vỡ vì module tự `from demo_agents.weather_agent import agent` (absolute import) — sửa bằng
     `importlib.import_module` qua dotted package path đúng.
  2. Filter loại trừ chỉ khớp đuôi `.sqlite3` chính xác, bỏ sót sidecar `*.sqlite3-wal`/`-shm` —
     đổi sang khớp substring.
  3. `standalone_server.py` bản đầu bắt lỗi guardrail-trip bằng `except Exception` chung, rò rỉ
     nguyên văn thông báo exception kỹ thuật ra người dùng cuối — phát hiện khi thật sự gọi
     `/api/chat` với câu hỏi ngoài phạm vi trên bundle đã convert, sửa bằng except riêng.
- Verify SỐNG: convert `demo_agents/weather_agent` → chạy `standalone_server.py` thật trong 1
  PROCESS TÁCH BIỆT (thư mục `/tmp`, port khác 8767 hoàn toàn) → hỏi thời tiết Hà Nội thật (Open-
  Meteo trả đúng) VÀ hỏi câu ngoài phạm vi (guardrail trip, message sạch).

## Files
| File | Action |
|------|--------|
| `harness/scripts/monolith_agent_deploy_converter.py` | created |
| `harness/scripts/test_monolith_agent_deploy_converter.py` | created |
| `wiki/concepts/agent-portability.md` | edited |
| `wiki/index.md`, `wiki/log.md` | updated |

## Notes
- Invoked via: yêu cầu trực tiếp của người dùng, xác nhận phạm vi qua AskUserQuestion 1 vòng (2 câu
  hỏi) trước khi viết code — tránh đoán sai 1 tool có phạm vi rộng (áp dụng cho MỌI agent theo quy
  ước, không riêng weather_agent).
- Tool tổng quát — không hardcode gì riêng cho weather_agent, verify test dùng weather_agent làm ví
  dụ THẬT (không fixture giả) vì đó là agent duy nhất trong repo hiện có `agent_spec.py` đúng quy
  ước.
- pytest: 71 (weather_agent) + 12 (converter) = 83/83 passed.

## Origin
- **Draft:** `wiki/draft/orca/040826-monolith-agent-deploy-converter.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
