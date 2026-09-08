---
type: concept
title: "Skill `/create-agent-avatar` — sinh avatar pixel-art Clawd-style cho agent mới"
tags: [skill, ui, design-system, pixel-art, harness]
timestamp: 2026-08-28
---

# create-agent-avatar-skill

Skill dự án (không phải skill cá nhân) đặt tại `.claude/skills/create-agent-avatar/SKILL.md`, dùng
chung engine `harness/scripts/pixel_icon_gen.py`. Gọi qua `/create-agent-avatar` khi cần
tạo/đổi avatar nhân vật pixel cho 1 demo agent — không dùng cho icon hình học đơn giản
(cloud/gear/magnifier, đó là việc chỉnh trực tiếp `chat.html`).

## Vì sao tồn tại

Trích xuất từ phiên thiết kế 3 avatar chính thức của dự án (weather/devops/librarian) — ~30 vòng
Design Feedback, nhiều lỗi LẶP LẠI (phụ kiện "chạm mắt", mũ "lơ lửng") trước khi rút ra được luật
chung. Mục đích: agent MỚI sau này không phải trả giá lại cùng những lỗi đó.

## 5 luật cốt lõi (đọc SKILL.md để có đầy đủ quy trình 7 bước + ví dụ code)

1. **Không phụ kiện nào chung hàng/ngay sát hàng mắt** trừ khi hàng đó TRẮNG HOÀN TOÀN — vi phạm
   luật này đã gây lỗi "chạm mắt" 4 lần liên tiếp (mic, tai nghe, kính, ve áo) trong phiên gốc, chỉ
   lộ rõ ở kích thước avatar thật (~24-30px), không thấy ở bản zoom lớn lúc thiết kế.
2. **Mỗi hàng của `hat` luôn ĐẶC, không hàng đệm gần-rỗng** — thêm 1 hàng "phụ kiện" chỉ vài ô tô
   màu giữa mũ và đầu từng bị hiểu nhầm là mũ lơ lửng cách đầu 1 khe hở.
3. **`hat` phải HẸP HƠN đầu, CAO hơn, và dùng pixel MỊN HƠN thân** (`hat_subdiv`) — rút ra sau khi
   user gửi ảnh mô hình Clawd thật đội top hat: mũ thật hẹp hơn hẳn đầu, cao hơn, và làm từ voxel
   nhỏ hơn hẳn khối thân — không phải phóng to cùng cỡ lưới. Xem `hat_subdiv` trong `AgentIcon`.
4. **`accessories` nhận toạ độ LẺ trực tiếp, không cần cơ chế subdiv riêng** — user yêu cầu áp pixel
   mịn cho "tất cả phụ kiện quần áo, không chỉ mũ"; hoá ra hệ rect đã hỗ trợ số thực sẵn (vd `0.25`)
   — chỉ cần DÙNG, không cần sửa engine. Badge "SEC"/"HR" từng phải thay bằng chữ vì icon 1-đơn-vị
   quá thô để đọc; vẽ lại ở độ phân giải phần tư-đơn-vị (khiên bảo mật, thẻ+lanyard) → quay lại icon
   thật, không cần chữ nữa. Chỉ áp cho chi tiết/badge nhỏ — mảng màu phẳng lớn (suit, belt) không
   cần độ phân giải này.
5. **`hat_subdiv` cho phép sculpt chi tiết hơn — nhưng KHÔNG có nghĩa dùng chung 1 khuôn cho mọi
   agent** — lỗi đã mắc: mọi `hat` (glasses/beret/headset/visor) đều vẽ theo cùng 1 tam giác thóp
   nhọn dần, chỉ khác màu → user: "mấy cái nón nhìn na ná nhau... kính và vòm tai nghe giờ cũng
   không tưởng tượng ra nổi". Phải tự hỏi hình dạng THẬT của từng vật trước khi vẽ (kính thấp-rộng
   2 tròng riêng; beret dome tròn phồng; headset dải mỏng cong; visor thấp-ngang; hoodie mới thật sự
   nhọn) — CHIỀU CAO cũng nên khác nhau theo tỉ lệ thật, không đồng loạt ~3 đơn vị như nhau.

## Sản phẩm liên quan

- `harness/scripts/pixel_icon_gen.py` — engine (dataclass `AgentIcon` với `hat_subdiv`, `AGENTS`,
  `VARIANTS`, `build_gallery_html()`).
- `llmwiki/html/280826-clawd-icon-gallery.html` — snapshot gallery: 3 avatar chính thức (weather
  suit+tie, devops kính vô cực+belt, librarian mortarboard+monocle) + 8 agent test + 24 biến thể
  màu.

## Origin
- **Phiên thiết kế gốc:** `wiki/log.md`, entry "2026-08-28 — feature —
  clawd-pixel-character-avatars-and-create-agent-avatar-skill".
- **Trích xuất theo yêu cầu user:** "trích xuất thành skill tạo /create-agent-avatar" → "update vào
  skill là tạo vào wiki luôn và đăng ký nó như skill của wiki và repo này" (trang này là kết quả của
  yêu cầu đăng ký thứ 2).
