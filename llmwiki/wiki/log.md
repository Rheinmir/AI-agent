# Log

## 2026-07-27 — ingest — huong-dan-xay-dung-agent-thuc-te
- sources/huong-dan-xay-dung-agent-thuc-te.md (created)
- concepts/agent.md (created)
- concepts/workflow.md (created)
- concepts/model-selection.md (created)
- concepts/tools.md (created)
- concepts/instructions.md (created)
- concepts/orchestration.md (created)
- concepts/manager-pattern.md (created)
- concepts/handoff-pattern.md (created)
- concepts/guardrails.md (created)
- concepts/human-in-the-loop.md (created)
- entities/openai-agents-sdk.md (created)
- entities/openai.md (created)
- index.md (updated)
- sources/draft/270726-ingest-agent-guide.md (created)

## 2026-07-27 — ingest — remove-translator-name
- sources/huong-dan-xay-dung-agent-thuc-te.md (edited — bỏ tên dịch giả khỏi câu mô tả)
- sources/draft/270726-ingest-agent-guide.md (edited — bỏ tên dịch giả khỏi mô tả What)

## 2026-07-27 — query — 3 yếu tố nền tảng quan trọng nhất để xây agent đầu tiên
- Trả lời: Model, Tools, Instructions ([[agent]] §Ba thành phần nền tảng, chi tiết ở [[model-selection]], [[tools]], [[instructions]]).
- Không tạo trang mới — câu trả lời đã có sẵn nguyên vẹn trong wiki hiện tại (không phát hiện insight mới).

## 2026-07-27 — propose — first-agent-weather
- sources/draft/270726-first-agent-weather.md (created — SPEC, task T-260727-01, status proposed)
- html/270726-first-agent-weather-seq.html (created — 4 diagram-box, docs-site-macos glass style)
- index.md (updated)

## 2026-07-27 — plan — first-agent-weather-PLAN
- sources/draft/270726-first-agent-weather-PLAN.md (created — 4 task thi hành, đổi tên `agents/` → `demo_agents/` để tránh đụng tên với package `agents` của openai-agents SDK)
- index.md (updated)

## 2026-07-27 — orca-workflow — first-agent-weather-build
- demo_agents/ (created — agent.py, run.py, test_tool.py, test_run_cli.py, README.md, requirements.txt, .env.example)
- sources/draft/270726-first-agent-weather-PLAN.md (edited 3 lần — sửa theo lỗi thật phát hiện lúc build: package name clash, Python 3.9 union syntax, dấu tiếng Việt, `-m` invocation)
- draft/orca/270726-first-agent-weather-build.md (created — output report, 4/4 test pass)
- index.md (updated)

## 2026-08-01 — docs-site-macos — weather-agent-docs
- html/010826-first-agent-weather-docs.html (created — 6 section glass-style docs cho weather agent MVP)
- sources/draft/010826-weather-agent-docs.md (created — output report)
- index.md (updated)

## 2026-08-01 — wikieval — weather-agent-eval
- harness/scripts/wikieval.py, harness/wikieval.config.yaml (created — copy từ harness template global)
- wiki/sources/evals/weather-known-city.md, weather-case-insensitive.md, weather-unknown-city.md (created)
- harness/evals/weather-agent-outputs.json, harness/metrics/eval-baseline.json (created — 3/3 decided-passing)
- draft/orca/010826-weather-agent-eval.md (created — output report)
- index.md (updated)

<!-- log:auto:start -->

### 🤖 Log tự-động (code-logger, không do agent ghi)

