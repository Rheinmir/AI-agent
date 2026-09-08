# Design — Weather Agent demo UI

Locked design system cho `demo_agents/weather_agent/web/` (`chat.html` + `index.html`). Các trang
sau này trong thư mục này phải DÙNG CHUNG hệ này, không tự chọn theme riêng — sửa ở đây trước,
đồng bộ tay sang từng `.html` (xem § Exports vì sao không `<link>` trực tiếp).

## System
- Genre · modern-minimal (app/tool UI, không phải trang marketing)
- Macrostructure · App Shell (non-catalog) — sidebar cố định + main scroll cho `chat.html`;
  single-card centered cho `index.html`. Không map vào 21 macrostructure của Hallmark vì cả hai
  đều là màn hình chức năng, không phải landing page.
- Theme · custom (vibe: "ChatGPT-style, sidebar neomorphism trên nền trắng, main phẳng hoàn toàn,
  single green accent" — đã amend 3 lần trong ngày 2026-08-03, xem § Variants; lịch sử: flat →
  mica-glass → neomorphism cho sidebar, panel nổi → phẳng hoàn toàn cho main)
- Axes · paper-band: light · display-style: grotesk-sans (system sans, một họ font duy nhất,
  có chủ đích — xem ghi chú trong `chat.html`) · accent-hue: chromatic-other (xanh lá ~165°)

## Tokens (canonical · `tokens.css` là source of truth)
```css
:root {
  --sidebar-bg: #171717;
  --sidebar-text: #ececec;
  --sidebar-text-dim: #a8a8a8;
  --sidebar-hover: #212121;
  --main-bg: #fbfefc;
  --text: #0d0d0d;
  --text-dim: #6e6e80;
  --bubble-user: #f4f4f4;
  --border: #e5e5e5;
  --color-border-2: #d0d0d5;
  --color-hover-surface: #f7f7f8;
  --color-disabled: #d9d9e3;

  --accent: #10a37f;
  --accent-2: #1a7f64;
  --color-on-accent: #ffffff;

  --color-danger: #b3261e;
  --color-danger-bg: #fdecea;
  --color-danger-hover: #ff6b6b;

  --color-avatar-user: #5a5a66;
  --color-dim-2: #9a9aa5;

  --icon-stroke: 2;
  --z-flyout: 50; --z-overlay: 500; --z-overlay-content: 501;

  --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;

  /* Panel — xem § Variants. Token kính mờ (--sidebar-glass-*) của bản mica cũ đã bỏ hẳn — sidebar
     giờ neomorphism (cặp bóng sáng/tối, không glass). --shadow-panel-light chỉ còn dùng cho .card
     (index.html) — .chat-main đã phẳng hoàn toàn, không còn radius/shadow riêng. */
  --radius-panel: 16px;
  --app-base-bg: #ffffff;
  --shadow-panel-light: 0 8px 24px rgba(13, 13, 13, .10);
  --neo-shadow-light: -9px -9px 18px rgba(255, 255, 255, .045), inset 0 1px 0 rgba(255, 255, 255, .03);
  --neo-shadow-dark: 10px 10px 26px rgba(0, 0, 0, .5);

  /* Overlay alpha — không rgba() rời rạc mid-render, mọi giá trị lặp lại đều qua token */
  --white-a08: rgba(255, 255, 255, .08); --white-a12: rgba(255, 255, 255, .12);
  --white-a15: rgba(255, 255, 255, .15); --white-a22: rgba(255, 255, 255, .22);
  --white-a45: rgba(255, 255, 255, .45); --white-a55: rgba(255, 255, 255, .55);
  --black-a06: rgba(0, 0, 0, .06); --black-a08: rgba(0, 0, 0, .08);
  --black-a3: rgba(0, 0, 0, .3); --black-a4: rgba(0, 0, 0, .4);
  --accent-a08: rgba(16, 163, 127, .08); --accent-a12: rgba(16, 163, 127, .12);
  --accent-a35: rgba(16, 163, 127, .35); --danger-a3: rgba(179, 38, 30, .3);
}
```

*Lưu ý:* dùng hex thay OKLCH — đây là hệ đã tồn tại sẵn trong code (không phải build mới từ
catalog Hallmark), khoá nguyên giá trị đang chạy thật để tránh lệch màu do quy đổi.

## CTA voice
- Primary · fill `var(--accent)`, chữ `var(--color-on-accent)` · radius 12px (nút vuông-bo) hoặc
  50% (nút tròn `.send-btn`) · padding 10-11px dọc, 13-18px ngang
- Secondary · outline `var(--border)`, nền `var(--main-bg)`, chữ `var(--text)` · cùng radius nhóm
- Focus-within (form/input) · viền đổi sang `var(--accent)` khi phần tử con bên trong được focus —
  áp dụng cả `form:focus-within` (composer, chat.html) lẫn `input:focus` (index.html)

## Motion stance
- Nhẹ, có chủ đích: `button:active{transform:scale(.96/.97)}`, sidebar/tour dùng
  `cubic-bezier(.4,0,.2,1)`, không bounce/overshoot
- Reduced-motion fallback · `prefers-reduced-motion:reduce` ép mọi transition/animation về gần 0ms

## Accessibility (bắt buộc theo hệ này)
- Mọi control tương tác có `:focus-visible{outline:2px solid var(--accent)}`, không animate
  outline xuất hiện
- Hover-only affordance PHẢI có tương đương `:focus-within`/`:focus` — không khoá tính năng sau
  chuột (bài học từ session-item/nút xoá trong `chat.html`)
- Hàng danh sách click-được nhưng KHÔNG phải `<button>` (vì chứa button lồng bên trong) dùng
  `role="button" tabindex="0"` + xử lý Enter/Space, không phải `<div>` click-only

## Responsive
- Breakpoint `max-width:768px` bắt buộc cho mọi layout có sidebar/panel cố định — chuyển sang
  overlay (`position:fixed` + backdrop click-to-close), không đẩy layout chính

## Variants
- **2026-08-03 — Panel nổi kiểu mica.** Theo yêu cầu trực tiếp, đổi từ layout gốc "flat, sidebar
  chạm hết viewport" sang "2 tấm panel nổi": `.app` có `gap:10px;padding:10px`, sidebar và
  `.chat-main`/`.card` đều `border-radius:var(--radius-panel)` + `box-shadow:var(--shadow-panel-*)`.
  Sidebar dùng kính mờ thật (`backdrop-filter:blur(20px) saturate(1.5)` + sheen góc trên qua
  `::before`), `.chat-main`/`.card` là card sáng phẳng (không blur — vùng nội dung cuộn nhiều,
  blur không cần thiết và tốn hiệu năng). Nền `--app-base-bg` ban đầu thử tối (`#0f0f0f`) rồi đổi
  lại trắng (`#ffffff`) theo phản hồi trực tiếp — bóng đổ (`box-shadow`) vẫn đủ tạo cảm giác nổi
  dù nền và panel sáng gần giống nhau, không bắt buộc phải có nền tối phía sau mới "nổi" được.
  Áp dụng ĐỒNG BỘ cả `chat.html` và `index.html` (cùng token `--radius-panel`/`--app-base-bg`/
  `--shadow-panel-light`) — không để một file amend mà file kia đứng yên, phá nguyên tắc "pages
  phải dùng chung hệ" của chính file này.
