#!/usr/bin/env python3
"""pixel_icon_gen.py — sinh icon nhân vật pixel "Clawd-style" (lấy cảm hứng từ mascot Clawd của
Claude Code — khối 8-bit đơn giản, 2 mắt chấm, xem wiki/log.md entry "clawd-pixel-icon-system") cho
avatar/step-indicator của các demo agent (weather/devops/librarian).

Lưu lại PATTERN đã chốt qua ~13 vòng Design Feedback (ảnh tham chiếu thật do user gửi, không đoán
mò) để TÁI DÙNG — thêm agent mới hoặc chỉnh mũ/màu chỉ cần sửa `AGENTS` bên dưới, không phải gõ tay
lại toàn bộ toạ độ <rect> như lúc thiết kế thủ công qua nhiều bản artifact.

Quyết định thiết kế đã chốt (đọc kỹ trước khi sửa CLAWD_BODY — đây là kết quả sau nhiều lần sửa sai,
không phải lựa chọn tuỳ hứng):
- Đầu/thân là 1 khối bề rộng CỐ ĐỊNH từ đỉnh xuống — KHÔNG co hẹp phần đầu rồi phình ra ở tay (lỗi
  đã mắc ở bản đầu, user chỉ ra bằng ảnh tham chiếu thật).
- Tai/tay thò ra 2 bên NGANG HÀNG với mắt (cùng 1 hàng) — không phải mắt nằm thấp hơn tai vài hàng.
- Mắt = ĐÚNG 1 chấm pixel/bên (không phải khối 2x1) — vẽ đè lên như 1 layer màu riêng, không khoét
  lỗ khỏi thân trắng.
- Chân = 4 chân cân đối 2 bên, khớp ĐÚNG mép thân (thân phải đủ rộng để chân không tràn ra ngoài).
- Mũ (hat) là phần DUY NHẤT khác nhau giữa các agent — thân/mắt/chân dùng chung 100%.

Cách dùng:
    python3 harness/scripts/pixel_icon_gen.py                  # in SVG ra stdout cho mọi agent
    python3 harness/scripts/pixel_icon_gen.py --preview out.html  # ghi trang xem trực tiếp
"""

import argparse
from dataclasses import dataclass, replace


def _grid_to_rects(grid):
    """Gộp các ô '#' liền kề THEO HÀNG thành 1 rect rộng hơn (x, y, width, height=1) — gọn hơn hẳn
    1 <rect> cho mỗi ô vuông, dễ đọc/debug khi in ra."""
    rects = []
    for y, row in enumerate(grid):
        x = 0
        while x < len(row):
            if row[x] == "#":
                start = x
                while x < len(row) and row[x] == "#":
                    x += 1
                rects.append((start, y, x - start, 1))
            else:
                x += 1
    return rects


def _rects_to_svg_children(rects):
    return "".join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}"/>' for x, y, w, h in rects)


# Thân Clawd DÙNG CHUNG cho mọi agent — xem "Quyết định thiết kế đã chốt" ở docstring module.
CLAWD_WIDTH = 10
CLAWD_BODY = [
    ".########.",  # 0 đỉnh khối (bề rộng CHÍNH, không co hẹp so với các hàng dưới)
    "##########",  # 1 tai/tay thò ra 2 bên — MẮT (xem EYES) vẽ đè lên ĐÚNG hàng này
    ".########.",  # 2 khối tiếp
    ".########.",  # 3 khối tiếp
    ".########.",  # 4 thân
    ".########.",  # 5 thân
    ".#.#..#.#.",  # 6 chân — 4 chân cân đối 2 bên, khớp đúng mép thân (cols1-8)
]

# Mắt = 1 chấm pixel/bên, NGANG HÀNG tai/tay (row1 của CLAWD_BODY, TƯƠNG ĐỐI — build_icon_svg tự
# cộng thêm chiều cao mũ khi ghép). Vẽ như layer màu riêng, không khoét lỗ khỏi thân trắng.
EYES = [(2, 1, 1, 1), (7, 1, 1, 1)]
EYE_COLOR = "#1a1a1a"
BODY_COLOR = "#ffffff"


@dataclass
class AgentIcon:
    name: str
    hat: list
    hat_color: str
    hat_highlight: str
    body_gradient: tuple
    label: str = ""
    # Phụ kiện TRÊN THÂN — vẽ đè lên NGOÀI CÙNG (sau mắt), toạ độ TƯƠNG ĐỐI so với CLAWD_BODY.
    # List các nhóm (color, [rect, ...]) — MỖI NHÓM 1 MÀU RIÊNG (vd kính 1 màu + belt 1 màu khác +
    # dụng cụ trên belt 1 màu khác nữa), render theo ĐÚNG THỨ TỰ khai báo (nhóm sau đè lên nhóm
    # trước). None = không có phụ kiện thân.
    accessories: list = None
    # Design Feedback (ảnh Clawd thật đội top hat): "accessory chọn bộ chia pixel nhỏ hơn thay vì to
    # ngang với thân" — mũ THẬT trong ảnh làm từ khối NHỎ HƠN HẲN khối thân, không phải cùng cỡ voxel
    # phóng to. `hat_subdiv` = số lần chia nhỏ 1 đơn vị thân cho `hat` (mặc định 1 = giống thân, dùng
    # cho agent cũ không đổi). VD subdiv=2: mỗi ký tự trong `hat` chỉ chiếm NỬA đơn vị thân — cho
    # phép vẽ chi tiết mịn hơn (vd 1 dải màu mảnh) trong cùng bề rộng vật lý.
    hat_subdiv: int = 1


# Font pixel 3x3 tối giản — Design Feedback: "logo quá khó biểu diễn thì dùng tên viết tắt được
# không, vd HR hay bảo mật thì SEC". Chỉ định nghĩa CHỮ CẦN DÙNG (không phải bảng chữ đầy đủ) — mỗi
# glyph là list rect (dx, dy, w, h) TƯƠNG ĐỐI trong khung riêng của chữ đó (dy 0-2 = 3 hàng cao,
# dx 0..width-1). `_text_rects()` ghép nhiều chữ ngang hàng, cách nhau 1 cột trống.
PIXEL_FONT_3x3 = {
    "H": (3, [(0, 0, 1, 1), (2, 0, 1, 1), (0, 1, 3, 1), (0, 2, 1, 1), (2, 2, 1, 1)]),
    "R": (3, [(0, 0, 2, 1), (0, 1, 2, 1), (0, 2, 1, 1), (2, 2, 1, 1)]),
    "S": (3, [(1, 0, 2, 1), (0, 1, 2, 1), (1, 2, 2, 1)]),
    "E": (2, [(0, 0, 2, 1), (0, 1, 1, 1), (0, 2, 2, 1)]),
    "C": (3, [(1, 0, 2, 1), (0, 1, 1, 1), (1, 2, 2, 1)]),
}


