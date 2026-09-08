---
type: draft
title: design-verified-by-use
status: proposed
tags: [docs-site-macos, output-report]
timestamp: 2026-08-03
task: T-260727-01
---

# 030826-design-verified-by-use
**Type:** draft
**Status:** proposed
**Tags:** docs-site-macos, output-report
**Proposed:** 2026-08-03

## What
Docs site tóm tắt đợt UI/UX cho `demo_agents/weather_agent/web/`: khoá design system qua Hallmark
(10 lỗi audit tĩnh), rồi 8 lỗi thật KHÁC chỉ lộ ra qua feedback trực tiếp trên trang chạy — luận
điểm chính: audit tĩnh và dùng thật bắt được 2 loại lỗi khác nhau, cần cả hai.

## Output
- `llmwiki/html/030826-design-verified-by-use.html` — 8 section (Luận điểm, Khoá hệ, và 6 bug thật
  theo đúng trình tự xảy ra: tour che nút, spacing lệch nhịp, đường dẫn dài che nút, event bubbling,
  mica→chìm hẳn, bài học/quy tắc), mind map, timeline cho vòng "chìm như 1" (2 lần sửa mới đúng ý).
- Nội dung lấy nguyên từ `demo_agents/weather_agent/web/design.md` (§ Notes, § Variants) và các
  dòng log `hallmark — post-lock-bugfix-*` — không phát minh thêm, chỉ trình bày lại có cấu trúc.

## Files
| File | Action |
|------|--------|
| `llmwiki/html/030826-design-verified-by-use.html` | created |
| `wiki/sources/draft/030826-design-verified-by-use.md` | created |
| `wiki/index.md` | modified |

## Notes
- Invoked via: `/docs-site-macos` skill, theo yêu cầu người dùng ("bổ sung đi" sau đề nghị của
  harness R10 docs-gate).

## Origin
- **Draft:** `wiki/sources/draft/030826-design-verified-by-use.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