- **2026-08-03 — Bỏ viền `.chat-main`/`.card`.** `--main-bg` (#fbfefc) gần trùng `--app-base-bg`
  (#ffffff) — viền `1px solid var(--border)` tạo đường kẻ cứng thừa không cần thiết giữa 2 màu gần
  như giống hệt nhau. Bỏ hẳn `border`, chỉ dựa `box-shadow:var(--shadow-panel-light)` để tạo cảm
  giác nổi — panel "chìm" vào nền, không có đường viền cắt rời. **Quy tắc thêm vào hệ:** khi panel
  và nền nó ngồi lên có cùng tông màu (chênh lệch lightness rất nhỏ), ưu tiên `box-shadow` đơn
  thuần thay vì thêm `border` để phân định ranh giới — border chỉ cần khi 2 màu đủ khác biệt để
  không tạo viền cứng phản tác dụng.
- **2026-08-03 — "Chìm như 1 với background" = bỏ HẾT, không chỉ viền.** Lần đầu chỉ bỏ `border`,
  giữ `border-radius`+`box-shadow` — chưa đúng ý. Yêu cầu thật là hoà HẲN vào nền, không còn ranh
  giới nào. `.chat-main` giờ không border, không border-radius, không box-shadow — chỉ còn
  `background:var(--main-bg)` (gần như cùng màu `--app-base-bg` nên thị giác merge thật). **`.card`
  trong `index.html` CHỦ Ý giữ nguyên `border-radius`+`box-shadow`** — khác `chat-main` vì đây là
  nội dung DUY NHẤT trên trang (không có sidebar bên cạnh làm mốc cấu trúc), bỏ hết sẽ mất hẳn ranh
  giới trực quan cho một form thao tác — không phải quên đồng bộ, mà là phân biệt có chủ đích theo
  ngữ cảnh trang.
- **2026-08-03 — Sidebar: mica-glass → neomorphism.** Theo yêu cầu trực tiếp. Bỏ hẳn
  `backdrop-filter`/`-webkit-backdrop-filter` (glass), bỏ `border`, bỏ sheen `::before`. Thay 1
  `box-shadow` "nổi" bằng cặp bóng đối xứng mô phỏng vật liệu được ép lồi ra từ CHÍNH bề mặt nó —
  đặc trưng cốt lõi phân biệt neomorphism với glass/mica (glass = trong suốt + lấy mẫu nền phía
  sau; neomorphism = đặc, không trong suốt, chỉ dùng bóng kép). *(Token ban đầu đặt tên
  `--neo-shadow-light/dark`; đổi tên thành `--neo-inset-*` cùng ngày khi thêm hướng "nổi" riêng
  cho `.chat-main` — xem entry "Đảo ngược nổi/lõm" bên dưới.)* 4 token glass cũ
  (`--sidebar-glass-bg/border/sheen`, `--shadow-panel-dark`) đã xoá khỏi `:root` — không còn nơi
  nào tham chiếu.
- **2026-08-03 — Composer focus-within xanh lá.** `form` (composer, chat.html) thêm
  `form:focus-within{border-color:var(--accent)}` — cùng ngôn ngữ với `input:focus` đã có ở
  `index.html`, để ô nhập câu hỏi báo rõ đang active bằng đúng accent màu của hệ thay vì im lặng.
  **AMEND cùng ngày (bugfix sau):** người dùng thấy hiệu ứng trực tiếp trên trang chạy thật rồi báo
  "select vào vẫn bị màu xanh lá này" — không muốn nữa. Xoá hẳn rule `form:focus-within`, composer
  giữ nguyên `border:1px solid var(--border)` cố định, không đổi màu khi focus.
- **2026-08-03 — Đảo ngược nổi/lõm: sidebar LÕM, chat-main NỔI.** Theo yêu cầu trực tiếp (kèm ảnh
  chụp tay vẽ minh hoạ). Trước đó cả `--neo-shadow-light`/`--neo-shadow-dark` chỉ có MỘT hướng
  "nổi" áp cho sidebar, còn `.chat-main` phẳng tuyệt đối. Giờ tách thành 2 cặp token riêng, dùng
  đúng kỹ thuật neomorphism cho từng trạng thái:
  - **Lõm (pressed-in)** — `.sidebar` — `--neo-inset-dark`/`--neo-inset-light`, cả hai đều
    `inset`: tối ở góc trên-trái (đáy hố khuất sáng), sáng rất nhạt ở góc dưới-phải (mép hố hắt
    sáng ngược). Trông như bị ấn/khắc VÀO bề mặt.
  - **Nổi (popped-out)** — `.chat-main` — `--neo-pop-light`/`--neo-pop-dark`, KHÔNG `inset`: sáng
    ở góc trên-trái (mặt hứng sáng), xám-xanh nhạt (không đen thuần, cùng họ với nền trắng) ở góc
    dưới-phải. `.chat-main` từ chỗ hoàn toàn phẳng (bugfix-5) giờ có lại `border-radius`+`box-shadow`
    — quyết định "chìm hoàn toàn" trước đó bị AMEND, không phải lỗi, ghi lại để không nhầm là
    quay đầu ngẫu nhiên.
  - **Quy tắc thêm vào hệ:** lõm và nổi trong neomorphism là 2 CẶP token riêng biệt (không phải
    đảo dấu +/- một cặp duy nhất) — hướng bóng, việc có `inset` hay không, và tông màu (tối cho bề
    mặt tối, xám-xanh nhạt cho bề mặt sáng) đều khác nhau giữa 2 trạng thái.
- **2026-08-03 — Sửa độ tương phản bóng lõm sidebar (không thấy được trên nền gần đen).** Người
  dùng report hiệu ứng "lõm" ở entry trên không thấy được sau khi reload — xác nhận server ĐÃ chạy
  đúng code mới (`curl` ra đúng CSS), vậy nguyên nhân không phải cache/chưa reload mà là chọn giá
  trị token sai: `--neo-inset-light` alpha `.025` gần như vô hình, và `--sidebar-bg:#171717` quá
  gần đen nên không còn "khoảng trống" (headroom) để bóng tối `--neo-inset-dark` đọc được là tối
  hơn nền. Sửa cả 2:
  - `--sidebar-bg:#171717→#1e1e22`, `--sidebar-hover:#212121→#2a2a2f` (giữ nguyên khoảng cách
    tương đối giữa bg/hover, chỉ nâng cả cụm sáng lên để có headroom).
  - `--neo-inset-dark`: offset/blur `8px/8px/18px→10px/10px/24px`, alpha `.55→.65`.
  - `--neo-inset-light`: offset/blur `-6px/-6px/14px→-8px/-8px/20px`, alpha `.025→.09` (~3.6×).
  - **Quy tắc thêm vào hệ:** bóng `inset` cần "headroom" tương phản ở CẢ HAI phía (nền không được
    quá gần biên đen/trắng tuyệt đối) mới đọc được bằng mắt — kiểm tra trực quan thật trên trình
    duyệt, không chỉ tin `curl` xác nhận code đã deploy đúng là đủ để kết luận hiệu ứng "hoạt động".
- **2026-08-03 — Bóng lõm sidebar: đen thuần → xám.** Người dùng chỉ ra `--neo-inset-dark` vẫn dùng
  `rgba(0,0,0,.65)` — đen thuần, không phải xám cùng họ với hệ màu sidebar (toàn bộ `--sidebar-*`
  đều là xám trung tính, không có giá trị đen thuần nào khác trong hệ). Đổi
  `rgba(0,0,0,.65)→rgba(12,12,15,.65)` — vẫn đủ tối để đọc được là bóng lõm (đã có headroom từ amend
  trước), nhưng là XÁM tối cùng tông với `--sidebar-bg`/`--sidebar-hover`, không phải đen tuyệt đối.
  - **Quy tắc thêm vào hệ:** trùng với anti-pattern "generic box-shadow dùng đen thuần" của
    redesign audit — bóng phải tint theo tông màu bề mặt xung quanh, kể cả bóng rất tối, không dùng
    `rgba(0,0,0,x)` làm giá trị mặc định.
- **2026-08-03 — Bỏ neomorphism, sidebar về PHẲNG + SÁNG (theo ảnh ChatGPT app thật).** Người dùng
  gửi ảnh chụp sidebar ChatGPT mobile thật — hoàn toàn phẳng (không bóng nổi/lõm), nền sáng chữ
  tối — ngược hẳn hướng neomorphism tối vừa tune xong. Hỏi lại phạm vi (AskUserQuestion): người
  dùng chọn "bỏ hết bóng, giữ màu tối" trước, rồi ngay sau đó chủ động nói thêm "bỏ màu tối" — kết
  hợp lại thành: `.sidebar` bỏ hết box-shadow VÀ đổi từ dark sang light để khớp ảnh tham chiếu.
  - Xoá `box-shadow` khỏi `.sidebar`; xoá hẳn 2 token `--neo-inset-dark/light` (không còn nơi nào
    dùng). `.chat-main`/`.card` vẫn giữ nguyên `--neo-pop-*` (nổi) — KHÔNG bị yêu cầu đổi, giữ
    nguyên theo đúng phạm vi câu hỏi đã hỏi trước khi sửa.
  - `--sidebar-bg:#1e1e22→#f5f5f7`, `--sidebar-text:#ececec→#0d0d0d`,
    `--sidebar-text-dim:#a8a8a8→#6e6e80` (trùng `--text-dim`), `--sidebar-hover:#2a2a2f→#ececed`.
  - Toàn bộ viền/hover trong sidebar trước đó dùng token `--white-a08/12/15/22/45` (overlay trắng
    mờ, chỉ hiện được trên nền tối) — đổi sang tương đương nền sáng: `--color-border-2` (viền
    `new-chat`/`sidebar-close`/`tour-help`), `--border` (viền trên `sidebar-foot`),
    `--color-danger-bg` (hover nút xoá session), `--accent` (hover `tour-help`, thay vì
    `--color-on-accent` trắng — vô hình trên nền sáng). 5 token `--white-a08/12/15/22/45` xoá khỏi
    `:root` — không còn nơi nào tham chiếu; `--white-a55` GIỮ LẠI vì `.tour-ring` dùng cho viền
    spotlight vẽ trên lớp scrim tối của tour, độc lập với màu nền sidebar.
  - **Quy tắc thêm vào hệ:** khi đổi nền một panel từ tối→sáng (hoặc ngược lại), phải rà lại MỌI
    token overlay-alpha (`--white-a*`/`--black-a*`) mà các phần tử con trong panel đó đang dùng cho
    viền/hover — token overlay chỉ có tác dụng đúng hướng tương phản với ĐÚNG MỘT nền (trắng-mờ cần
    nền tối, đen-mờ cần nền sáng); đổi nền mà không rà token con sẽ để lại viền/hover vô hình.
- **2026-08-03 — Bỏ hẳn "floating panel": sidebar phẳng dán mép, .chat-main thành sheet bo góc
  trái.** Bugfix-11 đổi màu sidebar nhưng vẫn giữ `border-radius` + `.app{padding:10px;gap:10px}`
  → 4 góc bo + khoảng hở quanh vẫn đọc là "panel nổi tách rời" (đúng ý người dùng phàn nàn: "giảm
  trọng số cái 4 cạnh nổi này xuống làm không có cạnh luôn"). Đổi sang mô hình sidebar dán mép +
  content là "sheet" bị đẩy — pattern quen thuộc (Notion, Arc, ChatGPT desktop):
  - `.sidebar`: bỏ hẳn `border-radius` — dán sát mép trái/trên/dưới viewport, 0 margin ngoài.
  - `.app`: bỏ `padding:10px` và `gap:10px` — không còn khoảng hở lộ nền `--app-base-bg` quanh 2
    panel; `.chat-main` chỉ đơn giản bị đẩy sang phải bởi `width` cố định của `.sidebar` (flex mặc
    định), không cần gap để tạo khoảng cách.
  - `.chat-main`: `border-radius:var(--radius-panel)` (bo đều 4 góc, 16px) →
    `border-radius:var(--radius-sheet) 0 0 var(--radius-sheet)` (chỉ bo 2 góc TRÁI — chỗ giáp
    sidebar; 2 góc phải vuông vì áp thẳng mép viewport phải). Token mới `--radius-sheet:24px` — lớn
    hơn `--radius-panel` có chủ đích ("cạnh bo góc lớn" theo đúng yêu cầu), tách biệt khỏi
    `--radius-panel` vì `.card` (index.html) vẫn cần bo đều 4 góc (không có sidebar làm mốc).
  - Mobile overlay drawer (`@media max-width:768px`) đồng bộ: `.sidebar{top:10px;left:10px;
    bottom:10px}` (panel nổi kiểu cũ) → `{top:0;left:0;bottom:0}` (dán mép, khớp đúng ảnh tham
    chiếu ChatGPT app mobile — drawer full-height không có khoảng hở).
  - **Quy tắc thêm vào hệ:** đổi màu bề mặt (tối→sáng) KHÔNG đủ để hết cảm giác "panel nổi" nếu
    `border-radius` + khoảng hở xung quanh (`padding`/`gap` của container cha) vẫn còn — 3 thứ này
    cùng tạo ra ấn tượng "vật thể tách rời", phải bỏ đồng thời cả 3 khi mục tiêu là "dán mép/liền
    khối". Khi 2 panel liền kề cần phân tách trực quan mà không dùng gap/viền, bo góc CHỈ ở cạnh
    giáp nhau (border-radius bất đối xứng, 2 giá trị 0) là kỹ thuật đúng, không phải bo đều 4 góc.
- **2026-08-03 — Góc bo `.chat-main` vô hình (contrast) + bỏ nốt viền còn sót.** Người dùng: "bo
  góc của khối div mẹ của khối này đâu" — góc bo 2 bên trái `.chat-main` (bugfix-12) có tồn tại
  trong CSS nhưng KHÔNG THẤY ĐƯỢC, vì phần notch góc-cắt lộ ra màu nền phía sau (`--app-base-bg`)
  mà giá trị cũ `#ffffff` gần như trùng `--main-bg:#fbfefc` (delta ~4/kênh màu) — CÙNG LOẠI LỖI với
  bóng inset sidebar không thấy được ở bugfix-9 (thiếu contrast headroom), chỉ khác đối tượng
  (corner-cutout thay vì box-shadow).
  - `--app-base-bg` (chỉ chat.html): `#ffffff→#e8e8ec` — xám nhạt đủ tương phản với `--main-bg` để
    lộ rõ phần góc bị cắt. **index.html CỐ Ý giữ nguyên `#ffffff`** — không có sidebar/góc bo bất
    đối xứng nên không cần contrast này, và trùng yêu cầu trước đó "nền dưới cùng để full trắng
    luôn" (đã có ở bugfix trước) — 2 file lệch giá trị token này có chủ đích, ghi rõ ở đây để không
    nhầm là thiếu đồng bộ.
  - Bỏ nốt 3 viền còn sót lại từ đợt chuyển sidebar sang nền sáng (bugfix-11): `.new-chat` và
    `.sidebar-close` bỏ hẳn `border` (trước đó dùng `var(--color-border-2)` để thay thế viền
    trắng-mờ cũ, giờ bỏ theo đúng tinh thần "không cạnh" của bugfix-12); `.sidebar-foot` bỏ
    `border-top`.
  - **Quy tắc thêm vào hệ:** BẤT KỲ hiệu ứng nào dựa vào chênh lệch màu giữa 2 bề mặt liền kề (bóng
    đổ, notch góc-cắt, viền mờ...) đều cần kiểm tra bằng mắt trên trình duyệt thật sau khi đổi màu
    — 2 giá trị hex "trông có vẻ khác nhau" trên giấy vẫn có thể render gần như giống hệt nhau nếu
    delta từng kênh RGB quá nhỏ (~dưới 8-10).
- **2026-08-03 — `--app-base-bg` = màu sidebar thật (không phải xám trung tính), bo góc to hơn.**
  Người dùng chỉnh lại ý bugfix-13: xám `#e8e8ec` riêng ở bước trước tuy đủ contrast nhưng SAI Ý
  NIỆM — "nó chính là neomorphism kiểu đẩy cái màn hình làm việc qua phải còn gì": notch góc-cắt
  của `.chat-main` phải lộ ra ĐÚNG màu mặt sidebar (như content sheet trượt đè lên bề mặt sidebar),
  không phải một backdrop trung lập thứ 3 không liên quan gì đến sidebar.
  - `--app-base-bg` (chỉ chat.html): `#e8e8ec` → `var(--sidebar-bg)` — tham chiếu trực tiếp, tự
    động đồng bộ nếu `--sidebar-bg` đổi sau này, đúng quan hệ ngữ nghĩa "notch lộ mặt sidebar".
  - `--radius-sheet`: `24px→36px` — bù lại việc `--sidebar-bg` (#f5f5f7) có contrast với
    `--main-bg` (#fbfefc) thấp hơn hẳn xám trung tính vừa bỏ; notch to hơn thì vẫn đọc rõ dù màu
    gần nhau, đỡ phải hy sinh đúng ý niệm màu chỉ để đổi lấy contrast.
  - index.html KHÔNG đổi theo `var(--sidebar-bg)` — không có sidebar để "đẩy", giữ `#ffffff` riêng.
  - **Quy tắc thêm vào hệ:** khi 1 token biểu diễn "màu bề mặt lộ ra phía sau vật thể bị cắt góc",
    ưu tiên tham chiếu ĐÚNG token của bề mặt thật đó (`var(--x)`) thay vì bịa một giá trị trung
    gian mới — dù trung gian có contrast tốt hơn, nó phá vỡ đúng ẩn dụ thị giác (ở đây là "đẩy qua
    bề mặt sidebar"); nếu contrast không đủ sau khi tham chiếu đúng, bù bằng kích thước hình học
    (bo góc to hơn) chứ không bù bằng cách đổi màu sai ý niệm.
- **2026-08-03 — Bóng sáng góc trên-trái tự che mất đường cong nó lẽ ra phải tôn lên; scrim tour
  quá gắt sau khi đổi theme sáng.** Hai lỗi phát sinh trực tiếp từ các amend vừa xong:
  - Người dùng: "giờ lại góc trái trên của div đó không được bo góc??" — `border-radius` CSS vẫn
    đúng (`var(--radius-sheet) 0 0 var(--radius-sheet)`, xác nhận qua curl), nhưng `--neo-pop-light`
    (`-8px -8px 18px rgba(255,255,255,.9)`) là bóng SÁNG gần trắng tuyệt đối, đặt lệch về góc
    TRÊN-TRÁI — sau khi bo góc tăng lên 36px (amend trước), vùng notch lớn hơn khiến bóng trắng gắt
    này phủ gần kín notch, xoá mất đúng phần tương phản đáng lẽ tố cáo đường cong. Hạ
    `alpha .9→.5`, `blur 18px→14px`, offset `-8px→-6px` — bóng còn là điểm nhấn nhẹ, không lấn át
    hình học nữa.
  - Người dùng: "cái nền gì xấu dữ vậy" (scrim tour) — lớp dim SVG dùng `rgba(0,0,0,.72)` (đen
    tuyệt đối, alpha rất cao) được chọn từ thời sidebar còn tối; giờ cả trang đã sáng/phẳng, mảng
    đen 72% trông quá gắt/lạc tông. Đổi `rgba(0,0,0,.72)→rgba(13,13,13,.5)` — cùng RGB với token
    `--text`, alpha hạ xuống 50%, đúng quy tắc "không dùng đen thuần mặc định" đã lập ở bugfix-10,
    áp dụng luôn cho chuỗi JS dựng SVG động (không chỉ token CSS tĩnh trong `:root`).
  - **Quy tắc thêm vào hệ:** một bóng/overlay có alpha CAO (gần đặc) đặt sát cạnh một đường cong có
    thể VÔ HIỆU HOÁ đường cong đó về mặt thị giác dù CSS hình học vẫn đúng — khi tăng kích thước 1
    yếu tố hình học (bo góc, notch...), phải rà lại các hiệu ứng phủ lên cạnh nó (bóng, glow) xem
    có còn tỉ lệ hợp lý không, không chỉ kiểm tra bản thân yếu tố đó. Quy tắc "không dùng
    `rgba(0,0,0,x)` mặc định" áp dụng cho MỌI nơi sinh màu, kể cả chuỗi SVG dựng bằng JS, không chỉ
    token tĩnh trong `:root`.
- **2026-08-03 — Tăng lại độ "nổi khối" của `.chat-main` (đẩy offset ra xa thay vì tăng alpha sát
  mép).** Người dùng: "làm nó nổi khối giống neumorphism đi" — bản hạ alpha ở bugfix-15 (sửa đúng
  lỗi che đường cong) nhưng đi hơi xa, bóng giờ quá mờ, mất hẳn cảm giác khối nổi 3D đặc trưng của
  neomorphism.
  - `--neo-pop-light`: alpha `.5→.65`, blur `14px→22px`, offset `-6px→-10px`.
  - `--neo-pop-dark`: alpha `.4→.55`, blur `26px→30px`, offset `10px→12px`.
  - Mấu chốt: KHÔNG chỉ tăng alpha tại chỗ (sẽ tái phát lỗi che notch ở bugfix-15) — đẩy OFFSET ra
    xa hơn đồng thời, để đỉnh sáng/tối của bóng rơi ra NGOÀI vùng cong notch thay vì đè thẳng lên
    nó. Ràng buộc cấu trúc: `.chat-main` áp mép phải/trên/dưới vào viewport (0 padding từ
    bugfix-12) nên bóng ở 3 cạnh đó gần như bị viewport cắt mất, chỉ cạnh trái (giáp sidebar, có
    notch) là còn "đất" để bóng thật sự hiện ra — độ nổi khối cảm nhận được chủ yếu đến từ đúng
    cạnh này, không phải toàn bộ 4 cạnh như neomorphism cổ điển (vốn giả định vật thể có margin tự
    do quanh cả 4 phía).
  - **Quy tắc thêm vào hệ:** khi cần bóng "nổi" MẠNH hơn cạnh 1 đường cong đã từng bị che, ưu tiên
    tăng OFFSET (đẩy đỉnh bóng ra xa đường cong) hơn là tăng ALPHA tại chỗ — tăng alpha tại chỗ dễ
    tái phát đúng lỗi wash-out vừa sửa; tăng offset vừa mạnh hơn vừa an toàn hơn cho đường cong.
- **2026-08-03 — Bóng tối lệch hue khỏi họ xám trung tính; bóng sáng bị đẩy quá xa thành vệt loang.**
  Người dùng: "chỉnh sao cho div bên phải nổi khối và liền mạch hơn, background đằng sau vẫn hơi
  lệch" rồi cụ thể hoá: "góc dưới thì ok, chỉ lỗi phần màu bg lộ ra, còn góc trên lởm lắm".
  - **Góc dưới-trái (OK, chỉ lệch màu):** `--neo-pop-dark` dùng `rgba(163,177,198,x)` — xanh-xám
    MẶC ĐỊNH của các neomorphism generator phổ biến, nhưng LỆCH hẳn khỏi họ xám trung tính thật của
    hệ này (`--sidebar-bg #f5f5f7`, `--main-bg #fbfefc`, `--border #e5e5e5` đều gần R=G=B). Đổi
    sang `rgba(13,13,13,.28)` — cùng RGB họ với `--text`, đúng tinh thần "không dùng màu ngoài họ
    trung tính" đã áp cho tour-scrim (bugfix-15) và bóng inset sidebar (bugfix-10), giờ áp luôn cho
    bóng nổi.
  - **Góc trên-trái ("lởm hết luôn"):** bugfix-16 đẩy `--neo-pop-light` offset ra `-10px`/blur
    `22px`/alpha `.65` để tránh che đường cong (bài học bugfix-15) — nhưng đi QUÁ XA theo hướng
    ngược lại: mảng trắng gần đặc lớn đến mức đọc như vệt loang/lỗi render, không còn là bóng nổi
    sạch. Hạ về mức vừa phải: offset `-6px`, blur `16px`, alpha `.4`.
  - **Quy tắc thêm vào hệ:** offset/blur/alpha của bóng "nổi khối" có một VÙNG AN TOÀN hẹp giữa 2
    lỗi đối xứng — quá GẦN/quá MẠNH thì đè lên đường cong hình học (bugfix-15); quá XA/quá MẠNH thì
    thành vệt loang tách rời khỏi vật thể (bugfix-17); tăng 1 thông số (offset hoặc alpha) để sửa
    lỗi này phải luôn cân lại các thông số còn lại, không chỉ đẩy 1 chiều. Mọi màu bóng "trung
    tính" trong hệ phải cùng họ RGB với `--text` (`R≈G≈B`), không dùng preset màu ngoài từ
    generator/thư viện dù trông "giống neomorphism" — hệ màu của DỰ ÁN quyết định, không phải quy
    ước ngành.
- **2026-08-03 — Đổi hẳn kỹ thuật bóng nổi: bóng NGOÀI → bóng INSET (bugfix-18, sau 3 lần vá tham
  số liên tiếp vẫn "lệch màu").** Người dùng vẫn báo "lệch màu" sau bugfix-17 (đã retint hue), rồi
  chỉ thẳng vào `.composer-wrap` (đúng vùng góc dưới-trái) — xác nhận đây KHÔNG phải lỗi tham số
  (alpha/blur/hue) mà là lỗi CẤU TRÚC: từ khi `.app` bỏ gap (bugfix-12), `.sidebar` và `.chat-main`
  chạm sát nhau tuyệt đối — bóng NGOÀI với offset ÂM (`-6px -6px`, hướng lên-trái) của `.chat-main`
  không có khoảng trống riêng để vẽ, buộc phải LEM sang đúng bề mặt `.sidebar` (một phần tử khác,
  không hề có shadow riêng) — tạo ra vệt tô màu lạ ngay trên nền sidebar phẳng. Không có tổ hợp
  alpha/blur/offset/màu nào của bóng NGOÀI sửa được việc này, vì bản chất bóng ngoài luôn vẽ tràn
  ra khỏi biên phần tử — sai công cụ, không phải sai số liệu.
  - Đổi `--neo-pop-light`/`--neo-pop-dark` từ bóng ngoài (offset dương/âm, blur lớn) sang bóng
    **inset**: `--neo-pop-light: inset 0 1px 0 rgba(255,255,255,.9), inset 1px 0 0
    rgba(255,255,255,.7)` (2 vệt highlight mảnh dọc cạnh trên+trái — ánh sáng hắt vào mép sheet);
    `--neo-pop-dark: inset -1px -1px 3px rgba(13,13,13,.10)` (bóng tối rất nhẹ góc dưới-phải,
    grounding). Bóng inset CHỈ vẽ TRONG khung phần tử, không bao giờ tràn ra ngoài — tuyệt đối
    không đụng tới `.sidebar` hay notch góc bo (notch giữ nguyên `--app-base-bg=--sidebar-bg`
    thuần, không bị tô thêm).
  - **Quy tắc thêm vào hệ:** khi 1 kỹ thuật CSS đã qua ≥2 lần vá tham số (alpha/blur/offset/màu)
    mà lỗi vẫn tái phát dưới dạng khác, dừng vá tham số — kiểm tra xem kỹ thuật (không phải giá
    trị) có còn phù hợp với cấu trúc layout hiện tại không. Bóng NGOÀI (không inset) giả định phần
    tử có khoảng trống/margin tự do quanh nó để bóng vẽ vào; trong layout FLUSH tuyệt đối (0 gap,
    0 padding, các phần tử chạm sát nhau) giả định đó sai — phải dùng bóng INSET (tự chứa trong
    biên phần tử) cho mọi cạnh giáp trực tiếp một phần tử khác.
- **2026-08-03 — Nút mở sidebar che mất góc bo khi đóng; bevel inset quá mảnh (bugfix-19).** Người
  dùng: "khi đóng thì mất cái cạnh bo góc đi" + "các góc và cạnh nổi khối giờ trông mờ vãi".
  - **Góc bo "biến mất" khi sidebar đóng:** không phải lỗi CSS — `border-radius` trên `.chat-main`
    không hề đổi theo trạng thái collapsed. Nguyên nhân thật: `.sidebar-open` (nút hamburger nổi,
    hiện ra khi sidebar đóng) đặt ở `top:12px;left:12px`, kích thước 34×34 — nằm LỌT HẲN trong vùng
    cung tròn 36px của notch góc trên-trái `.chat-main` (khi đóng, `.chat-main` lấp đầy từ x:0).
    Nút có viền+bóng+bán kính riêng (9px, nhỏ và sắc hơn hẳn cung 36px bên dưới) nên về mặt thị
    giác NUỐT gọn đúng vùng đường cong, tạo cảm giác "góc bo mất". Fix: dời nút ra
    `top:44px;left:44px` (36px bán kính + 8px đệm) — đủ để nút không chồng lên vùng cong nữa.
  - **Bevel "mờ vãi":** bevel inset ở bugfix-18 (1px/1px, alpha .9/.7/.10) quá mảnh để đọc rõ ở cỡ
    chữ/khoảng cách xem thường. Tăng spread lên 2px, alpha đậm hơn:
    `--neo-pop-light: inset 0 2px 0 rgba(255,255,255,.95), inset 2px 0 0 rgba(255,255,255,.85)`;
    `--neo-pop-dark: inset -2px -2px 6px rgba(13,13,13,.2)` — vẫn giữ nguyên kỹ thuật inset (an
    toàn với `.sidebar`/notch, không tái phát lỗi bugfix-15/16/17), chỉ tăng độ đậm.
  - **Quy tắc thêm vào hệ:** mọi phần tử `position:fixed` nổi trên góc của 1 panel có `border-radius`
    lớn phải kiểm tra xem bounding box của nó có chồng lên vùng cung tròn không — 1 phần tử vuông/
    bán kính nhỏ đặt lọt trong 1 cung tròn lớn sẽ luôn "nuốt" cảm giác bo góc của cung lớn, bất kể
    CSS `border-radius` của panel gốc vẫn đúng.
- **2026-08-03 — Notch mồ côi khi sidebar đóng; highlight tách thành 2 vệt thay vì 1 nét bold
  (bugfix-20).** Người dùng: "ở góc bật full màn vẫn nhìn thấy này" (notch vẫn còn khi sidebar đã
  đóng — full width, không còn sidebar để "đẩy") + "kêu nó bold lên chứ có phải là tách làm 2 đâu"
  (highlight 2 khai báo riêng ở bugfix-19 đọc thành 2 vệt kẻ mảnh, không phải ý "bold" ban đầu).
  - **Notch mồ côi:** `border-radius:var(--radius-sheet) 0 0 var(--radius-sheet)` trên `.chat-main`
    không điều kiện theo trạng thái sidebar — khi đóng, `.chat-main` lấp đầy toàn màn nhưng vẫn giữ
    góc bo lớn + notch lộ màu `--sidebar-bg`, dù không còn sidebar nào cạnh đó để "giải thích" cho
    notch — nhìn như 1 vệt xám lạc lõng ở góc màn hình trống. Thêm rule
    `.app.sidebar-collapsed .chat-main{border-radius:0}` — sidebar đóng thì `.chat-main` về vuông
    tuyệt đối, đúng tinh thần "sheet chỉ bo góc khi thật sự có sidebar để đẩy vào".
  - **Highlight tách 2 vệt:** `--neo-pop-light` ở bugfix-19 tách offset-x và offset-y thành 2 khai
    báo `inset` riêng (`inset 0 2px 0 ...` + `inset 2px 0 0 ...`) — dọc theo mỗi cạnh (trên, trái)
    đây là 2 NÉT KẺ MẢNH độc lập, không hợp nhất thành 1 khối liền mạch. Gộp lại thành **1 khai
    báo duy nhất** với offset chéo `inset 2px 2px 0 rgba(255,255,255,.95)` — cùng lúc dịch theo cả
    x và y, cho ra đúng 1 nét bold liền, không phải 2 vệt rời.
  - **Quy tắc thêm vào hệ:** "làm đậm/bold lên" 1 hiệu ứng bevel nghĩa là tăng CƯỜNG ĐỘ của MỘT
    nét duy nhất (offset chéo, alpha cao), không phải nhân thành nhiều khai báo `inset` theo từng
    trục riêng — nhiều khai báo riêng trục sẽ luôn đọc thành các đường kẻ tách rời dọc từng cạnh,
    kể cả khi mỗi đường đủ đậm.
- **2026-08-03 — Bỏ hẳn bevel `.chat-main` sau 5 lần vá liên tiếp (bugfix-21).** Người dùng gửi ảnh
  mobile: "tôi vẫn thấy 2 đường" — ngay cả bản gộp-1-khai-báo ở bugfix-20 vẫn đọc thành 2 đường
  song song: (1) viền cong HÌNH HỌC thật giữa `--main-bg` và backdrop lộ qua notch (luôn tồn tại,
  không thể tắt — đó chính là `border-radius`), và (2) đường bevel offset 2px vẽ chồng lên ngay
  sát viền đó. Bất kỳ bevel offset nào — dù 1 hay nhiều khai báo, dù inset hay ngoài, dù alpha cao
  hay thấp — VẼ THÊM MỘT ĐƯỜNG BÊN CẠNH đường viền thật thì luôn có nguy cơ đọc thành "2 đường",
  đây là giới hạn CỐ HỮU của kỹ thuật (không phải lỗi tham số như 5 lần vá trước tưởng).
  - Xoá hẳn `box-shadow` khỏi `.chat-main` — không còn `--neo-pop-light`/`--neo-pop-dark`. Tín hiệu
    "sheet nổi lên" giờ CHỈ đến từ 2 thứ không thể nhân đôi thành "đường thứ 2": `border-radius`
    (hình dạng) và chênh lệch màu nền `--main-bg` vs `--app-base-bg` (notch). 2 token trên xoá khỏi
    `:root` — không còn nơi nào tham chiếu (token discipline).
  - **Quy tắc thêm vào hệ:** khi 1 kỹ thuật trang trí (bevel/highlight/outline phụ) phải cùng tồn
    tại cạnh MỘT viền hình học đã có sẵn (border-radius, mép panel...), rủi ro "đọc thành nhiều
    đường" là CỐ HỮU chứ không phải do chọn sai tham số — nếu đã thử ≥2 biến thể tham số của cùng
    kỹ thuật mà vẫn bị chê "nhiều đường", câu trả lời đúng thường là BỎ HẲN lớp trang trí phụ, để
    đúng 1 tín hiệu hình học/màu sắc gốc tự nói lên toàn bộ, không thêm gì cạnh tranh với nó.
- **2026-08-04 — Viền xanh lá `:focus-visible` toàn cục lọt qua `textarea{outline:none}`.** Người
  dùng: "bỏ cái border xanh lá trong này đi, khả năng là selected đó" — đúng, `textarea#q` có
  `autofocus`, hiện outline xanh (`var(--accent)`) ngay khi tải trang. Nguyên nhân: rule
  `:focus-visible{outline:2px solid var(--accent)}` toàn cục (accessibility, không đổi) có
  specificity pseudo-class (0,1,0) CAO HƠN `textarea{outline:none}` (0,0,1) — outline:none bị đè dù
  khai báo đúng. Thêm `textarea:focus-visible{outline:none}` — specificity (0,1,1) thắng, chỉ tắt
  outline cho riêng ô nhập composer (đã có viền pill + con trỏ nhấp nháy làm tín hiệu focus), KHÔNG
  đụng tới `:focus-visible` toàn cục của mọi phần tử khác (nút, link, session-item...).
  - **Quy tắc thêm vào hệ:** `outline:none` trên 1 element selector KHÔNG chắc thắng được 1 rule
    `:focus-visible`/pseudo-class toàn cục khai báo sau — phải kiểm tra specificity, không chỉ thứ
    tự khai báo trong file; muốn override đúng 1 phần tử cụ thể, viết lại chính pseudo-class đó
    scoped vào phần tử (`textarea:focus-visible`), không sửa rule toàn cục.
- **2026-08-04 — Tooltip tour vẫn "dính" dù thuật toán tránh chồng lấn đã đúng toán học.** Người
  dùng gửi ảnh khoanh đỏ 2 tooltip (new-chat + sidebar-info, cùng `side:'right'`, đứng gần nhau
  theo chiều dọc): "sao khúc này vẫn dính thế". Thuật toán collision-avoidance (bugfix-6) TÍNH đúng
  — tooltip 2 bị đẩy xuống `p.top + p.height + GAP` khi chồng lấn — nhưng `GAP = 8px` giữa 2 khối
  nền đen sát cạnh nhau vẫn ĐỌC như liền khối bằng mắt thường, dù về mặt toán học không hề chồng
  pixel nào. Tăng `GAP: 8px → 20px`.
  - **Quy tắc thêm vào hệ:** "không chồng lấn về mặt toán học" (0 pixel overlap) và "đọc được là 2
    khối tách biệt bằng mắt" là 2 tiêu chí KHÁC NHAU — với 2 mảng màu đặc (không viền, không đổ
    bóng phân định) đặt cạnh nhau, cần khoảng cách đủ lớn (thường ≥16-20px, không phải 4-8px) mới
    có "khoảng thở" thị giác; thuật toán đúng vẫn có thể tạo kết quả "trông sai" nếu hằng số
    khoảng cách quá nhỏ.
- **2026-08-04 — Scrim tour "xám thô thiển" — alpha .5 quá thấp, pha loãng thành xám đục.** Người
  dùng: "sao cái nền xám dưới nền đen thô thiển vậy?" — xác nhận qua AskUserQuestion đây là lớp
  scrim mờ tour. Ở bugfix-15, scrim đổi từ `rgba(0,0,0,.72)` (đen thuần, bị chê "quá gắt") sang
  `rgba(13,13,13,.5)` — đổi CẢ màu (đen thuần → xám tối theo `--text`) LẪN alpha (.72→.5) trong 1
  bước, không tách riêng 2 biến. Alpha .5 để lộ quá nhiều nền sáng phía sau qua lớp mờ, pha loãng
  thành 1 mảng xám đục — không còn đọc là "lớp dim tối" nữa mà thành "một mảng xám lem nhem". Tăng
  `alpha: .5 → .65`, GIỮ NGUYÊN màu `rgba(13,13,13,...)` (không quay lại đen thuần — giữ đúng bài
  học bugfix-15 rằng đen thuần lệch tông với hệ màu trung tính của trang).
  - **Quy tắc thêm vào hệ:** khi 1 lần sửa trước đổi ĐỒNG THỜI cả màu và alpha để giải quyết 1 khiếu
    nại ("quá gắt"), và lần sau bị khiếu nại NGƯỢC LẠI ("quá nhạt/xám đục"), phải xác định biến nào
    trong 2 biến đó thực sự gây ra từng triệu chứng trước khi chỉnh — ở đây "gắt" đến từ màu (đen
    thuần), "nhạt/đục" đến từ alpha quá thấp; chỉnh đúng biến (tăng alpha, giữ màu) tránh dao động
    qua lại giữa 2 lỗi đối xứng.
- **2026-08-04 — `renderMarkdownLite()` lộ nguyên văn ký tự markdown thô (`#`/`##`, `-`, `1.`, `` ` ``,
  `>`) — phát hiện qua devops_agent (fork của file này), nhưng bug NẰM Ở HÀM DÙNG CHUNG, sửa ở đây.**
  Người dùng gửi ảnh chụp thật: bubble trợ lý hiện đúng "## ✅ Mình CÓ THỂ làm" — 2 dấu # còn nguyên
  văn trước icon, không phải heading thật. Nguyên nhân: bản `renderMarkdownLite()` gốc chỉ xử lý
  `**bold**`/`*italic*`/xuống dòng trên TOÀN CHUỖI 1 lần — không có khái niệm "dòng nào là header/
  list/blockquote", nên `#`/`##`/`###`, `- item`, `1. item`, `` `code` ``, `> quote` đều lọt qua
  nguyên văn (agent tự chọn markdown đầy đủ khi trả lời dù INSTRUCTIONS không ép cú pháp cụ thể).
  - Viết lại thành 2 hàm: `renderInline()` (bold/italic/code — áp dụng inline) + `renderMarkdownLite()`
    xử lý THEO DÒNG (`split('\n')`), nhận diện `^#{1,3}\s` → `<h1-3>`, `^[-*]\s` → `<li>` gom trong
    `<ul>`, `^\d+\.\s` → `<li>` gom trong `<ol>`, `^&gt;\s` → `<blockquote>` (lưu ý: `>` đã bị
    `escapeHtml()` chuyển thành `&gt;` TRƯỚC khi regex chạy — phải match `&gt;`, không phải `>` thô).
  - CSS mới (`.row.assistant .bubble h1/h2/h3/ul/ol/li/code/blockquote`) — dùng LẠI token màu đã có
    (`var(--text)`, `var(--bubble-user)`, `var(--border)`, `var(--text-dim)`), không tạo hex/rgba()
    mới, giữ đúng token discipline của hệ này.
  - Verify: extract ĐÚNG hàm thật từ file (không phải bản gõ tay riêng) chạy qua `node`, xác nhận
    input mẫu giống ảnh chụp màn hình cho output HTML đúng (`<h2>`, `<ul><li>`, `<code>`,
    `<blockquote>` thật, không còn `#`/`` ` ``/`>` thô). `node --check` xác nhận cả 2 file (bản gốc
    + fork devops_agent) parse hợp lệ sau khi sửa.
  - **Áp dụng ĐỒNG BỘ sang `demo_agents/devops_agent/web/chat.html`** (copy nguyên văn 2 hàm + khối
    CSS) — đây là bug ở phần LAYOUT DÙNG CHUNG (không phải delta màu/icon/nội dung riêng của
    devops_agent), nên sửa ở đây trước rồi propagate, đúng quy tắc "1 nguồn sự thật cho phần chung"
    đã lập từ lúc devops_agent fork file này (xem `demo_agents/devops_agent/web/design.md`).
  - **Quy tắc thêm vào hệ:** khi 1 file bị FORK sang agent khác (đã xảy ra với devops_agent), bug ở
    phần code KẾ THỪA (không phải phần delta đã khoá riêng) phải sửa ở bản GỐC trước, rồi propagate
    y hệt sang mọi bản fork — không sửa riêng lẻ từng fork, tránh 2 bản trôi dạt logic theo thời gian.
- **2026-08-26 — Icon mark đổi sang PIXEL ART (rect-grid), giữ nguyên ý nghĩa "đám mây thời tiết".**
  User yêu cầu 3 agent (weather/devops/librarian) cùng chuyển sang 1 hệ icon pixel-art thống nhất,
  sau khi research `/last30days` về xu hướng "AI agent pixel style" (Pixel Agents, AgentRoom — biến
  agent thành nhân vật pixel-art trong văn phòng ảo). Thay `<path>` cong (`M17.5 19a4.5...`,
  `stroke`-based) bằng lưới `<rect>` vuông (`fill`-based, `shape-rendering:crispEdges`) — VẪN vẽ
  hình đám mây (khối trên nhỏ, khối dưới rộng), chỉ đổi kỹ thuật vẽ, không đổi Ý NGHĨA biểu tượng.
  Áp dụng ĐÚNG 4 chỗ như cũ (favicon, empty-state, 2× avatar JS).
  ```html
  <svg viewBox="0 0 8 5"><rect x="3" y="0" width="2" height="1"/><rect x="1" y="1" width="6" height="1"/><rect x="0" y="2" width="8" height="2"/><rect x="1" y="4" width="6" height="1"/></svg>
  ```
  CSS đổi từ `stroke:var(--color-on-accent);fill:none;stroke-width:var(--icon-stroke);stroke-linecap/
  linejoin:round` sang `fill:var(--color-on-accent);stroke:none;shape-rendering:crispEdges`. Áp
  dụng ĐỒNG BỘ sang `devops_agent/web/chat.html` (đổi kỹ thuật vẽ tương tự cho icon vòng vô cực —
  xem `demo_agents/devops_agent/web/design.md` § Icon mark, cập nhật cùng ngày) + icon librarian
  (kính lúp pixel, không thuộc phần "avatar" đã khoá ở đây — xem `wiki/log.md`).
- **2026-08-29 — Icon mark đổi từ icon hình học (đám mây) sang NHÂN VẬT pixel "Clawd-style" (thân
  block trắng + mắt chấm + chân, lấy cảm hứng mascot Clawd của Claude Code) mặc SUIT + CÀ VẠT ĐỎ.**
  User yêu cầu style pixel NHÂN VẬT liên quan chức nghiệp cho cả 3 agent (không phải icon hình học
  đơn giản nữa) — quy trình đầy đủ + ~30 vòng Design Feedback nằm ở `wiki/log.md` (entry
  "2026-08-28 — feature — clawd-pixel-character-avatars..."), rồi trích xuất thành skill
  `/create-agent-avatar` (`.claude/skills/create-agent-avatar/SKILL.md`) + engine dùng chung
  `harness/scripts/pixel_icon_gen.py`. Weather: research ảnh thật cho thấy weatherman KHÔNG đội/đeo
  gì đặc trưng — chỉ suit + cà vạt (khác hẳn giả định ban đầu "mascot đội mũ mây"). Sinh markup qua
  `python3 harness/scripts/pixel_icon_gen.py` → `build_icon_svg('weather')`, KHÔNG gõ tay toạ độ
  `<rect>` (đổi cấu trúc nhân vật phải sửa `AGENTS['weather']` trong file đó trước, rồi generate
  lại — không sửa trực tiếp SVG trong `chat.html`).
  ```html
  <svg viewBox="0 0 10 7" shape-rendering="crispEdges"><g fill="#ffffff"><rect x="1" y="0" width="8" height="1"/><rect x="0" y="1" width="10" height="1"/><rect x="1" y="2" width="8" height="1"/><rect x="1" y="3" width="8" height="1"/><rect x="1" y="4" width="8" height="1"/><rect x="1" y="5" width="8" height="1"/><rect x="1" y="6" width="1" height="1"/><rect x="3" y="6" width="1" height="1"/><rect x="6" y="6" width="1" height="1"/><rect x="8" y="6" width="1" height="1"/></g><g fill="#1a1a1a"><rect x="2" y="1" width="1" height="1"/><rect x="7" y="1" width="1" height="1"/></g><g fill="#1E3A5F"><rect x="1" y="3" width="8" height="1"/><rect x="1" y="4" width="8" height="1"/><rect x="1" y="5" width="8" height="1"/></g><g fill="#DC2626"><rect x="4" y="3" width="2" height="1"/><rect x="4" y="4" width="1" height="1"/><rect x="4" y="5" width="1" height="1"/></g></svg>
  ```
  Nhân vật giờ có MÀU RIÊNG cho từng phần (thân trắng, mắt đen, suit navy `#1E3A5F`, cà vạt đỏ
  `#DC2626`) thay vì 1 màu đơn `fill:var(--color-on-accent)` kế thừa từ accent — CSS
  `.avatar.assistant svg{fill:var(--color-on-accent)}` / `.empty-state .icon svg{...}` VẪN GIỮ
  NGUYÊN (không xoá) vì màu inline trên từng `<g>` con LUÔN THẮNG màu kế thừa từ `<svg>` cha theo
  đúng cơ chế CSS inheritance — không cần sửa CSS, chỉ cần confirm hành vi này qua browser thật
  trước khi coi là xong. Áp dụng ĐÚNG 4 chỗ như cũ (favicon — viewBox nền 32×32 đổi theo tỉ lệ khung
  nhân vật mới, empty-state, 2× avatar JS).
- **2026-08-29 (tiếp) — Icon librarian trong step-indicator (`TOOL_STEPS.ask_librarian`) đổi từ
  kính lúp pixel cũ sang NHÂN VẬT librarian đã khoá (mũ cử nhân + kính một mắt + tua).** User phát
  hiện icon này bị bỏ sót ở lượt áp avatar chuẩn cho weather/devops (lượt trước chỉ đổi avatar
  CHÍNH của agent, không đụng badge nhỏ gọi sang librarian). Sinh markup qua
  `build_icon_svg('librarian')`. Đồng thời tăng size render từ 11px→15px
  (`.step-indicator.step-librarian .step-icon svg`) vì nhân vật nhiều màu/chi tiết hơn hẳn kính
  lúp đơn sắc cũ — so sánh trực quan 11/15/18px cho thấy 15px là mức nhỏ nhất vẫn đọc rõ mũ+tua+
  monocle, badge tròn (20px) giữ nguyên không đổi. Áp dụng ĐỒNG BỘ sang
  `devops_agent/web/chat.html` (xem file đó § Icon librarian, cùng ngày).

## Exports
`tokens.css` (trong `demo_agents/weather_agent/web/`) là source of truth, nhưng KHÔNG được
`<link>` trực tiếp từ `chat.html`/`index.html` — cả hai file cố ý self-contained một-file-duy-nhất
(quy ước xuyên suốt dự án: docs site, demo agent... đều mở được qua `file://` hoặc server tối giản
không phục vụ static asset phụ). `tokens.css` dùng để tham chiếu/đối chiếu khi sửa — khi đổi giá
trị, phải sửa cả 3 nơi (tokens.css + 2 khối `:root` inline) cho khớp nhau.

## Notes
- `hallmark audit chat.html` (2026-08-03) tìm ra 10 lỗi (3 critical, 3 major, 4 minor) — token
  discipline, thiếu breakpoint mobile, session-item không thao tác được bằng bàn phím, nút xoá
  chỉ hiện khi hover, stroke-width icon không đồng nhất, z-index tuỳ tiện, main-bg trắng tuyệt
  đối, `width:100vw` thừa trên phần tử `position:fixed`. Đã sửa hết cả 10 trước khi khoá file này.
- Font đơn (không cặp display/body) là quyết định có chủ đích, không phải model quên cặp font —
  bám theo yêu cầu gốc "copy theme của ChatGPT" (ChatGPT thật cũng chỉ dùng một họ, Söhne — không
  public/không tải được qua CDN theo quy tắc self-contained của dự án).
- **Phát hiện thêm sau khi khoá (2026-08-03, qua feedback người dùng thật trên trang chạy):**
  1. Overlay dạng spotlight (product tour) phủ toàn màn hình kể cả vùng đang sáng — bấm vào phần
     tử thật đang được tô sáng chỉ đóng overlay chứ không thực hiện hành động, phải bấm 2 lần.
     **Quy tắc thêm vào hệ:** mọi overlay kiểu spotlight/coach-mark PHẢI dùng `clip-path` khoét lỗ
     đúng vùng đang sáng để click lọt xuống phần tử thật — không được dùng một lớp phủ kín che hết
     màn hình rồi chỉ đóng khi bấm.
  2. `.session-item` padding ngang 10px lệch nhịp 12px dùng ở mọi phần tử khác trong sidebar (bug
     tĩnh); nút xoá toggle `display:none→flex` lúc hover làm `.stitle` bị đẩy/co đột ngột (bug
     hover — layout shift). **Quy tắc thêm vào hệ:** phần tử hiện/ẩn theo hover/focus trong một
     hàng flex/grid phải giữ `display` cố định, chỉ đổi `opacity`+`pointer-events` — không đổi
     `display` (thay đổi layout tham gia flow, gây dịch chuyển các phần tử lân cận).
  3. Span đường dẫn dài (`sidebar-foot`) không co được, đội nút "?" tràn ra ngoài
     `overflow:hidden` của sidebar → nút bị che khuất hoàn toàn (không phải chỉ tràn nhìn xấu, mà
     mất hẳn khả năng bấm). Nguyên nhân: flex item mặc định `min-width:auto`, không co dưới độ
     rộng nội dung dù đã có `flex-shrink`. **Quy tắc thêm vào hệ:** mọi text dài không kiểm soát
     được (đường dẫn, tên file, tiêu đề động) nằm cạnh phần tử cố định trong một hàng flex PHẢI có
     `min-width:0` + `overflow:hidden;text-overflow:ellipsis;white-space:nowrap` trên chính span
     đó — không chỉ dựa vào flex-shrink. Ưu tiên rút gọn kiểu "đầu…cuối" (giữa) thay vì chỉ cắt
     cuối khi cả phần đầu (ngữ cảnh) lẫn phần cuối (định danh cụ thể) đều cần giữ lại — xem
     `middleEllipsis()` trong `chat.html`.
  4. Listener đóng tour gắn ở `document.addEventListener('click', ..., true)` (capture, toàn
     trang) để bắt click lọt qua lỗ clip-path — nhưng bắt luôn CẢ những click chẳng liên quan gì
     tới tour (vd công cụ inspect/feedback bên ngoài click để chọn phần tử), remove DOM giữa
     chừng khiến node bị tách khỏi tài liệu (`getBoundingClientRect()` trả về `0x0`) trước khi bên
     ngoài kịp đọc. **Quy tắc thêm vào hệ:** không gắn listener đóng ở `document`/`window` cho một
     overlay chỉ cần đóng khi tương tác với MỘT TẬP phần tử cụ thể — gắn trực tiếp vào từng phần
     tử đó (`el.addEventListener('click', close, {once:true})`), phạm vi hẹp nhất có thể.
  5. Quét token-discipline đợt đầu chỉ bắt màu hex (`#...`), bỏ sót 12+ chỗ `rgba()` thô rải rác
     (border/shadow/overlay alpha). **Quy tắc thêm vào hệ:** khi audit token discipline, quét CẢ
     hex LẪN `rgba()`/`hsla()` — không chỉ một dạng cú pháp màu.
  6. `.sidebar{white-space:nowrap}` (thêm để chữ khỏi vỡ dòng lúc animate collapse-width) BỊ KẾ
     THỪA xuống `.sidebar-section` — đoạn mô tả dài không xuống dòng được nữa, tràn ngang rồi bị
     cắt bởi `overflow:hidden` của `.sidebar` cha. **Quy tắc thêm vào hệ:** `white-space:nowrap`
     đặt ở container cha (cho mục đích layout/animation của CHÍNH container đó) PHẢI đi kèm
     `white-space:normal` tường minh trên mọi khối text-dài/prose con bên trong — không được để
     nowrap tự kế thừa xuống nội dung cần wrap tự nhiên.
  7. Hai tooltip tour kề nhau theo chiều dọc (nút "Cuộc trò chuyện mới" và khối mô tả agent), cả
     hai cùng đặt bên phải (`side:'right'`) — vị trí tính ĐỘC LẬP cho từng cái (theo tâm dọc của
     chính spot đó) nên khi 2 spot gần nhau, 2 tooltip chồng đè lên nhau, chữ không đọc nổi.
     **Quy tắc thêm vào hệ:** vị trí tooltip trong MỘT overlay nhiều điểm phải tính THEO LÔ (đo hết
     rồi mới đặt), có bước tránh chồng lấn giữa các tooltip với nhau — không chỉ tránh tràn viewport
     mà còn phải tránh tràn lên NHAU. Thứ tự khai báo các spot phải khớp thứ tự thị giác trên↔dưới
     thật, không thì thuật toán đẩy-xuống sẽ đặt sai hướng.
