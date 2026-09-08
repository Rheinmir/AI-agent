---
type: concept
title: Click-Depth Pyramid — số click đo chất lượng UI
tags: [ui-ux, design-rule, wiki, librarian]
timestamp: 2026-08-05
---

# Click-Depth Pyramid — số click đo chất lượng UI

Rule đo UI: **số lần bấm để tới nội dung người dùng CẦN nhất = điểm chất lượng** — càng ít click
càng tốt. Nội dung xếp thành hình kim tự tháp: cái quan trọng/dùng thường xuyên nằm ở ĐỈNH (0-1
click), cái ít cần hơn/chuyên sâu hơn nằm CÀNG XUỐNG ĐÁY càng phải bấm thêm để tới — không hiện mặc
định, không chiếm chỗ tầng nhìn thường.

Rule này tách biệt 2 lớp độc lập với nhau:

- **Display layer** (tầng nhìn) — thứ user thấy, phải NÔNG, tối ưu cho việc thường làm nhất.
- **Storage layer** (tầng lưu trữ thật) — cấu trúc file/thư mục bên dưới có thể sâu/phức tạp hơn
  nhiều so với display layer, MIỄN LÀ độ sâu đó không rò rỉ lên UI. 2 lớp này không cần đối xứng
  1-1.

## Ví dụ áp dụng — wiki linted/raw

`/wiki` của từng agent (xem [[agent-7-layers]] § Data Collector, `demo_agents/{weather,devops}_agent/
wiki/`): mỗi topic có thể có 2 file trên đĩa — `<slug>.md` (bản đã lint/distill, sạch, có
frontmatter đầy đủ) và `<slug>-raw.md` (bản gốc chưa qua xử lý — text lộn xộn, dump thô). Display
layer CHỈ liệt kê bản linted trong sidebar (đỉnh pyramid — 1 click từ trang chủ wiki là thấy nội
dung cần). Bản raw KHÔNG xuất hiện trong danh sách mặc định — chỉ tới được qua 1 link "Xem bản gốc"
đặt trên trang linted (đáy pyramid — cố ý thêm 1 click, vì đây là nội dung tham khảo/audit, không
phải thứ user cần thường xuyên).

Vị trí lưu trên đĩa của 2 file này có thể sâu hơn hẳn cấu trúc phẳng cũ (vd
`wiki/sources/<slug>/<slug>.md` thay vì `wiki/sources/<slug>.md`) — storage layer được tự do tổ
chức lại mà KHÔNG ảnh hưởng số click của display layer, vì sidebar nhóm theo `type`/`title` trong
frontmatter, không theo đường dẫn vật lý.

## Cách đo (khi review 1 UI)

Đặt câu hỏi: "hành động phổ biến nhất của user trên màn này là gì?" → đếm số click từ điểm vào tới
lúc hoàn thành hành động đó. Số càng lớn, điểm càng thấp — không quan trọng UI có bao nhiêu tính
năng ẩn sâu bên dưới, miễn tính năng CHÍNH luôn ở gần đỉnh.

## Origin
- Người dùng đặt ra khi thiết kế luồng librarian agent (đối chiếu wiki riêng từng agent): "tầng
  nhìn của user lúc bth chỉ là topic sau lint, còn muốn coi raw thì mới phải mất thêm 1 step... số
  lượt click phải click càng nhiều để tiếp cận tới nội dung cần thiết thì điểm càng thấp, kim tự
  tháp cho nội dung user muốn hiển thị". Áp dụng đầu tiên vào `wiki_lib.py` (ẩn `*-raw.md` khỏi
  sidebar mặc định) — xem `wiki/log.md` entry liên quan tới librarian agent.
