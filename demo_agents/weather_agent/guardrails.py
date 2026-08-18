"""Input guardrail THẬT (agents SDK `@input_guardrail`) — khác hẳn "gate" cũ trong INSTRUCTIONS
(chỉ là văn bản, model tự diễn giải mỗi lần, không nhất quán — user phát hiện qua transcript thật:
hỏi vị trí Atlantis rồi hỏi tiếp "harness hay guardrail tạo ra gate này", model trả lời dài dòng,
có lúc lúng túng). Guardrail này chạy 1 agent phân loại RIÊNG, NHẸ (không tool), TRƯỚC/SONG SONG
với model chính — nếu câu hỏi ngoài phạm vi thời tiết, trip tất định và trả 1 câu từ chối CỐ ĐỊNH,
không để model chính tự "sáng tác" cách từ chối mỗi lần. Xem wiki/concepts/agent-7-layers.md.

**3 MỨC (không phải nhị phân)** — user phát hiện qua 2 bug thật (guardrail chặn nhầm câu hỏi tiếp
nối ngắn "về stage", chặn nhầm "giao task cho librarian"): 1 cổng nhị phân IN/OUT không có đường
lùi khi mơ hồ — sai là chặn cứng luôn. Thêm mức `UNCERTAIN`: KHÔNG tự chặn, đẩy xuống model chính
kèm 1 ghi chú ngữ cảnh (xem `classify_scope`/`build_uncertain_hint`, dùng ở harness.py/chatdemo.py
TRƯỚC khi gọi Runner.run — guardrail SDK không có cơ chế tiêm thêm context khi KHÔNG trip, nên phần
"đẩy hint" phải làm ở lớp harness, không phải trong @input_guardrail này). CHỈ hard-block khi model
phân loại THẬT SỰ tự tin là ngoài phạm vi.
"""

from dataclasses import dataclass

from agents import Agent, GuardrailFunctionOutput, ModelSettings, Runner, input_guardrail

from demo_agents.weather_agent.model_provider import get_model

OUT_OF_SCOPE_MESSAGE = (
    "Câu hỏi này ngoài phạm vi của mình — mình chỉ hỗ trợ thời tiết HIỆN TẠI và ghi chú múi "
    "giờ/khí hậu chung cho một số thành phố tiêu biểu. Mình không có thông tin địa lý, lịch sử, "
    "hay chi tiết kỹ thuật nội bộ (harness/guardrail/code). Bạn hỏi lại về thời tiết được không?"
)

# KHÔNG dùng output_type=<pydantic model> (structured output) — DeepSeek (provider chính của
# sandbox này, xem model_provider.py) trả lỗi 400 "response_format type is unavailable" cho kiểu
# này, dù OpenAI hỗ trợ. Guardrail phải chạy được trên CẢ 2 provider nên dùng văn bản thuần, tự
# parse — không phụ thuộc tính năng chỉ 1 bên có.
_OUT_TAG = "OUT_OF_SCOPE"
_UNCERTAIN_TAG = "UNCERTAIN"
_IN_TAG = "IN_SCOPE"

