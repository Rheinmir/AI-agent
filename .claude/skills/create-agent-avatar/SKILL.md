---
name: create-agent-avatar
description: Sinh avatar pixel-art "Clawd-style" (thân block trắng dùng chung, phụ kiện riêng theo chức nghiệp) cho 1 demo agent mới, dùng chung engine `harness/scripts/pixel_icon_gen.py`. Dùng khi user yêu cầu tạo/đổi icon-nhân-vật cho agent (không phải icon hình học đơn giản như cloud/gear).
---

# create-agent-avatar

Trích xuất từ phiên thiết kế 3 avatar weather/devops/librarian (~30 vòng Design Feedback, xem
`harness/scripts/pixel_icon_gen.py` + `llmwiki/wiki/log.md`). Mọi luật dưới đây là kết quả THẬT của
lỗi đã mắc và được user chỉ ra bằng ảnh/screenshot cụ thể — không phải best-practice lý thuyết.

## Khi nào dùng

User yêu cầu tạo avatar/icon nhân vật cho 1 agent mới, hoặc đổi phụ kiện/màu của agent đã có trong
`AGENTS` (`harness/scripts/pixel_icon_gen.py`). KHÔNG dùng cho icon hình học đơn giản (favicon dạng
khối/gear/magnifier) — đó là việc khác, chỉnh trực tiếp trong `chat.html` của agent.

## Quy trình 7 bước (làm ĐÚNG THỨ TỰ — mỗi bước tồn tại vì đã có lỗi thật ở bước đó)

### 1. Research ảnh tham khảo THẬT trước khi thiết kế — KHÔNG đoán stereotype

Lỗi đã mắc: đoán "devops = kỹ sư đội nón bảo hộ" và "weather = mascot đội mũ mây" mà không tra —
cả 2 đều SAI khi user gửi ảnh thật (weatherman thật mặc suit không đội gì; devops thật trong minh
hoạ đeo kính, không phải nón bảo hộ — nón bảo hộ là kỹ sư xây dựng).

Trước khi vẽ, `WebSearch` xem chức nghiệp này THẬT SỰ được vẽ/chụp như thế nào (tìm ảnh chân dung
thật + minh hoạ flat-design phổ biến cho vai trò đó). Nếu user tự gửi ảnh tham khảo, ƯU TIÊN ảnh đó
tuyệt đối — không thay bằng suy đoán riêng dù kết quả WebSearch khác.

### 2. Chọn phụ kiện SIGNATURE — 1 cái đủ để nhận diện, không cần nhiều

