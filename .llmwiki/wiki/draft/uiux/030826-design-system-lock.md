---
type: draft
title: design-system-lock
status: proposed
tags: [hallmark, output-report]
timestamp: 2026-08-03
task: T-260727-01
---

# 030826-design-system-lock
**Type:** draft
**Status:** proposed
**Tags:** hallmark, output-report
**Proposed:** 2026-08-03

## What
Sửa hết 10 lỗi từ `hallmark audit chat.html`, đồng bộ `index.html` (đang dùng hệ theme khác hẳn —
xanh dương kính mờ) về cùng một hệ token với `chat.html`, rồi khoá `design.md` cho toàn bộ
`demo_agents/weather_agent/web/`.

## Output
- **10/10 lỗi audit đã sửa** trong `chat.html`:
  - 3 critical: token discipline (19 raw hex → token đặt tên), thiếu breakpoint mobile (thêm
    `@media(max-width:768px)` chuyển sidebar thành overlay + backdrop), `session-item` không thao
    tác được bằng bàn phím (thêm `role="button" tabindex="0"` + keydown Enter/Space).
  - 3 major: nút xoá chỉ hiện khi hover (thêm `:focus-within`), stroke-width icon không đồng nhất
    1.8/2/2.4 (gộp về `--icon-stroke`), font đơn (giữ nguyên, ghi chú rõ là quyết định có chủ đích
    theo yêu cầu gốc "copy ChatGPT", không phải bug).
  - 4 minor: `--main-bg` trắng tuyệt đối → tint nhẹ `#fbfefc`, bỏ `width:100vw;height:100vh` thừa
    trên phần tử `position:fixed`, z-index tuỳ tiện → `--z-flyout/--z-overlay/--z-overlay-content`,
    empty-state căn giữa (giữ nguyên — audit tự nhận đây là chấp nhận được).
- **Đồng bộ `index.html`**: viết lại toàn bộ để dùng chung token với `chat.html` — bỏ theme kính mờ
  xanh dương (`#0a84ff`, backdrop-filter, gradient nền), chuyển sang flat + accent xanh lá
  (`#10a37f`) khớp `chat.html`; thêm favicon, meta description, focus-visible, press feedback
  giống hệ đã khoá.
- **`tokens.css`** — source of truth cho cả thư mục (không `<link>` trực tiếp vì cả 2 file
  self-contained một-file-duy-nhất theo quy ước dự án — ghi rõ deviation trong `design.md`).
- **`design.md`** — khoá hệ (genre modern-minimal, theme custom, token/CTA-voice/motion/a11y/
  responsive), ghi lại 10 lỗi đã sửa trong `## Notes` làm bằng chứng.
- 12/12 test offline vẫn pass (không đụng backend).

## Files
| File | Action |
|------|--------|
| `demo_agents/weather_agent/web/chat.html` | edited (sửa 10 lỗi audit, thêm stamp Hallmark) |
| `demo_agents/weather_agent/web/index.html` | rewritten (đồng bộ theme với chat.html) |
| `demo_agents/weather_agent/web/tokens.css` | created |
| `demo_agents/weather_agent/web/design.md` | created (khoá hệ thiết kế) |
| `wiki/index.md`, `wiki/log.md` | modified |

## Notes
- Invoked via: `/hallmark audit` → sửa tay 10 lỗi → `/hallmark` (lock the system), theo đúng thứ tự
  người dùng yêu cầu ("sửa hết 10 lỗi trước rồi mới khoá design.md").
- `.hallmark/log.json` (rotation log giữa các build) không tạo — đây là khoá MỘT hệ có sẵn, không
  phải build catalog mới cần rotate; `design.md` đã là bản ghi lâu dài.

## Origin
- **Draft:** `wiki/draft/uiux/030826-design-system-lock.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
