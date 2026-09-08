---
type: draft
title: devops-agent-mvp
status: proposed
tags: [orca-workflow, output-report]
timestamp: 2026-08-04
task: T-260727-01
---

# 040826-devops-agent-mvp
**Type:** draft
**Status:** proposed
**Tags:** orca-workflow, output-report
**Proposed:** 2026-08-04

## Agent Task Assignment
| Task | Agent | Status |
|------|-------|--------|
| Scaffold `demo_agents/devops_agent/` (Model + Tools + Instructions + guardrail) | Claude Code | done |
| Cheatsheet cục bộ (Data Collector): k8s, container-health, deployment-patterns, env-promotion, CI/CD | Claude Code | done |
| Test hermetic + verify live (câu hỏi hợp lệ + guardrail trip) | Claude Code | done |
| `agent_spec.py` + `exporters/` để tái dùng monolith-agent-deploy-converter làm chat UI test | Claude Code | done (SAI công cụ — sửa lại bên dưới) |
| Reuse `weather_agent/web/chat.html` + `chatdemo.py` cho chat UI test thật (thay converter) | Claude Code | done |

## What
Build agent DevOps thứ 2 của repo (sau `weather_agent`) từ `llmwiki/raw/devops-agent.md`, theo đúng
scope người dùng yêu cầu tường minh: **"hiện tại chưa cần connect tới đâu mà cần hỏi đáp thuần về
kiến thức devops trước"**. Raw file gốc nêu nhiều mở rộng (Grafana agent thật tham khảo
`pranshuparmar/witr`, k8s API thật, MCP pipeline trigger, multi-agent "squad" tham khảo
`bradygaster/squad`) — TẤT CẢ đều CHỦ Ý CHƯA làm, chỉ ghi lại trong README như việc sau.

## Output
- `demo_agents/devops_agent/agent.py` — `devops_agent`, 1 tool cục bộ `get_cheatsheet` (không gọi ra
  ngoài, khác `weather_agent` có tool gọi Open-Meteo thật), INSTRUCTIONS khai báo rõ giới hạn "CHƯA
  kết nối hệ thống thật" thay vì để agent giả vờ có khả năng.
- `demo_agents/devops_agent/guardrails.py` — `devops_scope_guardrail` (input guardrail thật, cùng
  pattern đã kiểm chứng ở `weather_agent/guardrails.py`), phạm vi RỘNG hơn (kiến thức DevOps nói
  chung, không chỉ 1 tool), thêm nhánh chặn MỚI: yêu cầu **thực thi hành động trên hệ thống thật**
  (vd "restart pod X giúp tôi") — verify SỐNG đã trip đúng.
- `demo_agents/devops_agent/data_collector.py` — 5 cheatsheet chủ đề (kubernetes, container-health,
  deployment-patterns, env-promotion, cicd-pipeline) + alias thông dụng (k8s, canary, ci/cd...).
- `pytest demo_agents/devops_agent` → **18 passed** (hermetic, mock `Runner.run`/network); toàn repo
  `pytest demo_agents/ harness/scripts` → **101 passed** (83 cũ + 18 mới), không có regression.
- Verify SỐNG (DeepSeek key thật): hỏi "Sự khác nhau giữa liveness và readiness probe?" → agent gọi
  `get_cheatsheet('container-health')`, trả lời đúng nội dung cheatsheet + diễn giải thêm; hỏi "Restart
  giúp tôi pod nginx trên cluster production" và "Công thức nấu phở bò thế nào?" → guardrail trip cả
  2, đúng thiết kế.
- Người dùng hỏi "chạy trên port nào để test thử" (đang nghĩ tới chat UI như weather_agent) rồi tự
  chỉ ra: monolith-agent-deploy-converter (đã build ở phiên trước) vốn đã sinh sẵn 1 trang chat tối
  giản BUILT-IN khi package không có `web/chat.html` riêng — không cần viết `chatdemo.py` mới. Thêm
  `demo_agents/devops_agent/agent_spec.py` (`build_devops_agent_spec`) + `exporters/__init__.py` +
  `exporters/openai_agents_exporter.py` (copy nguyên 2 file generic từ weather_agent, không đổi logic)
  để converter tìm được spec, rồi chạy `harness/scripts/monolith_agent_deploy_converter.py --src
  demo_agents/devops_agent --target python --port 8768` → convert thành công, start
  `standalone_server.py` thật (background, PID riêng) → verify SỐNG qua `/api/chat` (body
  `{"question", "session_id"}`): câu hỏi canary deployment trả lời đúng từ cheatsheet, câu hỏi nấu ăn
  bị guardrail chặn đúng; trang chủ `GET /` trả về chat UI built-in (không phải `web/chat.html`, vì
  devops_agent chưa có file đó) render đúng HTTP 200.