def _text_rects(text, start_x, start_y):
    """Ghép các glyph trong PIXEL_FONT_3x3 thành list rect (x, y, w, h) tuyệt đối, bắt đầu tại
    (start_x, start_y), mỗi chữ cách nhau 1 cột. Dùng cho accessory THÂN (không phải hat) — luôn
    đặt start_y >= 3 để không đè hàng mắt (LUẬT SỐ 1 trong SKILL.md)."""
    rects = []
    x = start_x
    for ch in text:
        width, glyph = PIXEL_FONT_3x3[ch]
        rects.extend((x + dx, start_y + dy, w, h) for dx, dy, w, h in glyph)
        x += width + 1
    return rects


# Mũ = phần DUY NHẤT khác nhau giữa các agent (thân/mắt/chân dùng chung CLAWD_BODY/EYES ở trên).
# 3 màu mũ chọn CHỦ Ý tương phản nhau (xanh trời/vàng an toàn/tím academic) VÀ tương phản màu badge
# nền của chính agent đó — theo yêu cầu "tô màu nón cho nổi bật, tươi sáng tương phản nhau".
#
# Mũ = phần khác nhau giữa các agent (thân/mắt/chân dùng chung CLAWD_BODY/EYES ở trên).
#
# Đảo hướng LỚN (Design Feedback: gửi 2 ảnh tham khảo thật — weatherman thật CHỈ mặc suit/tie đứng
# trước bản đồ, KHÔNG đội gì; devops thật trong minh hoạ đeo KÍNH, không phải nón bảo hộ — nón bảo
# hộ là kỹ sư xây dựng, sai chức nghiệp). Bỏ HẲN khái niệm "mũ trên đầu" cho weather/devops — 2 agent
# này giờ `hat=[]` (không hàng nào, không khe hở gì để lo), phụ kiện vẽ thẳng ĐÈ LÊN đầu/thân có sẵn
# qua `accessory_rects` (đúng cơ chế không-khe-hở đã dùng cho kính quý tộc librarian):
# - weather: tai nghe phát thanh + cần mic (user chọn qua AskUserQuestion, thay vì cloud-hat mang
#   tính biểu trưng không khớp ảnh tham khảo).
# - devops: KÍNH 2 mắt, và theo yêu cầu tiếp theo — hình dáng kính chính là ẩn dụ ký hiệu VÔ CỰC (∞)
#   của luồng CI/CD (2 vòng tròn nối bằng 1 cầu giữa = đúng hình ∞ khi nhìn ngang, khớp sơ đồ
#   CODE→BUILD→...→OPERATE trong ảnh tham khảo thứ 2).
# librarian GIỮ NGUYÊN mortarboard (đã tham khảo WebSearch, đúng chức nghiệp "học giả", không đổi).
AGENTS = {
    "weather": AgentIcon(
        name="weather",
        # Design Feedback: "thôi thà cho weather mặc suit cho rồi, vẽ tai nghe xấu quá" — bỏ hẳn tai
        # nghe (dù đã sửa hết lỗi dính mắt, hình vẫn không đẹp ở quy mô pixel này). Quay lại đúng ảnh
        # tham khảo gốc: weatherman thật KHÔNG đội/đeo gì trên đầu — chỉ mặc suit + cà vạt. Không có
        # `hat` — cà vạt vẽ thẳng xuống THÂN (torso), tách hẳn khỏi vùng đầu/mắt nên không thể dính.
        hat=[],
        hat_color="#DC2626",
        hat_highlight="#DC2626",
        body_gradient=("#10a37f", "#1a7f64"),
        label="Weather Agent — suit + cà vạt",
        # Design Feedback: "có suit đâu" → thêm ve áo ở row2 → "bị chạm mắt rồi, bổ line ngay lúc
        # chạm mắt" → BỎ ve áo ở row2 nhưng ĐỂ SÓT nút cà vạt vẫn ở row2 → "sao tie vẫn ở row đó" —
        # đúng, dù nút cà vạt không ĐÈ cột mắt (col4-5, khác col2/7) nhưng vẫn nằm chung row2 (hàng
        # đã xác định là "vùng nguy hiểm", nên phải trắng HOÀN TOÀN, không riêng gì cột mắt). Fix:
        # cà vạt dời hẳn xuống bắt đầu từ row3 CÙNG với áo vest — row2 giờ 100% trắng, không phụ kiện
        # nào chạm tới, nhất quán với nguyên tắc "1 hàng trắng ngăn cách mắt/phụ kiện" đã áp dụng.
        accessories=[
            (
                "#1E3A5F",  # navy — màu vest cổ điển, tương phản rõ trên nền badge xanh lá
                [
                    (1, 3, 8, 1),  # thân áo vest — full bề rộng, bắt đầu từ row3 (cách mắt 1 hàng)
                    (1, 4, 8, 1),  # thân áo vest
                    (1, 5, 8, 1),  # thân áo vest
                ],
            ),
            (
                "#DC2626",  # đỏ cổ điển — màu cà vạt presenter, đè lên trên áo vest, đúng khe sơ mi
                [
                    (4, 3, 2, 1),  # nút thắt cà vạt — CŨNG bắt đầu từ row3, row2 để trắng hoàn toàn
                    (4, 4, 1, 1),  # thân cà vạt
                    (4, 5, 1, 1),  # mũi cà vạt
                ],
            ),
        ],
    ),
    "devops": AgentIcon(
        name="devops",
        # Design Feedback: "cờ lê với kính chạm nhau rồi, kính đặt lên đỉnh đầu chẳng hạn" — kính cũ
        # nằm NGAY TRONG hàng thân, cạnh dưới vòng kính (row2) đụng thẳng cạnh trên cờ lê (row3) cùng
        # cột 6-7 → dính khối. Fix theo đúng gợi ý: kính đẩy LÊN ĐỈNH ĐẦU (kiểu dân kỹ thuật đẩy kính
        # lên trán khi tập trung) — chuyển thành `hat` riêng (2 hàng, PHÍA TRÊN đầu), tách hẳn khỏi
        # belt/cờ lê ở thân (cách nhau nguyên hàng mắt + nguyên hàng đỉnh đầu ở giữa).
        # Design Feedback (ảnh Clawd thật đội top hat), 3 vòng: (1) mũ nên hẹp + cao hơn; (2) phải
        # pixel MỊN hơn thân; (3) "mấy cái nón nhìn na ná nhau... kính giờ cũng không tưởng tượng ra
        # nổi" — bản trước dùng CHUNG 1 khuôn "thóp nhọn dần" cho mọi agent, kính bị vo tròn thành 1
        # hình tam giác giống hệt beret/tai nghe. Kính THẬT phẳng/rộng (không nhọn), 2 tròng RÕ RỆT
        # tách biệt ở TRÊN CÙNG (không phải đỉnh) rồi mới gộp gọng — sửa lại đúng hình dạng đó.
        hat_subdiv=2,
        hat=[
            "....####....####....",  # 0 2 tròng kính RÕ RỆT, tách hẳn 2 bên (highlight)
            "....####....####....",  # 1
            "....############....",  # 2 gọng nối liền 2 tròng (base) — khe cầu ở giữa đã lấp lại
            "....############....",  # 3 chạm thẳng vào đỉnh đầu — kính THẤP/RỘNG, không nhọn
        ],
        hat_color="#1F2937",
        hat_highlight="#475569",
        body_gradient=("#326CE5", "#244da4"),
        label="DevOps Agent — kính đẩy lên đỉnh đầu + belt dụng cụ",
        # Giờ CHỈ còn 2 nhóm ở thân (kính đã chuyển lên hat) — belt + cờ lê, MÀU RIÊNG từng nhóm
        # (Design Feedback gốc: "kính không đủ signature, thêm 1 belt có kẹp cây bút chì/cờ lê").
        # Belt dụng cụ ngang thân (row4, đúng kiểu "tool belt" kỹ sư thật) + 1 cờ lê kẹp trên belt
        # (đầu cờ lê rộng hơn thò lên trên belt, thân xuyên qua/dưới belt).
        accessories=[
            (
                "#44403C",  # belt da nâu đậm — tương phản rõ trên thân trắng
                [(1, 4, 8, 1)],  # dây belt ngang full bề rộng thân (row4)
            ),
            (
                "#F97316",  # cờ lê cam an toàn — nổi bật trên belt nâu tối + thân trắng
                [
                    (6, 3, 2, 1),  # đầu cờ lê (rộng hơn, thò lên trên belt)
                    (6, 4, 1, 1),  # thân cờ lê xuyên qua belt (đè lên belt = đúng ý "kẹp trên belt")
                    (6, 5, 1, 1),  # thân cờ lê thò xuống dưới belt
                ],
            ),
        ],
    ),
    "librarian": AgentIcon(
        name="librarian",
        hat=[
            "##########",  # 0 BẢNG VUÔNG PHẲNG rộng full 10 cột (highlight) — mũ cử nhân thật có
            #                 bảng rộng HƠN ĐẦU, tràn ra 2 bên (tham khảo WebSearch), không co hẹp
            #                 bằng đầu như bản cũ
            "..######..",  # 1 dải mũ hẹp hơn (color) — nối xuống đầu, đúng hình academic cap thật
        ],
        hat_color="#A855F7",  # tím academic — tương phản xanh trời + vàng
        hat_highlight="#C084FC",  # tím nhạt — bóng đổ đỉnh mũ
        body_gradient=("#d97757", "#b85c3e"),
        label="Librarian — mũ cử nhân + tua + kính quý tộc 1 mắt",
        # 3 nhóm phụ kiện, CÙNG 1 màu vàng kim (đồng bộ "đồ trang sức vàng"), đều đè lên bề mặt ĐẶC
        # sẵn có (bảng mũ/dải mũ/đầu) — không hàng rời, không khe hở:
        # (0) nút/khuy giữa bảng mũ (y=-2, đúng hàng bảng vuông) — mũ cử nhân thật luôn có 1 khuy
        #     giữa bảng, nơi dây tua bắt đầu (tham khảo WebSearch).
        # (1) tua mũ: 1 ô trên dải mũ (y=-1, cạnh TRÁI dải) + 1 ô rủ xuống mép trái đỉnh đầu (y=0,
        #     col1 vẫn nằm trong CLAWD_BODY row0 "########" nên KHÔNG lơ lửng) — CỐ Ý đặt bên TRÁI,
        #     đối diện kính quý tộc bên phải, tránh 2 phụ kiện chồng lên nhau thành 1 khối vàng lớn
        #     khó đọc (Design Feedback lần trước: tua+kính cùng bên dính thành 1 mảng).
        # (2) kính quý tộc 1 mắt: vòng quanh MẮT PHẢI (col7, row1 của CLAWD_BODY), chừa đúng ô mắt ở
        #     giữa không tô đè, + 1 dây/xích ngắn rủ xuống. Chỉ librarian có — khớp chủ đề "học giả".
        accessories=[
            (
                "#FDE047",  # vàng kim loại — tương phản tím mũ + trắng thân + đen mắt
                [
                    (4, -2, 1, 1),  # khuy giữa bảng mũ
                    (2, -1, 1, 1),  # tua mũ — điểm gắn trên dải mũ (cạnh trái)
                    (1, 0, 1, 1),  # tua mũ — rủ xuống mép trái đỉnh đầu
                    (6, 0, 3, 1),  # kính — viền trên vòng kính
                    (6, 1, 1, 1),  # kính — viền trái (viền phải bỏ = đúng ô mắt, không tô đè)
                    (8, 1, 1, 1),  # kính — viền phải
                    (6, 2, 3, 1),  # kính — viền dưới vòng kính
                    (8, 3, 1, 1),  # kính — dây/xích rủ xuống
                ],
            )
        ],
    ),
    # --- 8 agent TEST — gọi qua skill /create-agent-avatar (xem .claude/skills/create-agent-avatar/
    # SKILL.md), KHÔNG phải agent thật đang chạy trong demo_agents/ — mục đích thử quy trình 6 bước +
    # 2 luật cốt lõi (không đè hàng mắt, hat luôn 2 hàng đặc) trên nhiều role liên tiếp. Research thật
    # qua WebSearch cho từng role trước khi chọn signature (không đoán mò).
    "security_agent": AgentIcon(
        name="security_agent",
        # WebSearch: hình ảnh phổ biến nhất cho "cybersecurity/hacker" là người mặc HOODIE trùm đầu.
        # Design Feedback (ảnh Clawd thật đội top hat), 2 vòng: (1) "tỉ lệ nón hợp lý là vậy, sao
        # mình làm khổ thế" — mũ THẬT hẹp hơn hẳn đầu + cao hơn (không chỉ 2 hàng dẹt); (2) làm rồi
        # vẫn chưa đúng ý — "ý là accessory chọn bộ chia PIXEL NHỎ HƠN thay vì to ngang với thân" —
        # trong ảnh, mũ làm từ KHỐI VOXEL NHỎ HƠN HẲN khối thân, không phải cùng cỡ voxel phóng to.
        # Dùng `hat_subdiv=2` — mỗi ký tự trong `hat` chỉ chiếm NỬA đơn vị thân, cho phép lưới 6 hàng
        # x20 cột (thay vì 3x10) tạo đường THÓP MƯỢT hơn (nhiều nấc nhỏ) trong CÙNG kích thước vật lý.
        # Design Feedback: "nhìn hổng ra hoodie luôn" — tam giác thóp trơn (dù đúng SILHOUETTE mũ
        # trùm) thiếu 2 chi tiết THẬT mà mắt người dùng để nhận ra hoodie: (1) vải BUNG RỘNG ở đáy
        # (không thóp mượt tới tận đáy — hoodie thật phồng ra khi tới vai), (2) LỚP LÓT bên trong hé
        # ra ở miệng mũ (thường khác màu vải ngoài) — thêm cả 2 dưới đây.
        hat_subdiv=2,
        hat=[
            "........####........",  # 0 đỉnh (highlight) — hẹp nhất, pixel mịn nhờ subdiv=2
            ".......######.......",  # 1
            "......########......",  # 2
            "......########......",  # 3
            ".....##########.....",  # 4
            "....############....",  # 5 BUNG RỘNG hẳn ở đáy (12, thay vì thóp mượt tiếp) — vải dồn
            #                            lại quanh cổ/vai, đặc trưng hoodie kéo lên
        ],
        hat_color="#18181B",
        hat_highlight="#3F3F46",
        body_gradient=("#7F1D1D", "#450A0A"),
        label="Security Agent — mũ hoodie (pixel mịn) + huy hiệu khiên",
        # Design Feedback: "logo quá khó biểu diễn thì dùng tên viết tắt được không" → chữ "SEC" →
        # rồi: "áp [pixel mịn] với tất cả phụ kiện quần áo không chỉ mũ, nhờ vậy HR/security có độ
        # phân giải cao hơn thì không cần đè chữ nữa" — ĐÚNG: `accessories` vốn đã nhận toạ độ LẺ
        # (không cần field `hat_subdiv` riêng, hệ rect vẽ sẵn hỗ trợ số thực) — chỉ là chưa dùng tới.
        # Quay lại ICON THẬT (khiên bảo mật — biểu tượng an ninh kinh điển) nhưng vẽ ở ĐỘ PHÂN GIẢI
        # PHẦN TƯ ĐƠN VỊ (0.25) thay vì nguyên đơn vị — 5 dải xếp chồng thu hẹp dần tạo đường cong
        # khiên mượt hơn hẳn khối vuông cũ, rõ ràng hơn cả icon terminal cũ LẪN chữ "SEC".
        accessories=[
            (
                "#71717A",  # lớp lót bên trong mũ (khác màu vải ngoài) — hé ra ở miệng mũ, y ÂM
                # (tương đối CLAWD_BODY) nên vẫn nằm TRONG vùng mũ, không đụng luật "row2 phải trắng"
                [(4.2, -0.8, 1.6, 0.6)],
            ),
            (
                "#4ADE80",  # xanh lá nhạt — nửa trên khiên (highlight)
                [(3.3, 3, 2.4, 0.6), (3.5, 3.6, 2.0, 0.6)],
            ),
            (
                "#16A34A",  # xanh lá đậm — nửa dưới khiên thu nhọn (base)
                [(3.7, 4.2, 1.6, 0.5), (3.9, 4.7, 1.2, 0.5), (4.1, 5.2, 0.8, 0.3)],
            ),
        ],
    ),
    "finance_agent": AgentIcon(
        name="finance_agent",
        # WebSearch: kế toán/tài chính hay gắn với kính + máy tính + tiền. Visor xanh lá kế toán
        # (green eyeshade) là biểu tượng THẬT, lâu đời, vẫn dễ nhận diện hơn kính (đã dùng cho
        # devops) — chọn để KHÔNG trùng signature với agent khác.
        # Design Feedback: phụ kiện đầu nên hẹp+cao hơn, pixel mịn hơn thân — rồi: "mấy cái nón nhìn
        # na ná nhau" — bản trước lại là 1 DOME tam giác y hệt beret. Visor THẬT là 1 dây quai MỎNG
        # + 1 BRIM RỘNG-DẸT chiếu ra phía trước (rộng hơn hẳn cao, không phồng tròn như dome) — sửa
        # lại đúng tỉ lệ ngang > dọc đó, không tam giác/dome.
        hat_subdiv=2,
        hat=[
            "........####........",  # 0 dây quai (highlight) — mỏng
            "...##############...",  # 1 brim RỘNG-DẸT chiếu thẳng ra, không phồng tròn — chạm đầu
        ],
        hat_color="#16A34A",
        hat_highlight="#4ADE80",
        body_gradient=("#065F46", "#022C22"),
        label="Finance Agent — visor kế toán + xấp tiền ($)",
        # Xấp tiền trên ngực, màu vàng kim — row>=3. Design Feedback: "áp pixel mịn cho tất cả phụ
        # kiện" — đổi 2 thanh phẳng cũ thành 3 tờ XOÈ LỆCH (mỗi tờ cao 0.4 đơn vị, dịch dần) tạo hiệu
        # ứng xấp tiền thật hơn hẳn 2 thanh chồng khít. Rồi: "ghi thêm ký tự dollar cho ngầu" — thêm
        # ký hiệu "$" (nét dọc xuyên qua hình S) đè lên tờ trên cùng, màu xanh lá đậm tương phản vàng.
        accessories=[
            (
                "#EAB308",
                [(2, 4, 3, 0.4), (2.3, 4.4, 3, 0.4), (2.6, 4.8, 3, 0.4)],
            ),
            (
                # Design Feedback: bản đầu quá nhỏ (0.5 đơn vị) đọc thành dấu "+" chứ không ra hình
                # cong "S" — phóng to hẳn thành "con dấu $" in đè lên xấp tiền (thật ra dollar sign
                # IN TRÊN tiền là đúng thực tế), độ lệch trái/phải giữa các nét tăng lên 0.6 đơn vị
                # (thay vì 0.15-0.4) để mắt thấy rõ đường cong ngay cả ở size nhỏ.
                "#166534",  # xanh lá đậm cổ điển của ký hiệu $ — tương phản vàng kim
                [
                    (3.9, 4.3, 0.3, 0.4),  # nét dọc trên
                    (3.5, 4.65, 1.0, 0.3),  # hình S — nét trên
                    (2.9, 4.95, 1.0, 0.3),  # hình S — nét giữa (lệch trái RÕ)
                    (3.5, 5.25, 1.0, 0.3),  # hình S — nét dưới
                    (3.9, 5.55, 0.3, 0.35),  # nét dọc dưới
                ],
            ),
        ],
    ),
    "legal_agent": AgentIcon(
        name="legal_agent",
        # WebSearch: lawyer thật không có headwear đặc trưng (khác security/finance) — chỉ suit +
        # tie/bow-tie + gavel/briefcase. KHÔNG đội gì, giống weather (đúng thực tế), nhưng khác hẳn
        # hình dạng phụ kiện thân (nơ ngang thay vì cà vạt dọc) để không trùng weather.
        hat=[],
        hat_color="#1F2937",
        hat_highlight="#1F2937",
        body_gradient=("#78350F", "#451A03"),
        label="Legal Agent — suit + nơ + huy hiệu búa toà",
        # Design Feedback: "áp pixel mịn cho tất cả phụ kiện quần áo" — búa toà refine ở độ phân
        # giải phần tư đơn vị (đầu búa dẹt hơn thật + cán thon + đế gỗ nhỏ), rõ hình gavel hơn hẳn
        # bản 2-rect khối vuông cũ. Suit (mảng phẳng lớn) GIỮ NGUYÊN đơn vị thường — mịn hoá không có
        # lợi cho 1 mảng màu phẳng.
        accessories=[
            (
                "#1F2937",  # suit charcoal — thân, row>=3
                [(1, 3, 8, 1), (1, 4, 8, 1), (1, 5, 8, 1)],
            ),
            (
                "#991B1B",  # nơ (bow tie) — NGANG, khác hẳn cà vạt DỌC của weather
                [(3, 3, 3, 1)],
            ),
            (
                "#CA8A04",  # huy hiệu búa toà (gavel) — đầu búa dẹt + cán thon + đế gỗ
                [(3, 4, 2, 0.6), (3.6, 4.6, 0.5, 1.0), (2.8, 5.5, 1.6, 0.3)],
            ),
        ],
    ),
    "marketing_agent": AgentIcon(
        name="marketing_agent",
        # WebSearch: beret (mũ nồi) là biểu tượng THẬT cho creative/nghệ sĩ, có sẵn trong bộ icon
        # chuyên dụng — chọn thay vì đoán mascot chung chung.
        # Design Feedback: phụ kiện đầu nên hẹp+cao hơn, pixel mịn hơn thân — rồi: "mấy cái nón nhìn
        # na ná nhau" — bản trước dùng chung khuôn "thóp nhọn dần" nên beret trông y hệt kính/tai
        # nghe (khác mỗi màu). Beret THẬT là DOME TRÒN PHỒNG (rộng ngay gần đỉnh, không nhọn) + 1 cục
        # tem nhỏ lệch 1 bên trên đỉnh — sửa lại đúng dáng đó, KHÔNG tam giác nữa.
        hat_subdiv=2,
        hat=[
            "............##......",  # 0 cục tem nhỏ lệch phải (highlight) — CHỈ tem mới nhọn
            ".....##########.....",  # 1 dome phồng RỘNG NGAY (không thóp dần như tam giác)
            "....############....",  # 2 dome phồng rộng nhất — điểm khác biệt với kính/tai nghe
            "....############....",  # 3
            ".....##########.....",  # 4 vành thu lại
            "......########......",  # 5 chạm thẳng vào đầu
        ],
        hat_color="#C026D3",
        hat_highlight="#E879F9",
        body_gradient=("#701A75", "#4A044E"),
        label="Marketing Agent — beret + huy hiệu ống kính",
        # Huy hiệu ống kính máy ảnh trên ngực — row>=3. Design Feedback: "áp pixel mịn cho tất cả
        # phụ kiện" — vòng kính refine ở độ phân giải phần tư đơn vị (4 cạnh cong đều: trên/dưới
        # ngắn+dày, trái/phải cao+mảnh) tạo hình tròn thật hơn hẳn 3-rect góc vuông cũ.
        accessories=[
            (
                "#22D3EE",
                [
                    (3.2, 4, 1.6, 0.35),  # vòng kính — cạnh trên
                    (3, 4.35, 0.35, 0.9),  # vòng kính — cạnh trái
                    (4.65, 4.35, 0.35, 0.9),  # vòng kính — cạnh phải
                    (3.2, 5.25, 1.6, 0.35),  # vòng kính — cạnh dưới
                ],
            )
        ],
    ),
    "hr_agent": AgentIcon(
        name="hr_agent",
        # WebSearch: HR gắn với thẻ nhân viên/lanyard hơn là headwear — không đội gì, đúng thực tế.
        hat=[],
        hat_color="#EA580C",
        hat_highlight="#EA580C",
        body_gradient=("#9A3412", "#431407"),
        label="HR Agent — thẻ đeo lanyard (pixel mịn)",
        # Design Feedback: lanyard+thẻ cũ chỉ 3 rect nguyên-đơn-vị (quá thô để đọc) → đổi tạm sang
        # chữ "HR" → rồi: "áp pixel mịn cho cả phụ kiện quần áo, nhờ vậy không cần đè chữ nữa" —
        # dựng LẠI đúng ý tưởng gốc (lanyard + thẻ + ảnh) nhưng ở độ phân giải PHẦN TƯ đơn vị: dây
        # đeo mảnh hơn hẳn, thẻ có tỉ lệ thật (dọc, bo dáng), thêm 1 ảnh/khung + 1 dải chữ giả lập —
        # rõ ràng hơn hẳn bản thô cũ, không cần chữ thay thế nữa.
        accessories=[
            (
                "#1E40AF",  # dây lanyard — mảnh, chỉ 0.4 đơn vị ngang
                [(4.3, 3, 0.4, 1)],
            ),
            (
                "#F97316",  # thẻ nhân viên — tỉ lệ dọc thật (2.4 x 1.7)
                [(3.3, 4, 2.4, 1.7)],
            ),
            (
                "#1E3A5F",  # ảnh/khung trên thẻ — ô vuông nhỏ phía trên thẻ
                [(3.9, 4.2, 1.2, 0.7)],
            ),
            (
                "#FDE68A",  # dải "tên" giả lập phía dưới thẻ — chi tiết chỉ khả thi nhờ pixel mịn
                [(3.6, 5.2, 1.8, 0.2)],
            ),
        ],
    ),
    "data_scientist_agent": AgentIcon(
        name="data_scientist_agent",
        # WebSearch: "Lab Coat & Glasses: Characters are often depicted with labcoats and glasses" —
        # 2 tín hiệu MẠNH NHẤT theo tham khảo thật, không chỉ 1. Design Feedback: "sao không để mắt
        # kính luôn" — ĐÚNG, glasses không hề trùng devops (devops đeo kính ĐẨY LÊN ĐỈNH ĐẦU dạng
        # `hat`; đây là kính ĐEO TRÊN MẶT, hình dạng/vị trí khác hẳn) — bỏ biểu đồ cột (signature phụ,
        # yếu hơn) để nhường chỗ, tránh ngực quá rối.
        hat=[],
        hat_color="#7C3AED",
        hat_highlight="#7C3AED",
        body_gradient=("#4C1D95", "#2E1065"),
        label="Data Scientist — kính + áo blouse phòng lab",
        accessories=[
            (
                "#E2E8F0",  # áo blouse xám nhạt (khác trắng thân để vẫn thấy được) — row>=3
                [(1, 3, 8, 1), (1, 4, 8, 1), (1, 5, 8, 1)],
            ),
            (
                "#1E3A5F",  # 2 khuy áo — điểm nhấn cho thấy đây là áo, không phải thân trần
                [(4, 4, 1, 1), (4, 5, 1, 1)],
            ),
            (
                # Kính đeo mặt DẠNG HỞ ĐÁY (row0-1 CHỈ, KHÔNG viền dưới ở row2) — row2 vẫn trắng
                # 100% làm khe hở an toàn trước áo blouse ở row3, đúng LUẬT SỐ 1. Gọng nhạt kiểu
                # kính khoa học (khác hẳn màu tối #1F2937 của devops).
                "#7DD3FC",
                [
                    (1, 0, 3, 1),  # tròng trái — viền trên
                    (1, 1, 1, 1),  # tròng trái — viền trái (viền phải bỏ = đúng ô mắt)
                    (3, 1, 1, 1),  # tròng trái — viền phải
                    (4, 1, 2, 1),  # cầu nối giữa 2 tròng
                    (6, 0, 3, 1),  # tròng phải — viền trên
                    (6, 1, 1, 1),  # tròng phải — viền trái
                    (8, 1, 1, 1),  # tròng phải — viền phải (đúng ô mắt, không tô đè)
                ],
            ),
        ],
    ),
    "support_agent": AgentIcon(
        name="support_agent",
        # WebSearch: customer support = tai nghe (headset), gần như đồng nhất trong mọi icon set.
        # ĐÂY chính là concept đã bỏ ở weather (không hợp weatherman thật) — nay có agent hợp hẳn.
        # Design Feedback: phụ kiện đầu nên hẹp+cao hơn, pixel mịn hơn thân — rồi: "vòm trên tai
        # nghe giờ cũng không tưởng tượng ra nổi" — bản trước CAO/DÀY như beret/hoodie, mất hẳn dáng
        # BĂNG CONG MẢNH đặc trưng headset. Headband THẬT là 1 dải MỎNG cong hình vòm (không dày lên
        # thành khối), thấp hơn hẳn beret/hoodie — sửa lại THẤP + MỎNG, cong dần ra 2 bên nối với ốp
        # tai (đã có sẵn ở body row1 col0/col9).
        hat_subdiv=2,
        hat=[
            ".......######.......",  # 0 đỉnh vòm (highlight) — dải MỎNG, không dày
            "......########......",  # 1 vòm cong rộng dần ra 2 bên — chạm thẳng vào đầu
        ],
        hat_color="#0EA5E9",
        hat_highlight="#7DD3FC",
        body_gradient=("#0891B2", "#164E63"),
        label="Support Agent — tai nghe chăm sóc khách hàng + mic",
        # Design Feedback vòng 2: "chụp tai phải to hơn tai mới ra dáng đang đeo chụp tai" — ốp tai
        # cũ chỉ đúng bằng 1x1 ô tai (không khác gì ô tai gốc) → phóng to hẳn (1.3x1.8, tràn từ hàng
        # đỉnh đầu xuống quá row2 1 chút) để rõ ràng LỚN HƠN tai thật. "thiếu mic tai nghe nữa" — bổ
        # sung cần mic từ ốp tai PHẢI đi xuống, nhưng lần này giữ NGUYÊN trong khoảng cột 8.0-8.7 —
        # KHÔNG BAO GIỜ chạm cột 7 (đúng cột mắt phải) — bài học từ lỗi cần mic weather trước đây.
        accessories=[
            (
                "#0369A1",
                [
                    (0, 0.6, 1.3, 1.8),  # ốp tai trái — LỚN hơn hẳn ô tai gốc (1x1)
                    (8.7, 0.6, 1.3, 1.8),  # ốp tai phải — đối xứng, cách mắt phải (col7) 0.7 đơn vị
                ],
            ),
            (
                "#1E293B",  # cần mic — xám than, tương phản xanh dương của ốp tai
                [
                    (8.3, 2.4, 0.4, 0.6),  # đoạn 1 — ngay dưới ốp tai phải
                    (8.1, 3.0, 0.4, 0.6),  # đoạn 2 — vẫn giữ cột >=8.0, không chạm cột mắt (7)
                    (8.0, 3.6, 0.6, 0.5),  # đầu mic — hình cầu nhỏ, gần khu vực miệng
                ],
            ),
        ],
    ),
    "sales_agent": AgentIcon(
        name="sales_agent",
        # WebSearch: sales rep = suit + briefcase + bắt tay. Cặp táp không cầm được (nhân vật không
        # có tay cầm đồ) nên đặt NHƯ ĐANG XÁCH bên hông, tràn nhẹ ra ngoài mép thân (giống kỹ thuật
        # tua mũ/dây kính đã dùng an toàn cho librarian) — không đội gì (đúng thực tế).
        hat=[],
        hat_color="#374151",
        hat_highlight="#374151",
        body_gradient=("#B45309", "#78350F"),
        label="Sales Agent — suit + cà vạt vàng + cặp táp",
        accessories=[
            (
                "#374151",  # suit charcoal — row>=3
                [(1, 3, 8, 1), (1, 4, 8, 1), (1, 5, 8, 1)],
            ),
            (
                "#F59E0B",  # cà vạt vàng (khác màu đỏ của weather, tránh trùng)
                [(4, 3, 2, 1), (4, 4, 1, 1), (4, 5, 1, 1)],
            ),
            (
                "#78350F",  # cặp táp xách bên hông trái — chạm mép thân (col1), tràn nhẹ ra col0
                [(0, 4, 2, 1), (0, 5, 2, 1)],
            ),
        ],
    ),
}