_SCOPE_INSTRUCTIONS = (
    "Bạn là bộ phân loại phạm vi cho 1 weather agent. Nhiệm vụ DUY NHẤT: xác định CẤU TRÚC/Ý ĐỊNH "
    "của câu hỏi có phải đang hỏi thời tiết/múi giờ/khí hậu hay không — không trả lời câu hỏi, "
    "không phân loại.\n\n"
    "QUAN TRỌNG — chỉ nhìn Ý ĐỊNH câu hỏi, TUYỆT ĐỐI KHÔNG xét thành phố được nhắc tới có PHẢI là "
    "nơi CÓ THẬT, NỔI TIẾNG, hay HƯ CẤU hay không — việc thành phố đó có dữ liệu hay không là việc "
    "của TOOL tra cứu (get_weather/get_city_note), không phải việc của bạn. Ví dụ: 'Thời tiết ở "
    "Atlantis thế nào?' hay 'Thời tiết ở Hogwarts ra sao?' VẪN LÀ TRONG PHẠM VI dù Atlantis/Hogwarts "
    "là địa danh hư cấu — câu hỏi có cấu trúc 'thời tiết ở X thế nào' là hỏi thời tiết, bất kể X là "
    "gì. Chỉ NGOÀI PHẠM VI khi câu hỏi hỏi thứ KHÁC thời tiết về địa danh đó (vị trí, lịch sử...).\n\n"
    "TRONG PHẠM VI: hỏi thời tiết HIỆN TẠI một thành phố/địa danh BẤT KỲ (kể cả tên lạ, hư cấu, "
    "không tồn tại — không tự đoán, cứ coi là hỏi thời tiết); hỏi múi giờ/khí hậu chung một thành "
    "phố; câu hỏi tiếp nối tự nhiên của hội thoại đang nói về thời tiết (vd 'còn ngày mai', 'so với "
    "hôm qua' — việc từ chối dữ liệu lịch sử/dự báo là của model chính, không phải bạn); lời chào/"
    "cảm ơn/xã giao ngắn; hỏi 'bạn làm được gì'; yêu cầu ĐỌC/tóm tắt 1 trang web CỤ THỂ (có URL rõ "
    "ràng) miễn nội dung được nêu là LIÊN QUAN THỜI TIẾT (bài viết thời tiết, tin thời tiết cực "
    "đoan...); yêu cầu TÌM KIẾM thông tin thời tiết trên internet (vd 'tin bão mới nhất', 'cảnh báo "
    "thời tiết cực đoan gần đây ở khu vực X') — đây là dùng tool fetch/search qua MCP, đọc-only; yêu "
    "cầu lấy PHỤ ĐỀ 1 video YouTube hoặc đọc 1 RSS feed CỤ THỂ miễn nội dung liên quan thời tiết; "
    "nếu URL/nội dung không nêu rõ liên quan gì tới thời tiết thì vẫn NGOÀI PHẠM VI (xem dưới); "
    "**'librarian' KHÔNG PHẢI 1 người/agent bên ngoài mà là 1 TOOL NỘI BỘ của chính agent này** "
    "(ask_librarian — tra cứu sâu hơn trong wiki ghi chú thành phố đã thu thập sẵn) — mọi câu yêu "
    "cầu 'giao task/nhờ/bảo librarian tìm/search giúp...' dù phrasing giống ra lệnh cho 1 bên thứ "
    "ba, vẫn TRONG PHẠM VI như bất kỳ câu hỏi tra cứu thời tiết nào khác.\n\n"
    "NGOÀI PHẠM VI: hỏi VỊ TRÍ địa lý, lịch sử, dân số, văn hoá của 1 địa danh (vd 'Atlantis ở đâu', "
    "'Atlantis có thật không') — khác hẳn hỏi THỜI TIẾT của địa danh đó; hỏi về cách hệ thống/"
    "harness/guardrail/kiến trúc code hoạt động; BẤT KỲ chủ đề nào không liên quan thời tiết (toán, "
    "lập trình, tin tức, ý kiến cá nhân...).\n\n"
    "MỨC ĐỘ TỰ TIN — đây là điểm khác biệt so với phân loại nhị phân: nếu câu hỏi RÕ RÀNG khớp 1 "
    f"mục TRONG PHẠM VI hoặc NGOÀI PHẠM VI ở trên, trả lời tự tin bằng '{_IN_TAG}'/'{_OUT_TAG}'. Nếu "
    "câu hỏi KHÔNG khớp rõ mục nào — diễn đạt lạ, chủ đề mới không có trong danh sách trên, câu quá "
    f"ngắn/thiếu ngữ cảnh để chắc chắn — trả '{_UNCERTAIN_TAG}: <lý do>' thay vì đoán liều. CHỈ dùng "
    f"'{_OUT_TAG}' khi bạn THỰC SỰ CHẮC CHẮN; còn nghi ngờ dù chỉ một chút thì dùng "
    f"'{_UNCERTAIN_TAG}'.\n\n"
    f"CHỈ trả lời ĐÚNG 1 DÒNG theo định dạng: '{_OUT_TAG}: <lý do ngắn>' hoặc "
    f"'{_UNCERTAIN_TAG}: <lý do ngắn>' hoặc '{_IN_TAG}: <lý do ngắn>'. Không thêm chữ nào khác, "
    "không giải thích dài."
)