- **Sửa lại ngay sau đó:** người dùng phản hồi thẳng trang built-in "mất công mà xấu xí" — đúng,
  đây là chọn SAI công cụ (converter sinh cho mục đích ĐÓNG GÓI triển khai, không phải để có UI đẹp
  test cục bộ). Dừng bundle cũ, thay bằng `demo_agents/devops_agent/web/chat.html` (COPY NGUYÊN VĂN
  từ `weather_agent/web/chat.html`, không đổi 1 token CSS — chỉ đổi nội dung/branding/câu hỏi mẫu/
  localStorage key) + `demo_agents/devops_agent/chatdemo.py` (mirror `weather_agent/chatdemo.py`,
  bớt phần harness/dashboard chưa có, tự bắt `InputGuardrailTripwireTriggered` trả đúng
  `OUT_OF_SCOPE_MESSAGE` riêng). Verify SỐNG đủ `/`, `/api/sessions`, `/api/chat`, `/api/history`,
  `/api/reset` trên port 8768 — xem entry log riêng `devops-agent-reuse-weather-chat-ui`.

## Files
| File | Action |
|------|--------|
| `demo_agents/devops_agent/__init__.py` | created |
| `demo_agents/devops_agent/model_provider.py` | created (copy pattern từ weather_agent, generic) |
| `demo_agents/devops_agent/data_collector.py` | created |
| `demo_agents/devops_agent/guardrails.py` | created |
| `demo_agents/devops_agent/agent.py` | created |
| `demo_agents/devops_agent/run.py` | created |
| `demo_agents/devops_agent/requirements.txt` | created |
| `demo_agents/devops_agent/.env.example` | created |
| `demo_agents/devops_agent/README.md` | created |
| `demo_agents/devops_agent/test_data_collector.py` | created |
| `demo_agents/devops_agent/test_guardrails.py` | created |
| `demo_agents/devops_agent/test_tool.py` | created |
| `demo_agents/devops_agent/test_run_cli.py` | created |
| `demo_agents/devops_agent/agent_spec.py` | created |
| `demo_agents/devops_agent/exporters/__init__.py` | created (copy generic từ weather_agent) |
| `demo_agents/devops_agent/exporters/openai_agents_exporter.py` | created (copy generic từ weather_agent) |
| `demo_agents/devops_agent/web/chat.html` | created (copy nguyên văn từ weather_agent, đổi nội dung) |
| `demo_agents/devops_agent/chatdemo.py` | created (mirror weather_agent/chatdemo.py) |
| `wiki/index.md`, `wiki/log.md` | updated |

## Notes
- Invoked via: yêu cầu trực tiếp của người dùng, đọc `llmwiki/raw/devops-agent.md` trước khi build,
  KHÔNG fetch 2 repo GitHub được nhắc tới (`pranshuparmar/witr`, `bradygaster/squad`) — chỉ là tham
  khảo cho việc SAU (kết nối Grafana thật, kiến trúc multi-agent), không cần cho MVP hỏi đáp thuần.
- **Cố ý CHƯA làm** (đối xứng với các layer weather_agent có, nhưng thêm dần theo yêu cầu, không phải
  thiếu sót): Memory dài hạn, Harness tường minh (max_turns/retry), Monitoring/hooks + `/monitor`
  `/evaluate`. Tool `get_cheatsheet` KHÔNG gọi ra ngoài (khác `get_weather` của weather_agent) —
  đúng yêu cầu "chưa cần connect tới đâu". `agent_spec.py`/`exporters` giữ lại (đúng mục đích gốc:
  cho phép dùng `monolith-agent-deploy-converter` SAU NÀY khi thật sự cần đóng gói triển khai nơi
  khác) — nhưng KHÔNG dùng cho việc test UI cục bộ (bài học rút ra ở bugfix ngay sau).
- **Bài học công cụ đúng việc:** `monolith-agent-deploy-converter` sinh chat UI TỐI GIẢN (không
  sidebar/session-list) vì mục đích của nó là app chat CHUẨN ĐỂ ĐÓNG GÓI đem deploy nơi khác — không
  phải "cách nhanh để có UI đẹp test tại chỗ". Khi agent ĐÃ có sẵn 1 UI hoàn thiện dùng chung được
  (`weather_agent/web/chat.html` là self-contained, không hardcode gì riêng cho weather ngoài nội
  dung text), copy + đổi nội dung + viết `chatdemo.py` mirror là đúng hướng hơn hẳn.
- Guardrail của devops_agent có 1 nhánh KHÔNG có ở weather_agent: chặn yêu cầu thực thi hành động
  thật (restart pod, chạy lệnh, trigger pipeline) — cần thiết vì agent DevOps dễ bị hiểu nhầm là có
  quyền hành động, phải chặn rõ ràng thay vì để model tự "xin lỗi" không nhất quán.
- **Chưa commit** — theo quy tắc an toàn chung, chờ user xác nhận rõ ràng.

## Origin
- **Draft:** `wiki/draft/orca/040826-devops-agent-mvp.md`
- **Raw source:** `llmwiki/raw/devops-agent.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