Mỗi agent chỉ cần 1 phụ kiện đặc trưng đủ mạnh (mây+mưa, kính hình vô cực CI/CD, mũ cử nhân). Có
thể thêm phụ kiện phụ ở vùng THÂN (không phải đầu) nếu cần thêm "signature" (vd belt+cờ lê cho
devops) — nhưng LUÔN đặt cách xa vùng mắt (xem luật #4).

### 3. Dựng bằng `AgentIcon` — KHÔNG tự vẽ `<rect>` tay

Sửa `harness/scripts/pixel_icon_gen.py`, thêm 1 entry mới vào `AGENTS` (dict ở đầu file):

```python
"ten_agent": AgentIcon(
    name="ten_agent",
    hat=[...],              # xem luật #4-5 bên dưới — có thể để [] nếu không đội gì
    hat_color="#RRGGBB",
    hat_highlight="#RRGGBB",
    body_gradient=("#RRGGBB", "#RRGGBB"),  # màu badge nền, tương phản với hat_color
    label="Tên hiển thị — mô tả ngắn phụ kiện",
    accessories=[
        ("#RRGGBB", [(x, y, w, h), ...]),   # nhóm 1 (vd belt)
        ("#RRGGBB", [(x, y, w, h), ...]),   # nhóm cuối = SIGNATURE, đè lên trên
    ],
),
```

`CLAWD_BODY`, `EYES` là DÙNG CHUNG — KHÔNG sửa (mọi agent phải cùng 1 thân/mắt/chân để nhất quán
theo bộ, đây là quyết định thiết kế đã chốt, không phải giới hạn kỹ thuật).

**Mẹo — `(x, y, w, h)` trong `accessories` KHÔNG bắt buộc là số nguyên.** Hệ render vẽ thẳng ra
`<rect>` SVG nên nhận toạ độ LẺ (vd `0.25`, `0.4`) — dùng NGAY khi 1 badge/chi tiết cần độ phân
giải cao hơn 1 đơn vị thân (huy hiệu, biểu tượng cong, dụng cụ nhỏ) — KHÔNG cần cơ chế `subdiv`
riêng như `hat` (xem LUẬT SỐ 3), chỉ hat mới cần `hat_subdiv` vì hat dùng lưới string. Design
Feedback: badge "SEC"/"HR" ban đầu phải thay bằng CHỮ vì icon 1-đơn-vị quá thô để đọc — sau khi vẽ
lại bằng toạ độ phần tư-đơn-vị (0.25), cả 2 quay về ICON THẬT (khiên bảo mật, thẻ+lanyard) rõ ràng
hơn hẳn, không cần chữ nữa. Mảng màu PHẲNG lớn (suit, belt) thì KHÔNG cần độ phân giải này — chỉ áp
cho chi tiết/badge nhỏ cần đường cong hoặc hình dạng phức tạp.

### 4. LUẬT SỐ 1 (mắc lỗi này 4 LẦN liên tiếp trong phiên gốc — đọc kỹ): không phụ kiện nào được
   nằm CHUNG HÀNG với mắt hay hàng NGAY SÁT DƯỚI mắt nếu không phải trắng 100%

`EYES` nằm ở `row1` của `CLAWD_BODY` (tương đối, cộng thêm chiều cao `hat` khi ghép). Bất kỳ pixel
tối màu nào ở CHÍNH cột mắt (col2/col7, tương đối theo hat_h) tại `row0` (ngay trên mắt) hoặc
`row2` (ngay dưới mắt) sẽ NHÌN NHƯ dính liền vào mắt ở kích thước avatar thật (~24-30px) — dù ở bản
zoom lớn (300px+) trông tách biệt rõ ràng. Đây là lỗi ĐÃ XẢY RA với: cần mic tai nghe (weather),
băng tai nghe (weather, lần 2), ve áo vest (weather, lần 3), kính đeo mắt (devops), cờ lê chạm kính
(devops) — tất cả đều do vi phạm luật này.

**Cách tuân thủ, chọn 1 trong 2:**
- (a) Nếu phụ kiện thuộc vùng ĐẦU (kính, mũ, tai nghe...): đặt vào `hat` (xem luật #5) — `hat`
  LUÔN nằm phía trên `CLAWD_BODY`, tự động cách hàng mắt ít nhất `hat_h` hàng, không bao giờ dính.
- (b) Nếu phụ kiện thuộc vùng THÂN (cà vạt, belt, huy hiệu...): coordinate `y` bắt đầu từ **row3
  trở xuống** (row2 để TRẮNG HOÀN TOÀN — không riêng gì cột mắt, cả hàng luôn, kể cả phần phụ kiện
  không đè đúng cột mắt vẫn phải tránh vì đây là "vùng nguy hiểm" đã xác nhận qua nhiều lần sửa).

Tự kiểm TRƯỚC khi build: liệt kê mọi `(x, y, w, h)` trong `accessories`, nếu `y == 0`, `y == 1`,
hay `y == 2` (tương đối CLAWD_BODY, tức ngay trên/ngay dưới mắt) → SAI, dời xuống `y >= 3` hoặc
chuyển sang `hat`.

### 5. LUẬT SỐ 2: MỖI HÀNG của `hat` phải ĐẶC (không có ô rỗng ngoài viền), KHÔNG BAO GIỜ 1 hàng
   gần-rỗng

Lỗi đã mắc: thêm 1 hàng "phụ kiện" chỉ có 2-3 ô tô màu trong 10 ô, còn lại TRONG SUỐT → lộ nền
badge ngay giữa mũ và đầu → nhìn như mũ LƠ LỬNG cách đầu 1 khe hở.

Mỗi hàng trong `hat` phải gần kín (dùng `#` liên tục cho phần thân chính, viền `.` chỉ ở 2 mép
ngoài cùng) — hàng CUỐI của `hat` PHẢI chạm thẳng vào `CLAWD_BODY[0]` (không hàng đệm rỗng ở
giữa). Muốn thêm chi tiết phụ (giọt mưa, nút quai...) → vẽ ĐÈ LÊN bằng `accessories` với `y` âm
(tương đối `CLAWD_BODY`, sẽ tự cộng `hat_h` khi render) chứ KHÔNG thêm 1 hàng rời rạc vào `hat`.

### 6. LUẬT SỐ 3: `hat` phải HẸP HƠN đầu, CAO hơn 2 hàng, và dùng PIXEL MỊN HƠN thân (`hat_subdiv`)

Design Feedback (user gửi ảnh mô hình Clawd thật đội top hat), 2 vòng liên tiếp: (1) "tỉ lệ nón
với Clawd như vậy mới hợp lý, sao mình làm mũ khổ thế" — bản đầu mọi `hat` đều RỘNG BẰNG ĐẦU
(`.########.`, khớp `CLAWD_BODY[0]`) và chỉ 2 hàng DẸT, khác hẳn ảnh thật (mũ hẹp hơn hẳn đầu +
cao hơn); (2) sau khi thu hẹp bằng đúng lưới 10-cột vẫn CHƯA ĐÚNG Ý — "accessory chọn bộ chia
pixel nhỏ hơn thay vì to ngang với thân" — mũ THẬT làm từ voxel NHỎ HƠN HẲN khối thân, không phải
cùng cỡ ô phóng to.

**Cách làm đúng — dùng `hat_subdiv` (mặc định 1, dùng cho agent không có mũ/`hat=[]`):**

```python
"ten_agent": AgentIcon(
    ...,
    hat_subdiv=2,  # mỗi ký tự trong `hat` chỉ chiếm 1/2 đơn vị thân — lưới MỊN GẤP ĐÔI
    hat=[
        # 6 hàng x 20 cột (= 3 hàng x 10 cột TÍNH THEO ĐƠN VỊ THÂN, nhờ subdiv=2)
        "........####........",  # 0 đỉnh (highlight) — HẸP NHẤT, không chạm mép nào
        ".......######.......",  # 1
        "......########......",  # 2
        "......########......",  # 3
        ".....##########.....",  # 4
        ".....##########.....",  # 5 hàng CUỐI — chạm thẳng vào đầu, vẫn hẹp hơn hẳn đầu (10/20≈5
        #                            đơn vị thân, so với đầu rộng 8)
    ],
    ...
),
```

Quy tắc cụ thể:
- Mỗi hàng string phải dài ĐÚNG `10 * hat_subdiv` ký tự (vd subdiv=2 → 20 ký tự/hàng) — SAI độ dài
  sẽ lệch toàn bộ lưới khi render, tự kiểm bằng `len(row) == 10 * hat_subdiv` trước khi build.
- **KHÔNG dùng CHUNG 1 khuôn "thóp nhọn dần" cho mọi agent** — lỗi ĐÃ MẮC: bản đầu áp cùng 1 kiểu
  tam giác thóp-lên-đỉnh cho glasses/beret/headset/visor, chỉ đổi màu → user chỉ ra: "mấy cái nón
  nhìn na ná nhau... đến cả kính và vòm trên tai nghe giờ cũng không tưởng tượng ra nổi nữa". Có
  `hat_subdiv` KHÔNG có nghĩa mọi mũ phải nhọn — nó chỉ cho phép SCULPT hình dáng THẬT của từng phụ
  kiện chi tiết hơn. Trước khi vẽ, tự hỏi: vật này THẬT SỰ có hình gì? Vài mẫu tỉ lệ đã dùng (khác
  hẳn nhau, không phải công thức cố định):
  - **Kính (glasses)** — THẤP + RỘNG, 2 khối tròng RÕ RỆT tách biệt ở hàng TRÊN CÙNG rồi mới gộp
    gọng bên dưới — KHÔNG nhọn dần từ 1 điểm.
  - **Mũ nồi (beret)** — DOME TRÒN PHỒNG ngay gần đỉnh (rộng luôn, không thóp), chỉ 1 cục tem nhỏ
    lệch 1 bên mới nhọn.
  - **Băng tai nghe (headset)** — MỎNG (1-2 hàng, thấp hơn hẳn các mũ khác), cong nhẹ, không dày
    thành khối.
  - **Vành visor** — THẤP + RỘNG NGANG hơn cao (brim chiếu thẳng ra), khác beret ở tỉ lệ ngang>dọc.
  - **Mũ trùm (hoodie)** — CAO + nhọn dần thật (đây là kiểu DUY NHẤT hợp lý dùng khuôn thóp).
- `hat_subdiv=2` là mức mặc định khuyến nghị (đủ mịn để thấy rõ khác biệt với thân, không quá vụn
  vặt khó đọc ở size avatar thật ~24-30px) — chỉ tăng lên 3+ nếu thật sự cần chi tiết tinh hơn, và
  PHẢI tự kiểm QuickLook ở mini scale trước khi chốt (subdiv càng cao, chi tiết càng dễ vỡ hình ở
  size nhỏ).
- **Chiều cao (`len(hat)/hat_subdiv`) cũng nên KHÁC NHAU giữa các agent** theo đúng tỉ lệ thật của
  vật đó (headset/visor thấp ~1 đơn vị; glasses ~2; beret/hoodie cao ~3) — chiều cao giống hệt nhau
  hàng loạt cũng là 1 dấu hiệu "dùng chung khuôn" cần tránh.
- Vẫn áp dụng NGUYÊN LUẬT SỐ 2 (mỗi hàng đặc, không khe hở, hàng cuối chạm thẳng đầu) — subdiv chỉ
  đổi ĐỘ MỊN của lưới, không đổi nguyên tắc "đặc, không khe hở".
- Agent nào KHÔNG có phụ kiện đầu thật sự (vd weather mặc suit không đội gì, legal/HR/sales cũng
  vậy — xem các agent này trong `AGENTS`) thì để `hat=[]`, không cần `hat_subdiv`.

Ví dụ đúng (weather gốc, đã bỏ — xem lịch sử) — mũ mây 2 hàng đặc, giọt mưa vẽ đè lên hàng cuối
bằng `accessories=[("#0369A1", [(2, -1, 1, 1), (7, -1, 1, 1)])]` (không thêm hàng rỗng).

### 7. Tự kiểm QuickLook TRƯỚC khi cho user xem — bắt buộc, không được bỏ qua

```bash
python3 harness/scripts/pixel_icon_gen.py --gallery /tmp/gallery.html   # xem 3 chuẩn + variant
# hoặc, khi đang thiết kế 1 agent cụ thể:
python3 -c "
import sys; sys.path.insert(0, 'harness/scripts')
from pixel_icon_gen import build_icon_svg
svg = build_icon_svg('ten_agent')
open('/tmp/zoom.html','w').write(f'<meta charset=\"utf-8\"><style>body{{margin:0;background:#0f1115;display:flex;align-items:center;justify-content:center;height:100vh}}svg{{width:400px;shape-rendering:crispEdges}}</style>{svg}')
"
qlmanage -t -s 1200 -o /tmp/ql /tmp/zoom.html   # rồi Read ảnh PNG sinh ra, TỰ soi lỗi trước
```

Soi ở CẢ 2 mức: zoom lớn (400px, dễ thấy chi tiết) VÀ mini (~22-30px, đúng kích thước avatar thật
trong chat UI) — lỗi "chạm mắt"/"lơ lửng" thường CHỈ lộ ra ở mini, không thấy ở bản zoom lớn. Chỉ
publish Artifact cho user xem SAU KHI đã tự soi cả 2 mức và không thấy vấn đề.

## Sinh nhiều biến thể màu nhanh (không cần thiết kế lại hình dạng)

```python
from pixel_icon_gen import AGENTS, _with_accessory_color
variant = _with_accessory_color(AGENTS["ten_agent"], "#RRGGBB", group_index=-1)  # -1 = nhóm cuối
```

`group_index` mặc định `-1` (nhóm SIGNATURE, luôn khai cuối cùng trong `accessories`). Việc này AN
TOÀN vì chỉ đổi màu, giữ nguyên toạ độ đã kiểm chứng — biến thể HÌNH DẠNG khác (đổi kiểu phụ kiện)
phải làm thủ công qua bước 3-6, không sinh hàng loạt tự động.

## Áp dụng vào chat.html thật (sau khi user CHỐT thiết kế)

1. Cập nhật `design.md` của agent đó TRƯỚC (nếu agent có quy tắc "mọi đổi icon phải qua design.md
   trước" — xem `demo_agents/devops_agent/web/design.md`).
2. Thay các vị trí: `<link rel="icon">` favicon data-URI, `.empty-state .icon svg`, mọi
   `.avatar.assistant svg` trong JS (thường có ở cả `addRow` và typing-row function).
3. Restart server, hard-refresh, verify sống — KHÔNG báo "xong" chỉ dựa vào đọc code.
4. Viết Output Report (bước dưới) — KHÔNG chỉ ghi 1 dòng log.

## Output Report (bắt buộc — skill này ghi thẳng vào wiki, không chỉ vào chat)

Sau khi user CHỐT thiết kế (dù đã áp vào `chat.html` hay mới dừng ở gallery preview), ghi lại NGAY,
theo đúng 3 bước:

**1. Lưu snapshot HTML đã tự-kiểm (QuickLook) vào `llmwiki/html/DDMMYY-<ten-agent>-avatar.html`** —
`DDMMYY` = hôm nay, `<ten-agent>` = tên agent mới (vd `290826-support-agent-avatar.html`). Đây là
file gallery/preview THẬT đã cho user xem, không phải bản nháp — copy nguyên nội dung, không tóm
tắt.

**2. Ghi 1 entry vào `llmwiki/wiki/log.md`** (thêm trước `<!-- log:auto:start -->`, theo đúng format
`## YYYY-MM-DD — feature — <slug>` các entry khác đang dùng), nêu rõ: agent nào, phụ kiện signature
là gì, ảnh tham khảo đã tra (nếu có), có vi phạm/tự sửa luật nào trong SKILL.md không, đường dẫn
file snapshot ở bước 1, và **đã áp vào `chat.html` thật hay chưa** (nếu chưa, ghi rõ "chưa áp dụng
— chờ user xác nhận", đừng để mơ hồ).

**3. Nếu agent này là agent HOÀN TOÀN MỚI (chưa từng có trong wiki)**, cân nhắc thêm 1 dòng vào
`llmwiki/wiki/index.md` trỏ tới entry log vừa ghi hoặc tới trang riêng nếu agent đó có trang giới
thiệu — bỏ qua bước này nếu chỉ đổi avatar cho agent ĐÃ có sẵn trong wiki (tránh index trùng lặp).

Không bỏ qua Output Report chỉ vì thiết kế "chưa chốt xong" — ghi ngay cả kết quả TRUNG GIAN quan
trọng (vd đảo hướng lớn sau khi tham khảo ảnh thật) nếu phiên làm việc có thể bị ngắt giữa chừng;
sửa/nối thêm vào entry đó khi có tiến triển tiếp, không cần đợi "xong hẳn" mới ghi.