def _with_accessory_color(agent, new_color, group_index=-1):
    """Trả về BẢN SAO `agent` với màu của 1 NHÓM accessory đổi sang `new_color`, giữ nguyên toạ độ
    rect và mọi nhóm khác — dùng để sinh variant màu HÀNG LOẠT mà không đụng tới hình dạng đã được
    kiểm chứng an toàn (không khe hở, không chạm mắt). `group_index` mặc định -1 (nhóm cuối cùng —
    theo quy ước accessories khai NHÓM CHỮ KÝ sau cùng để nó đè lên trên)."""
    accessories = list(agent.accessories or [])
    color, rects = accessories[group_index]
    accessories[group_index] = (new_color, rects)
    return replace(agent, accessories=accessories)


# 8 biến thể MÀU cho mỗi agent (yêu cầu: "spawn thêm 8 phiên bản nữa của mỗi agent") — CHỈ đổi màu
# của phụ kiện CHỮ KÝ (cà vạt/dụng cụ/đồ trang sức), giữ NGUYÊN hình dạng + toạ độ đã chốt qua nhiều
# vòng Design Feedback (an toàn, không tái phạm lỗi khe hở/chạm mắt) — biến thể HÌNH DẠNG khác hẳn
# (kiểu cà vạt khác, dụng cụ khác) nên làm RIÊNG qua `/create-agent-avatar` với tay người thiết kế
# xác nhận từng bước, không sinh hàng loạt tự động (rủi ro lặp lại các lỗi đã từng mắc trong phiên
# thiết kế 3 agent chuẩn).
WEATHER_TIE_COLORS = [
    "#F97316",  # cam
    "#EAB308",  # vàng
    "#16A34A",  # xanh lá
    "#0D9488",  # xanh ngọc
    "#2563EB",  # xanh dương
    "#7C3AED",  # tím
    "#DB2777",  # hồng
    "#6B7280",  # xám bạc
]
DEVOPS_TOOL_COLORS = [
    "#22C55E",  # xanh lá
    "#EAB308",  # vàng
    "#EF4444",  # đỏ
    "#3B82F6",  # xanh dương
    "#A855F7",  # tím
    "#EC4899",  # hồng
    "#94A3B8",  # bạc kim loại
    "#78350F",  # nâu gỗ
]
LIBRARIAN_ACCENT_COLORS = [
    "#C0C0C0",  # bạc
    "#B87333",  # đồng
    "#D48A8E",  # vàng hồng
    "#4B5563",  # xám thép (gunmetal)
    "#CD7F32",  # đồng thau
    "#0EA5E9",  # sapphire
    "#10B981",  # emerald
    "#DC2626",  # ruby
]
VARIANTS = {
    "weather": [_with_accessory_color(AGENTS["weather"], c, 1) for c in WEATHER_TIE_COLORS],
    "devops": [_with_accessory_color(AGENTS["devops"], c, 1) for c in DEVOPS_TOOL_COLORS],
    "librarian": [_with_accessory_color(AGENTS["librarian"], c, 0) for c in LIBRARIAN_ACCENT_COLORS],
}


