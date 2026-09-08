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
chỗ avatar trợ lý (JS).

**Cập nhật 26/08/2026 — đổi kỹ thuật vẽ sang PIXEL ART (rect-grid), giữ NGUYÊN ý nghĩa vòng vô
cực.** User yêu cầu 3 agent (weather/devops/librarian) cùng chuyển sang 1 hệ icon pixel-art thống
nhất, sau khi research `/last30days` về xu hướng "AI agent pixel style" (Pixel Agents, AgentRoom —
biến agent thành nhân vật pixel-art). Thay `<path>` cong (`M9.828 9.172a4 4 0...`, `stroke`-based)
bằng lưới `<rect>` vuông (`fill`-based, `shape-rendering:crispEdges`) — VẪN vẽ hình vòng vô cực
(2 vòng lặp nối nhau ở giữa), chỉ đổi kỹ thuật vẽ (đường cong mượt → khối pixel vuông), không đổi
Ý NGHĨA biểu tượng đã chọn ở trên. Áp dụng ở ĐÚNG 4 chỗ như cũ (favicon, empty-state, 2× avatar JS)
— không thêm/bớt vị trí dùng icon.
```html
<svg viewBox="0 0 8 4"><rect x="1" y="0" width="2" height="1"/><rect x="5" y="0" width="2" height="1"/><rect x="0" y="1" width="1" height="2"/><rect x="3" y="1" width="2" height="2"/><rect x="7" y="1" width="1" height="2"/><rect x="1" y="3" width="2" height="1"/><rect x="5" y="3" width="2" height="1"/></svg>
```
CSS đổi từ `stroke:var(--color-on-accent);fill:none;stroke-width:var(--icon-stroke);stroke-linecap/
linejoin:round` sang `fill:var(--color-on-accent);stroke:none;shape-rendering:crispEdges` — vì rect
là khối đặc (fill), không phải nét (stroke), khác kỹ thuật vẽ gốc đã ghi ở trên (đoạn này THAY THẾ,
không còn áp dụng đoạn "Giữ NGUYÊN kỹ thuật vẽ" phía trên nữa kể từ 26/08/2026).

**Cập nhật 29/08/2026 — đổi từ icon hình học (vòng vô cực) sang NHÂN VẬT pixel "Clawd-style" đeo
KÍNH đẩy lên đỉnh đầu (ẩn dụ hình vô cực CI/CD) + BELT dụng cụ + cờ lê.** Cùng đợt đổi với
`weather_agent` (xem `weather_agent/web/design.md` § Variants, entry cùng ngày, cùng skill
`/create-agent-avatar` + engine `harness/scripts/pixel_icon_gen.py`) — quy trình đầy đủ +
Design Feedback nằm ở `wiki/log.md`. Kính (2 vòng nối cầu giữa) CHÍNH LÀ ký hiệu vô cực (∞) khi
nhìn ngang — giữ được ý nghĩa biểu tượng gốc "vòng lặp CI/CD" dù đổi hẳn từ icon hình học sang nhân
vật đeo phụ kiện. Sinh markup qua `build_icon_svg('devops')` trong `pixel_icon_gen.py`, KHÔNG gõ
tay toạ độ `<rect>` — đổi cấu trúc phải sửa `AGENTS['devops']` trong file đó trước rồi generate lại.
```html
<svg viewBox="0 0 10 9" shape-rendering="crispEdges"><g fill="#475569"><rect x="2" y="0" width="2" height="0.5"/><rect x="6" y="0" width="2" height="0.5"/></g><g fill="#1F2937"><rect x="2" y="0.5" width="2" height="0.5"/><rect x="6" y="0.5" width="2" height="0.5"/><rect x="2" y="1" width="6" height="0.5"/><rect x="2" y="1.5" width="6" height="0.5"/></g><g fill="#ffffff"><rect x="1" y="2" width="8" height="1"/><rect x="0" y="3" width="10" height="1"/><rect x="1" y="4" width="8" height="1"/><rect x="1" y="5" width="8" height="1"/><rect x="1" y="6" width="8" height="1"/><rect x="1" y="7" width="8" height="1"/><rect x="1" y="8" width="1" height="1"/><rect x="3" y="8" width="1" height="1"/><rect x="6" y="8" width="1" height="1"/><rect x="8" y="8" width="1" height="1"/></g><g fill="#1a1a1a"><rect x="2" y="3" width="1" height="1"/><rect x="7" y="3" width="1" height="1"/></g><g fill="#44403C"><rect x="1" y="6" width="8" height="1"/></g><g fill="#F97316"><rect x="6" y="5" width="2" height="1"/><rect x="6" y="6" width="1" height="1"/><rect x="6" y="7" width="1" height="1"/></g></svg>
```
Nhân vật có MÀU RIÊNG từng phần (thân trắng, mắt đen, kính xám `#1F2937`/`#475569`, belt nâu
`#44403C`, cờ lê cam `#F97316`) — CSS `fill:var(--color-on-accent)` hiện có VẪN GIỮ NGUYÊN, không
xoá (màu inline trên `<g>` con luôn thắng màu kế thừa từ `<svg>` cha). Áp dụng ĐÚNG 4 chỗ như cũ.

### Icon librarian (step-indicator) — cập nhật 29/08/2026, cùng đợt với weather_agent
`TOOL_STEPS.ask_librarian` (badge nhỏ khi devops_agent gọi sang librarian_agent qua socket) trước
đó bị bỏ sót — vẫn dùng icon kính lúp pixel cũ trong khi avatar chính đã đổi. Đổi sang NHÂN VẬT
librarian đã khoá (mũ cử nhân + kính một mắt + tua), sinh qua `build_icon_svg('librarian')` trong
`harness/scripts/pixel_icon_gen.py` — xem `weather_agent/web/design.md` § entry cùng ngày để biết
chi tiết so sánh size (11px→15px). Đồng bộ y hệt sang file này.

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
