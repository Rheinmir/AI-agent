# Design — DevOps Agent demo UI

Locked design system cho `demo_agents/devops_agent/web/` (`chat.html`). File này là **FORK** của
`demo_agents/weather_agent/web/design.md`, không phải hệ độc lập từ đầu — `chat.html` được tạo bằng
cách COPY NGUYÊN VĂN file của weather_agent rồi chỉ đổi nội dung/màu/icon (xem `wiki/log.md`,
entry `devops-agent-reuse-weather-chat-ui`). File này **CHỈ ghi lại phần KHÁC** (delta) so với bản
gốc — phần còn lại (layout, spacing, motion, a11y, responsive...) đọc trực tiếp ở file gốc, không
copy lại để tránh 2 nơi có thể lệch nhau theo thời gian.

**Quy tắc cho sửa sau này:** mọi thay đổi màu/icon/copy của `devops_agent/web/chat.html` phải qua
file này trước (thêm vào § Variants), giống đúng kỷ luật `weather_agent/web/design.md` đã áp dụng —
không sửa tay `chat.html` rồi thôi, để tránh lặp lại đúng lỗi đã bị người dùng chỉ ra: "lần đầu chưa
có thì tạo lại chứ sao lại dùng luôn logo của weather" (favicon/logo bị copy nguyên không suy nghĩ).

## Kế thừa nguyên văn từ weather_agent/web/design.md (KHÔNG lặp lại ở đây)
- Genre · modern-minimal, Macrostructure · App Shell (sidebar + main scroll)
- Toàn bộ token layout/spacing/radius/shadow (`--radius-panel`, `--radius-sheet`, `--neo-pop-*`,
  `--sidebar-bg`, `--main-bg`, `--border`, v.v. — TRỪ `--accent`/`--accent-2`, xem § Delta)
- CTA voice, Motion stance, Accessibility, Responsive breakpoint — xem file gốc, áp dụng y hệt.
- Toàn bộ lịch sử `§ Variants` của file gốc (21 bugfix ngày 2026-08-03/04) — áp dụng cho
  `devops_agent/chat.html` VÌ layout được copy SAU khi các bugfix đó đã có sẵn trong bản gốc, không
  cần tự trải qua lại.

## Delta — riêng cho devops_agent (khoá TẠI ĐÂY, không khoá ở file gốc)

### Màu thương hiệu — Kubernetes blue, không phải xanh lá của weather_agent
```css
--accent: #326CE5;   /* Kubernetes blue — màu brand chính thức */
--accent-2: #244da4; /* darken ~28% từ --accent, cùng công thức weather_agent dùng cho accent-2 */
```
Lý do chọn Kubernetes: cheatsheet hiện có (`data_collector.py`) xoay quanh K8s nhiều nhất — kubectl,
pod lifecycle là chủ đề đầu tiên/chi tiết nhất; container-health, deployment-patterns,
env-promotion đều lấy K8s làm ví dụ trung tâm khi giải thích. Đây là "công nghệ xương sống của
domain agent theo" theo đúng yêu cầu người dùng, KHÔNG phải màu tuỳ chọn thẩm mỹ. Quy ước này cũng
được ghi vào `AgentSpec.accent_color` (`demo_agents/devops_agent/agent_spec.py`) để
`harness/scripts/monolith_agent_deploy_converter.py` dùng lại đúng màu này cho trang chat built-in
khi đóng gói triển khai — 2 nơi phải khớp giá trị hex, sửa ở đây thì sửa luôn bên đó.

### Icon mark — vòng vô cực, không phải đám mây thời tiết
Thay path SVG hình đám mây (`M17.5 19a4.5...`, biểu tượng thời tiết) bằng path hình **vòng vô cực**
(kiểu Tabler icon "infinity", `M9.828 9.172a4 4 0...`) — biểu tượng phổ biến nhất cho DevOps (vòng
lặp develop→deploy→monitor liên tục). Dùng ở ĐÚNG 4 chỗ như bản gốc: favicon, icon empty-state, 2
chỗ avatar trợ lý (JS). Giữ NGUYÊN kỹ thuật vẽ của hệ gốc — single `<path>`, `fill:none`,
`stroke:currentColor` (hoặc `var(--color-on-accent)` trong khối màu), `stroke-linecap`/
`stroke-linejoin:round`, cùng token `--icon-stroke` — chỉ đổi hình dạng, không đổi cách vẽ.

### Nội dung — đổi toàn bộ copy, giữ cấu trúc
Title/meta description, header sidebar + hero ("Weather Agent"→"DevOps Agent"), 4 câu hỏi mẫu (đổi
từ câu hỏi thời tiết sang: liveness/readiness probe, canary deployment, "restart pod nginx" — demo
guardrail chặn hành động thật, "Bạn làm được gì?"), placeholder ô nhập, label tour — xem `chat.html`
trực tiếp, không lặp lại text ở đây (dễ lệch nếu duplicate).

### localStorage key — namespace riêng, tránh đụng dữ liệu 2 agent
`weather-chat-sidebar-collapsed`/`weather-chat-session-id`/`weather-chat-tour-seen` →
`devops-chat-*` — 2 agent có thể mở cùng trình duyệt mà không ghi đè trạng thái của nhau.

## Variants
- **2026-08-04 — `renderMarkdownLite()` lộ nguyên văn `#`/`##`/`` ` ``/`>` (propagate từ bản gốc,
  KHÔNG phải delta riêng).** Người dùng phát hiện qua ảnh chụp thật của CHÍNH devops_agent ("##" lộ
  nguyên văn trước "✅ Mình CÓ THỂ làm"), nhưng bug nằm ở hàm `renderMarkdownLite()` KẾ THỪA từ
  `weather_agent/web/chat.html` (§ Kế thừa nguyên văn ở trên), không phải phần đã khoá riêng ở file
  này. Sửa ở bản GỐC trước (xem `weather_agent/web/design.md` § Variants, entry cùng ngày), rồi copy
  nguyên văn 2 hàm (`renderInline`/`renderMarkdownLite`) + khối CSS mới
  (`.bubble h1/h2/h3/ul/ol/li/code/blockquote`, dùng lại token màu có sẵn) sang `chat.html` của
  devops_agent — KHÔNG viết logic riêng, giữ đúng nguyên tắc "1 nguồn sự thật cho phần layout dùng
  chung" đã lập từ lúc fork. Verify: extract hàm thật từ file qua `node`, input mẫu giống ảnh chụp
  màn hình cho output đúng (`<h2>`, không còn `##` thô).

## Notes
- File này được tạo RETROACTIVE (sau khi các lựa chọn màu/icon đã có trong `chat.html` từ trước) —
  theo yêu cầu trực tiếp của người dùng để chính thức hoá thành baseline khoá, tránh lặp lại việc
  sửa tay tuỳ tiện không qua ghi chép (đã xảy ra 1 lần: copy nguyên xanh lá + icon đám mây từ
  weather_agent mà không suy nghĩ, bị người dùng chỉ ra).
- Không lặp lại toàn bộ 21 bugfix của file gốc — tham chiếu thay vì copy, giữ 1 nguồn sự thật cho
  phần layout DÙNG CHUNG. Nếu devops_agent sau này cần lệch layout riêng (không chỉ màu/icon/copy),
  bugfix đó phải ghi vào § Variants Ở ĐÂY, không sửa ngược lên file gốc của weather_agent.

## Origin
- **Fork từ:** `demo_agents/weather_agent/web/design.md`
- **Log:** `wiki/log.md` — entry `devops-agent-reuse-weather-chat-ui`,
  `devops-agent-domain-accent-color-and-converter-support`
