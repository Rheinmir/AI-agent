---
type: draft
title: chat-sidebar-redesign
status: proposed
tags: [redesign-existing-projects, output-report]
timestamp: 2026-08-03
task: T-260727-01
---

# 030826-chat-sidebar-redesign
**Type:** draft
**Status:** proposed
**Tags:** redesign-existing-projects, output-report
**Proposed:** 2026-08-03

## What
Áp audit của `/redesign-existing-projects` lên `demo_agents/weather_agent/web/chat.html` — trọng tâm
là thêm nút đóng/mở sidebar (bug người dùng chỉ ra: sidebar không thu gọn được), cộng các mục nhỏ
trong audit: focus ring, press feedback, favicon/meta, tighten typography ở empty-state.

## Output
- **Sidebar thu gọn được** — nút ✕ trong sidebar (cạnh "Cuộc trò chuyện mới") để đóng, nút ☰ nổi
  góc trên-trái (chỉ hiện khi sidebar đang đóng) để mở lại. Trạng thái nhớ qua `localStorage`, main
  content tự giãn full-width khi sidebar đóng (animate `width`/`padding`, không dùng `display:none`
  đột ngột).
- **Focus-visible** — outline rõ ràng cho keyboard nav trên mọi control (trước đó không có style
  riêng, phụ thuộc hoàn toàn default trình duyệt).
- **Press feedback** — `button:active{transform:scale(.96)}` áp dụng chung, cộng
  `prefers-reduced-motion` guard.
- **Favicon + meta description** — trước đó thiếu cả hai (audit mục "Strategic Omissions"/"Iconography").
- **Typography polish** — `empty-state h2` thêm `font-weight:600`, `letter-spacing:-.01em`,
  `text-wrap:balance`; đoạn dẫn dùng `text-wrap:pretty`.
- Giữ nguyên bảng màu/layout ChatGPT-style đã chốt trước đó (accent xanh lá `#10a37f`, sidebar tối
  phẳng) — không thêm gradient/noise trang trí vì lệch khỏi yêu cầu rõ ràng trước đó "copy theme
  của ChatGPT" (ChatGPT bản thân cũng phẳng/tối giản, thêm texture sẽ đi ngược chính yêu cầu đó).
- 12/12 test offline vẫn pass (không đụng backend).

## Files
| File | Action |
|------|--------|
| `demo_agents/weather_agent/web/chat.html` | edited (sidebar collapse, focus/press states, favicon, typography) |
| `wiki/index.md`, `wiki/log.md` | modified |

## Notes
- Invoked via: `/redesign-existing-projects` skill, theo yêu cầu người dùng ("sao không có nút đóng
  side bar"). Phạm vi cố ý thu hẹp theo đúng "Rules" của skill ("small, targeted improvements over
  big rewrites") — không rewrite lại toàn bộ giao diện, không đổi bảng màu/layout đã được duyệt.
- Tiếp theo: chạy `/hallmark` theo yêu cầu người dùng ("đặt /hallmark cuối cùng").

## Origin
- **Draft:** `wiki/draft/uiux/030826-chat-sidebar-redesign.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
