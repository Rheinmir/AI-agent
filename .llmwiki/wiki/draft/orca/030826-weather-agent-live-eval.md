---
type: draft
title: weather-agent-live-eval
status: proposed
tags: [wikieval, output-report]
timestamp: 2026-08-03
task: T-260727-01
---

# 030826-weather-agent-live-eval
**Type:** draft
**Status:** proposed
**Tags:** wikieval, output-report
**Proposed:** 2026-08-03

## What
Bổ sung eval CẤP AGENT (không chỉ cấp tool) cho weather agent — phản hồi trực tiếp cho nhận xét
trước đó "evaluation của dự án chứ đâu phải của wiki": 3 golden cũ chỉ chạy `_get_weather_impl()`
(hàm Python thuần), không hề đi qua Model/Instructions thật. 4 golden mới chạy
`Runner.run_sync(weather_agent, ...)` THẬT — gọi DeepSeek thật, qua đúng luồng agent thật.

## Output
- 4 golden mới, tag `agent-level`, dưới `llmwiki/wiki/sources/evals/`:
  - `agent-known-city` — hỏi tự nhiên, agent tự gọi tool + trả lời có nhiệt độ hợp lệ
  - `agent-unknown-city-guardrail` — agent tự áp guardrail "không bịa số liệu" (kiểm chứng
    `INSTRUCTIONS` có thật sự chặn được hành vi model, không chỉ tool trả đúng marker)
  - `agent-capability-declaration` — agent tự khai báo năng lực đúng thật (nhắc Open-Meteo cụ thể,
    không trả lời chung chung)
  - `agent-multiturn-memory` — **test được cả `SQLiteSession`**, thứ hoàn toàn không thể test ở
    cấp tool: gọi 2 lượt cùng session (Hà Nội → "còn Hạ Long thì so với đó"), chỉ chấm lượt 2,
    assert phải nhớ được "đó" = Hà Nội mà không cần nhắc lại tên
- Output thật lấy từ 4 lần gọi `Runner.run_sync` thật (DeepSeek), không gõ tay — ví dụ
  `agent-multiturn-memory`: agent tự dựng bảng so sánh Hà Nội (28.2°C) vs Hạ Long (29.1°C) đúng cả
  2 thành phố dù lượt 2 không hề nhắc "Hà Nội".
- `python3 harness/scripts/wikieval.py --outputs harness/evals/weather-agent-combined-outputs.json --write-baseline`
  → **7/7 decided-passing** (3 golden tool-level cũ + 4 golden agent-level mới, cùng 1 baseline).

## Files
| File | Action |
|------|--------|
| `llmwiki/wiki/sources/evals/agent-known-city.md` | created |
| `llmwiki/wiki/sources/evals/agent-unknown-city-guardrail.md` | created |
| `llmwiki/wiki/sources/evals/agent-capability-declaration.md` | created |
| `llmwiki/wiki/sources/evals/agent-multiturn-memory.md` | created |
| `harness/evals/weather-agent-live-outputs.json` | created |
| `harness/evals/weather-agent-combined-outputs.json` | created |
| `harness/metrics/eval-baseline.json` | regenerated (7 goldens) |
| `wiki/index.md`, `wiki/log.md` | modified |

## Notes
- Invoked via: yêu cầu "bổ sung đi" của người dùng sau đề nghị harness R10 docs-gate, ưu tiên đúng
  chỗ hổng đã bị chỉ ra trước đó (eval cấp tool ≠ eval cấp agent).
- Gọi DeepSeek thật 4 lần (tốn API call thật, không phải mock) — đây là đánh đổi có chủ đích để
  bằng chứng phản ánh đúng hành vi model thật, không phải giả định.
- Tier-3 LLM-judge vẫn quarantined (`verified:false`) — không cần cho 7 golden này, tất cả quyết
  định được bằng tier-1 deterministic asserts.

## Origin
- **Draft:** `wiki/draft/orca/030826-weather-agent-live-eval.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
