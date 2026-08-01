---
type: draft
title: 270726-ingest-agent-guide
tags: [ingest, output-report]
timestamp: 2026-07-27
---

# 270726-ingest-agent-guide
**Type:** draft
**Status:** proposed
**Tags:** ingest, output-report
**Proposed:** 2026-07-27

## What
Chưng cất tài liệu "Hướng dẫn xây dựng Agent thực tế" (OpenAI, bản dịch tiếng Việt) thành 1 trang
source, 10 trang concept và 2 trang entity trong wiki, có wikilink chéo và cập nhật index/log.

## Output
- Trích xuất toàn văn 34 trang PDF (pymupdf, do wiki chưa có poppler cho pipeline Read PDF gốc).
- Tạo trang source tổng hợp liên kết tới toàn bộ concept/entity con.
- Tạo 10 trang concept: agent, workflow, model-selection, tools, instructions, orchestration,
  manager-pattern, handoff-pattern, guardrails, human-in-the-loop.
- Tạo 2 trang entity: openai, openai-agents-sdk (ví dụ code SDK dùng xuyên suốt tài liệu).
- Cập nhật wiki/index.md (14 dòng mới) và wiki/log.md.

## Files
| File | Action |
|------|--------|
| `wiki/sources/huong-dan-xay-dung-agent-thuc-te.md` | created |
| `wiki/concepts/agent.md` | created |
| `wiki/concepts/workflow.md` | created |
| `wiki/concepts/model-selection.md` | created |
| `wiki/concepts/tools.md` | created |
| `wiki/concepts/instructions.md` | created |
| `wiki/concepts/orchestration.md` | created |
| `wiki/concepts/manager-pattern.md` | created |
| `wiki/concepts/handoff-pattern.md` | created |
| `wiki/concepts/guardrails.md` | created |
| `wiki/concepts/human-in-the-loop.md` | created |
| `wiki/entities/openai-agents-sdk.md` | created |
| `wiki/entities/openai.md` | created |
| `wiki/index.md` | modified |
| `wiki/log.md` | modified |

## Notes
- Invoked via: `/ingest` skill
- File `raw/` không bị chỉnh sửa (R1); chỉ đọc.
- `wiki/_template.md` không được tạo do R5 (folder-structure) không cho phép file `.md` tùy ý ở `wiki/`
  root — mỗi trang concept/entity/source tự khai frontmatter OKF (R9) trực tiếp.

## Origin
- **Draft:** `wiki/sources/draft/270726-ingest-agent-guide.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