| Thời điểm | Event | Chi tiết |
|---|---|---|
| 2026-07-27 09:58:50 | `file.write` | llmwiki/wiki/concepts/human-in-the-loop.md · tool=Write · session=bdb1a446 · actor=agent · prev=5a20c359bbf66e3508448904 |
| 2026-07-27 09:59:02 | `file.write` | llmwiki/wiki/entities/openai-agents-sdk.md · tool=Write · session=bdb1a446 · actor=agent · prev=715d12cf98cb3cbc5f1bce6a |
| 2026-07-27 09:59:07 | `file.write` | llmwiki/wiki/entities/openai.md · tool=Write · session=bdb1a446 · actor=agent · prev=099033040c7312b44d4cd72de5098dee604 |
| 2026-07-27 09:59:13 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=bdb1a446 · actor=agent · prev=79a1f1a909045d2c7252aa0286373d3525d2e7418e81de |
| 2026-07-27 09:59:17 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=bdb1a446 · actor=agent · prev=9348d7fdbfe7f08c84ad68954af758e88bc05d1a8af20e84 |
| 2026-07-27 09:59:30 | `file.write` | llmwiki/wiki/sources/draft/270726-ingest-agent-guide.md · tool=Write · session=bdb1a446 · actor=agent · prev=c110d82bcab |
| 2026-07-27 10:00:19 | `file.write` | llmwiki/wiki/sources/huong-dan-xay-dung-agent-thuc-te.md · tool=Edit · session=bdb1a446 · actor=agent · prev=3517b779f0c |
| 2026-07-27 10:00:24 | `file.write` | llmwiki/wiki/sources/draft/270726-ingest-agent-guide.md · tool=Edit · session=bdb1a446 · actor=agent · prev=add97b3de822 |
| 2026-07-27 10:00:39 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=bdb1a446 · actor=agent · prev=20c7fc1d697b585470053b5462201d7ad3ec2b236141b61c |
| 2026-07-27 10:03:06 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=bdb1a446 · actor=agent · prev=2ac354db0609b3815e33dc23dbfd5bce4ae27dabd251ac56 |
| 2026-07-27 10:04:21 | `task.new` |  · task=T-260727-01 · title=Build first agent — weather MVP (model+tools+instructions) · state=proposed · actor=agent ·  |
| 2026-07-27 10:06:30 | `file.write` | llmwiki/wiki/sources/draft/270726-first-agent-weather.md · tool=Write · session=bdb1a446 · actor=agent · prev=eddc86610e |
| 2026-07-27 10:06:37 | `file.write` | llmwiki/wiki/sources/draft/270726-first-agent-weather.md · tool=Edit · session=bdb1a446 · actor=agent · prev=7605a2443b9 |
| 2026-07-27 10:08:41 | `file.write` | llmwiki/html/270726-first-agent-weather-seq.html · tool=Write · session=bdb1a446 · actor=agent · prev=c8a441b47786666671 |
| 2026-07-27 10:09:17 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=bdb1a446 · actor=agent · prev=e4bf06141af548ff354a98b3e48eea6840100c3a06dceb |
| 2026-07-27 10:09:24 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=bdb1a446 · actor=agent · prev=d789926bde7bd17cd299a10d75ae8d521aba3168d853e3b4 |
| 2026-07-27 10:11:50 | `task.set` |  · task=T-260727-01 · state=approved · note=gate: user duyệt qua AskUserQuestion · actor=agent · prev=9fbf878ad6e927f078 |
| 2026-07-27 10:14:31 | `file.write` | llmwiki/wiki/sources/draft/270726-first-agent-weather-PLAN.md · tool=Write · session=bdb1a446 · actor=agent · prev=8db2d |
| 2026-07-27 10:14:36 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=bdb1a446 · actor=agent · prev=e6e6c099c150af91cba22b007c7ed4186541f25ddd7320 |
| 2026-07-27 10:14:45 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=bdb1a446 · actor=agent · prev=c746ce1540b518604ebb9f869bd1b63653633e1f3ab6bc5f |
| 2026-07-27 10:17:14 | `file.write` | llmwiki/wiki/sources/draft/270726-first-agent-weather-PLAN.md · tool=Edit · session=bdb1a446 · actor=agent · prev=47ff4e |
| 2026-07-27 10:17:24 | `file.write` | llmwiki/wiki/sources/draft/270726-first-agent-weather-PLAN.md · tool=Edit · session=bdb1a446 · actor=agent · prev=68f71d |
| 2026-07-27 10:17:31 | `file.write` | llmwiki/wiki/sources/draft/270726-first-agent-weather-PLAN.md · tool=Edit · session=bdb1a446 · actor=agent · prev=c89674 |
| 2026-07-27 10:17:39 | `file.write` | llmwiki/wiki/sources/draft/270726-first-agent-weather-PLAN.md · tool=Edit · session=bdb1a446 · actor=agent · prev=93047f |
| 2026-07-27 10:18:49 | `file.write` | llmwiki/wiki/sources/draft/270726-first-agent-weather-PLAN.md · tool=Edit · session=bdb1a446 · actor=agent · prev=46005f |
| 2026-07-27 10:19:35 | `file.write` | llmwiki/wiki/draft/orca/270726-first-agent-weather-build.md · tool=Write · session=bdb1a446 · actor=agent · prev=fa0881e |
| 2026-07-27 10:19:41 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=bdb1a446 · actor=agent · prev=9324c0a7e596512e74272c785d48826ed86fba586609ab |
| 2026-07-27 10:19:47 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=bdb1a446 · actor=agent · prev=9bc4a7800aeab365a16f2e9ec980db3d9cab3d2f4014e697 |
| 2026-07-27 10:19:51 | `task.set` |  · task=T-260727-01 · state=dispatched · note=Claude Code tự thi hành 4 task trong phiên · actor=agent · prev=9fce4c64d2 |
| 2026-07-27 10:19:51 | `task.set` |  · task=T-260727-01 · state=done · note=4/4 test pass, chưa commit — chờ user · actor=agent · prev=099efd3171d13ee45b470 |
| 2026-08-01 13:40:30 | `file.write` | llmwiki/html/010826-first-agent-weather-docs.html · tool=Write · session=bdb1a446 · actor=agent · prev=03c5f2e9da4ce6d47 |
| 2026-08-01 13:40:41 | `file.write` | llmwiki/wiki/sources/draft/010826-weather-agent-docs.md · tool=Write · session=bdb1a446 · actor=agent · prev=cf96931fec9 |
| 2026-08-01 13:40:48 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=bdb1a446 · actor=agent · prev=1ef2cd13a7f309ad1f2a9885ac0596c43d88cc39d4037b |
| 2026-08-01 13:40:52 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=bdb1a446 · actor=agent · prev=3142983effe60e4b9bef2a27fcc7b56a9a863821bf3383f5 |
| 2026-08-01 13:41:58 | `file.write` | llmwiki/wiki/sources/evals/weather-known-city.md · tool=Write · session=bdb1a446 · actor=agent · prev=019a4d41cb31f85012 |
| 2026-08-01 13:42:03 | `file.write` | llmwiki/wiki/sources/evals/weather-case-insensitive.md · tool=Write · session=bdb1a446 · actor=agent · prev=e6c2da95972a |
| 2026-08-01 13:42:08 | `file.write` | llmwiki/wiki/sources/evals/weather-unknown-city.md · tool=Write · session=bdb1a446 · actor=agent · prev=57c4a2bd058279c6 |
| 2026-08-01 13:42:36 | `file.write` | llmwiki/wiki/draft/orca/010826-weather-agent-eval.md · tool=Write · session=bdb1a446 · actor=agent · prev=85f22dd261cdcd |
| 2026-08-01 13:42:39 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=bdb1a446 · actor=agent · prev=b77beb823a12256e681e2199db701f2c732b69962107c2 |
| 2026-08-01 13:42:43 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=bdb1a446 · actor=agent · prev=40f6d39f84cf3e352516007cdd85beddadd2f30a32ef4d6a |

<!-- log:auto:end -->
