---
type: draft
title: weather-agent-eval
status: proposed
tags: [wikieval, output-report]
timestamp: 2026-08-01
task: T-260727-01
---

# 010826-weather-agent-eval
**Type:** draft
**Status:** proposed
**Tags:** wikieval, output-report
**Proposed:** 2026-08-01

## What
Thêm eval/regression gate cho `_get_weather_impl` (weather agent) bằng wikieval — 3 golden khớp đúng
3 test case đã có trong `test_tool.py`, chạy cascade tier-1 (deterministic asserts) từ output thật của
hàm, ghi baseline để CI/agent sau không thể âm thầm phá vỡ hành vi.

## Output
- 3 golden mới dưới `llmwiki/wiki/sources/evals/`: `weather-known-city`, `weather-case-insensitive`,
  `weather-unknown-city` — bao đúng 3 hành vi: tra đúng thành phố có dấu, case/space-insensitive, và
  guardrail `NO_DATA:<city>` khi không có dữ liệu.
- Copy engine `harness/scripts/wikieval.py` + `harness/wikieval.config.yaml` từ harness template global
  vào project (project trước đó chưa có sẵn — lần đầu dùng wikieval trong repo này).
- Candidate output lấy từ **hàm thật** `_get_weather_impl` (không gõ tay), ghi ở
  `harness/evals/weather-agent-outputs.json`.
- `python3 harness/scripts/wikieval.py --outputs harness/evals/weather-agent-outputs.json --write-baseline`
  → **3/3 decided-passing**, baseline ghi ở `harness/metrics/eval-baseline.json`.
- `--check` xác nhận chạy lại không có regression (exit 0).

## Files
| File | Action |
|------|--------|
| `harness/scripts/wikieval.py` | created (copy từ harness template global) |
| `harness/wikieval.config.yaml` | created (copy từ harness template global, `verified: false`) |
| `harness/evals/weather-agent-outputs.json` | created |
| `harness/metrics/eval-baseline.json` | created (baseline) |
| `llmwiki/wiki/sources/evals/weather-known-city.md` | created |
| `llmwiki/wiki/sources/evals/weather-case-insensitive.md` | created |
| `llmwiki/wiki/sources/evals/weather-unknown-city.md` | created |
| `wiki/index.md` | modified |
| `wiki/log.md` | modified |

## Notes
- Invoked via: skill `wikieval` (không có trong danh sách skill khả dụng của phiên — đọc trực tiếp
  `~/.claude/skills/wikieval/SKILL.md` và làm theo hướng dẫn thủ công).
- Tier-3 LLM-rubric judge vẫn quarantined (`verified: false`) — không cần cho 3 golden này vì cả 3 đều
  quyết định được bằng tier-1 deterministic asserts, không cần model.
- Goldens khớp 1-1 với `test_tool.py` đã có (test framework khác, mục đích khác: pytest chạy lúc dev,
  wikieval là regression gate độc lập đọc trực tiếp từ wiki — cả hai cùng tồn tại, không thay thế nhau).

## Origin
- **Draft:** `wiki/draft/orca/010826-weather-agent-eval.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