def build_icon_svg(agent_key, extra_attrs=""):
    """Trả về markup <svg> cho 1 agent đã khai trong AGENTS (theo key). Tiện gọi nhanh cho 3 agent
    CHÍNH THỨC; với variant/agent mới chưa đăng ký, dùng `build_icon_svg_for()` trực tiếp."""
    return build_icon_svg_for(AGENTS[agent_key], extra_attrs)


def build_icon_svg_for(agent, extra_attrs=""):
    """Trả về markup <svg> HOÀN CHỈNH (đỉnh mũ highlight, phần mũ còn lại + phụ kiện mũ base, thân
    trắng, mắt tối màu, + phụ kiện thân nếu có) cho 1 `AgentIcon` bất kỳ (không cần đăng ký trong
    AGENTS — dùng để dựng variant/preview thử mà không đụng bộ 3 agent chính thức). `extra_attrs`
    chèn thẳng vào thẻ <svg> (vd 'class="step-icon-svg"')."""
    subdiv = agent.hat_subdiv
    hat_h = len(agent.hat) / subdiv  # chiều cao mũ TÍNH THEO ĐƠN VỊ THÂN — có thể lẻ nếu subdiv>1

    def _scale(rects):
        return [
            (round(x / subdiv, 4), round(y / subdiv, 4), round(w / subdiv, 4), round(h / subdiv, 4))
            for x, y, w, h in rects
        ]

    height = hat_h + len(CLAWD_BODY)

    hat_highlight_rects = _scale(_grid_to_rects(agent.hat[:1]))  # row0 = luôn là highlight
    hat_base_rects = _grid_to_rects(agent.hat[1:])
    hat_base_rects = _scale([(x, y + 1, w, h) for x, y, w, h in hat_base_rects])  # bù 1 hàng đã tách
    body_rects = [(x, y + hat_h, w, h) for x, y, w, h in _grid_to_rects(CLAWD_BODY)]
    eyes_rects = [(x, y + hat_h, w, h) for x, y, w, h in EYES]

    attrs = f'viewBox="0 0 {CLAWD_WIDTH} {height}" shape-rendering="crispEdges"'
    if extra_attrs:
        attrs += f" {extra_attrs}"
    accessory_layer = ""
    for color, rects in agent.accessories or []:
        offset_rects = [(x, y + hat_h, w, h) for x, y, w, h in rects]
        accessory_layer += f'<g fill="{color}">{_rects_to_svg_children(offset_rects)}</g>'
    return (
        f"<svg {attrs}>"
        f'<g fill="{agent.hat_highlight}">{_rects_to_svg_children(hat_highlight_rects)}</g>'
        f'<g fill="{agent.hat_color}">{_rects_to_svg_children(hat_base_rects)}</g>'
        f'<g fill="{BODY_COLOR}">{_rects_to_svg_children(body_rects)}</g>'
        f'<g fill="{EYE_COLOR}">{_rects_to_svg_children(eyes_rects)}</g>'
        f"{accessory_layer}"
        f"</svg>"
    )