_scope_guardrail_agent = Agent(
    name="Weather scope guardrail",
    model=get_model(),
    instructions=_SCOPE_INSTRUCTIONS,
    # temperature=0 — cùng lý do đã áp cho demo_agents/devops_agent/guardrails.py::_scope_guardrail_agent
    # (tác vụ phân loại, không cần sinh văn tự do — giảm ngẫu nhiên giữa các lần gọi).
    model_settings=ModelSettings(temperature=0),
)


@dataclass
class ScopeCheck:
    verdict: str  # "in_scope" | "uncertain" | "out_of_scope"
    reason: str

    @property
    def is_out_of_scope(self):
        """Giữ tên cũ cho code/test đang đọc field nhị phân — chỉ mức out_of_scope mới hard-block."""
        return self.verdict == "out_of_scope"


def _parse_scope_check(text):
    """Parse dòng phân loại 3 mức. Fail-OPEN (verdict="in_scope") nếu model trả sai định dạng — 1
    guardrail phụ không nên tự nó chặn nhầm câu hỏi thời tiết hợp lệ vì lỗi parse."""
    line = (text or "").strip()
    upper = line.upper()
    reason = line.split(":", 1)[-1].strip() if ":" in line else line
    if upper.startswith(_OUT_TAG):
        return ScopeCheck(verdict="out_of_scope", reason=reason)
    if upper.startswith(_UNCERTAIN_TAG):
        return ScopeCheck(verdict="uncertain", reason=reason)
    return ScopeCheck(verdict="in_scope", reason=reason)


async def classify_scope(question, context=None):
    """Gọi bộ phân loại 3 mức TRỰC TIẾP — dùng ở harness.py TRƯỚC Runner.run/run_streamed, để có
    thể tiêm hint cho mức UNCERTAIN trước khi model chính bắt đầu chạy (KHÔNG thể làm việc này sau
    khi Runner.run đã bắt đầu — @input_guardrail không có cơ chế sửa input/instructions cho lượt
    đang chạy)."""
    result = await Runner.run(_scope_guardrail_agent, question, context=context)
    return _parse_scope_check(result.final_output)


_UNCERTAIN_HINT_TEMPLATE = (
    "\n\n---\n"
    "GHI CHÚ NỘI BỘ (bộ phân loại phạm vi tự động sinh ra, KHÔNG phải lời người dùng): câu hỏi VỪA "
    "RỒI được đánh giá KHÔNG CHẮC CHẮN có thuộc phạm vi thời tiết hay không (lý do phân loại: "
    "{reason}). Đọc kỹ lại câu hỏi trong ngữ cảnh hội thoại: nếu thấy THẬT SỰ ngoài phạm vi, hãy "
    "giải thích ngắn gọn giới hạn của bạn (đừng trả lời bừa ngoài chủ đề thời tiết); nếu vẫn có vẻ "
    "liên quan (chỉ diễn đạt lạ/thiếu ngữ cảnh riêng lẻ), hãy trả lời bình thường hoặc hỏi lại xác "
    "nhận nếu cần — ĐỪNG tự động từ chối chỉ vì cách hỏi khác thường."
)


def build_uncertain_hint(reason):
    return _UNCERTAIN_HINT_TEMPLATE.format(reason=reason or "không rõ")


@input_guardrail
async def weather_scope_guardrail(ctx, agent, input):
    """Vẫn giữ dạng @input_guardrail — dùng làm lớp bảo vệ DỰ PHÒNG cho caller gọi Runner.run trực
    tiếp không qua harness.py (vd run.py CLI, xem agent.py::weather_agent), và để agent_spec.py có
    object thật tham chiếu khi xuất spec. Đường live chat (chatdemo.py qua harness.py) KHÔNG dựa
    vào cơ chế trip này nữa — nó gọi classify_scope() trực tiếp TRƯỚC khi chạy model chính, vì cần
    tiêm hint cho mức UNCERTAIN (guardrail SDK không hỗ trợ)."""
    check = await classify_scope(input, context=ctx.context)
    return GuardrailFunctionOutput(output_info=check, tripwire_triggered=check.is_out_of_scope)