def build_preview_html():
    """Trang HTML tự chứa xem trực tiếp cả 3 icon — CÙNG cách đã dùng để tự kiểm qua `qlmanage -t`
    (QuickLook) suốt quá trình thiết kế, xem wiki/log.md."""
    cards = []
    for key, agent in AGENTS.items():
        svg = build_icon_svg(key)
        c1, c2 = agent.body_gradient
        cards.append(
            f'<div class="card"><div class="badge" '
            f'style="background:linear-gradient(135deg,{c1},{c2})">{svg}</div>'
            f'<div class="label">{agent.label}</div></div>'
        )
    return (
        '<meta charset="utf-8"><title>Pixel Icon Preview</title><style>'
        "body{margin:0;padding:40px;background:#0f1115;display:flex;gap:32px;"
        "font-family:-apple-system,sans-serif;flex-wrap:wrap}"
        ".card{display:flex;flex-direction:column;align-items:center;gap:10px}"
        ".badge{width:130px;height:130px;border-radius:26px;display:flex;"
        "align-items:center;justify-content:center}"
        ".badge svg{width:96px}"
        ".label{color:#cfd3da;font-size:13px;text-align:center;max-width:150px}"
        "</style>" + "".join(cards)
    )


def build_gallery_html():
    """Trang xem TOÀN BỘ: hàng đầu 3 icon CHÍNH THỨC (AGENTS, đã chốt qua Design Feedback), bên
    dưới mỗi agent 8 biến thể màu (VARIANTS) — dùng để chọn variant ưng ý mà không cần sinh code
    tay từng cái, cùng cách tự-kiểm qua `qlmanage -t` (QuickLook) đã dùng suốt phiên thiết kế."""

    def card(agent, label):
        svg = build_icon_svg_for(agent)
        c1, c2 = agent.body_gradient
        return (
            f'<div class="card"><div class="badge" '
            f'style="background:linear-gradient(135deg,{c1},{c2})">{svg}</div>'
            f'<div class="label">{label}</div></div>'
        )

    standard_row = "".join(card(agent, agent.label) for agent in AGENTS.values())
    variant_sections = []
    for key, variants in VARIANTS.items():  # CHỈ agent có khai VARIANTS (không phải mọi AGENTS)
        cards = "".join(card(variant, f"{key} #{i + 1}") for i, variant in enumerate(variants))
        variant_sections.append(f'<h2>{key} — 8 biến thể màu</h2><div class="row">{cards}</div>')

    return (
        '<meta charset="utf-8"><title>Pixel Icon Gallery</title><style>'
        "body{margin:0;padding:40px;background:#0f1115;font-family:-apple-system,sans-serif;"
        "color:#cfd3da}"
        "h1{font-size:20px;margin:0 0 20px}"
        "h2{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:#8a8f99;"
        "margin:32px 0 12px}"
        ".row{display:flex;gap:20px;flex-wrap:wrap}"
        ".card{display:flex;flex-direction:column;align-items:center;gap:8px}"
        ".badge{width:96px;height:96px;border-radius:20px;display:flex;align-items:center;"
        "justify-content:center}"
        ".badge svg{width:70px}"
        ".label{font-size:11px;text-align:center;max-width:110px}"
        "</style>"
        "<h1>Chuẩn (row đầu — đã chốt)</h1>"
        f'<div class="row">{standard_row}</div>' + "".join(variant_sections)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--preview", metavar="FILE", help="Ghi 1 trang HTML preview ra FILE thay vì in SVG ra stdout."
    )
    parser.add_argument(
        "--gallery",
        metavar="FILE",
        help="Ghi trang xem 3 icon chuẩn + 8 biến thể màu/agent ra FILE.",
    )
    args = parser.parse_args()

    if args.gallery:
        with open(args.gallery, "w", encoding="utf-8") as f:
            f.write(build_gallery_html())
        print(f"Đã ghi gallery: {args.gallery}")
        return 0

    if args.preview:
        with open(args.preview, "w", encoding="utf-8") as f:
            f.write(build_preview_html())
        print(f"Đã ghi preview: {args.preview}")
        return 0

    for key in AGENTS:
        print(f"=== {key} ===")
        print(build_icon_svg(key))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
