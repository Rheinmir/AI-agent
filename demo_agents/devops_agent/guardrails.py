"""Input guardrail THẬT (agents SDK `@input_guardrail`) — cùng pattern đã kiểm chứng ở
demo_agents/weather_agent/guardrails.py: 1 agent phân loại RIÊNG, NHẸ (không tool), chạy TRƯỚC model
chính, trip tất định thay vì để model chính tự "sáng tác" cách từ chối mỗi lần.

Phạm vi ở đây RỘNG hơn weather_agent (không phải 1 tool duy nhất mà là kiến thức chung DevOps) —
guardrail chỉ chặn những gì THỰC SỰ ngoài chủ đề DevOps/hạ tầng/vận hành phần mềm, không chặn dựa
trên việc agent có cheatsheet sẵn cho đúng chủ đề đó hay không (agent vẫn được dùng kiến thức chung
để trả lời câu hỏi DevOps hợp lệ, xem INSTRUCTIONS trong agent.py).

**3 MỨC (không phải nhị phân)** — cùng lý do đã đổi ở weather_agent/guardrails.py (đọc docstring ở
đó): 1 cổng nhị phân IN/OUT không có đường lùi khi mơ hồ. Thêm mức `UNCERTAIN`: KHÔNG tự chặn, đẩy
xuống model chính kèm ghi chú ngữ cảnh (xem `classify_scope`/`build_uncertain_hint`, dùng ở
chatdemo.py TRƯỚC khi gọi Runner.run/run_streamed)."""

from dataclasses import dataclass

from agents import Agent, GuardrailFunctionOutput, ModelSettings, Runner, input_guardrail

from demo_agents.devops_agent.model_provider import get_model

OUT_OF_SCOPE_MESSAGE = (
    "Câu hỏi này ngoài phạm vi của mình — mình chỉ hỗ trợ hỏi đáp kiến thức DevOps/hạ tầng "
    "(Kubernetes, container, CI/CD, pattern triển khai, promote môi trường dev/uat/stage/prod...). "
    "Mình cũng CHƯA kết nối tới cluster/Grafana/pipeline thật nào — không thể kiểm tra tình trạng "
    "hệ thống thật, chỉ giải thích khái niệm/cheatsheet. Bạn hỏi lại về DevOps được không?"
)

# Không dùng output_type=<pydantic model> — DeepSeek (provider chính của sandbox, xem
# model_provider.py) trả lỗi 400 "response_format type is unavailable" cho kiểu này. Dùng văn bản
# thuần tự parse để chạy được trên cả DeepSeek lẫn OpenAI.
_OUT_TAG = "OUT_OF_SCOPE"
_UNCERTAIN_TAG = "UNCERTAIN"
_IN_TAG = "IN_SCOPE"

_SCOPE_INSTRUCTIONS = (
    "Bạn là bộ phân loại phạm vi cho 1 DevOps knowledge Q&A agent. Nhiệm vụ DUY NHẤT: xác định "
    "CẤU TRÚC/Ý ĐỊNH của câu hỏi có phải đang hỏi kiến thức DevOps/hạ tầng/vận hành phần mềm hay "
    "không — không trả lời câu hỏi, không phân loại đúng/sai kỹ thuật.\n\n"
    "QUAN TRỌNG — LUÔN đọc TOÀN BỘ lịch sử hội thoại được cung cấp trước khi phân loại, KHÔNG chỉ "
    "nhìn tin nhắn CUỐI CÙNG một mình: nếu tin nhắn cuối NGẮN/MƠ HỒ (1-3 từ, đại từ, cụm từ chưa "
    "đầy đủ ý — vd 'về stage', 'còn cái kia thì sao', 'tiếp tục đi') NHƯNG các lượt TRƯỚC ĐÓ trong "
    "hội thoại đang bàn về chủ đề DevOps hợp lệ, hãy phân loại TRONG PHẠM VI theo mạch hội thoại đó "
    "— chỉ phân loại NGOÀI PHẠM VI nếu tin nhắn cuối có dấu hiệu RÕ RÀNG đổi hẳn sang chủ đề khác "
    "(không liên quan DevOps), không phải chỉ vì nó ngắn/thiếu ngữ cảnh riêng lẻ.\n\n"
    "TRONG PHẠM VI: Kubernetes/container/Docker; health check (liveness/readiness/startup probe); "
    "pattern triển khai ứng dụng (rolling update, blue-green, canary, feature flag); promote môi "
    "trường dev/uat/stage/production; CI/CD pipeline; monitoring/observability KHÁI NIỆM (Grafana/"
    "Prometheus dùng để làm gì, khác nhau ra sao — không phải truy vấn dữ liệu THẬT); linux/mạng cơ "
    "bản liên quan vận hành dịch vụ; incident response/troubleshooting quy trình chung; lời chào/"
    "cảm ơn/xã giao ngắn; hỏi 'bạn làm được gì'; yêu cầu ĐỌC nội dung 1 trang web CỤ THỂ (có URL rõ "
    "ràng) dù chủ đề trang đó không hẳn về DevOps; yêu cầu TÌM KIẾM thông tin trên internet (vd "
    "'phiên bản mới nhất của Kubernetes là gì', 'tin tức gần đây về...') dù chủ đề tìm kiếm không "
    "hẳn về DevOps; yêu cầu TÌM repo GitHub, lấy PHỤ ĐỀ 1 video YouTube cụ thể, hoặc đọc 1 RSS feed "
    "cụ thể — đây là dùng tool fetch/search/github_search/youtube_transcript/rss_feed (đọc-only, "
    "internet công khai), khác hẳn yêu cầu THỰC THI hành động lên hệ thống thật; **'librarian' KHÔNG "
    "PHẢI 1 người/agent bên ngoài mà là 1 TOOL NỘI BỘ của chính agent này** (ask_librarian — tra cứu "
    "sâu hơn trong wiki cheatsheet đã thu thập sẵn) — mọi câu yêu cầu 'giao task/nhờ/bảo librarian "
    "tìm/search giúp...' dù phrasing giống ra lệnh cho 1 bên thứ ba, vẫn TRONG PHẠM VI như bất kỳ "
    "câu hỏi tra cứu DevOps nào khác, KHÔNG được coi là 'giao việc cho ai đó khác'.\n\n"
    "NGOÀI PHẠM VI: yêu cầu THỰC THI hành động thật trên hệ thống NỘI BỘ (vd 'restart pod X giúp "
    "tôi', 'chạy lệnh này trên cluster của tôi', 'trigger pipeline deploy giúp tôi') — agent không "
    "có quyền truy cập hệ thống nội bộ nào, không thể phân biệt bằng cách trả lời, phải guardrail "
    "chặn rõ (khác hẳn yêu cầu ĐỌC 1 trang web công khai qua URL — cái đó TRONG PHẠM VI, xem trên); "
    "hỏi về kiến trúc nội bộ của chính agent này (harness/"
    "guardrail/code); BẤT KỲ chủ đề nào không liên quan DevOps/hạ tầng (nấu ăn, y tế, pháp lý, tin "
    "tức, chủ đề lập trình KHÔNG liên quan vận hành/triển khai như thuật toán, UI framework...).\n\n"
    "MỨC ĐỘ TỰ TIN — đây là điểm khác biệt so với phân loại nhị phân: nếu câu hỏi RÕ RÀNG khớp 1 "
    f"mục TRONG PHẠM VI hoặc NGOÀI PHẠM VI ở trên, trả lời tự tin bằng '{_IN_TAG}'/'{_OUT_TAG}'. Nếu "
    "câu hỏi KHÔNG khớp rõ mục nào — diễn đạt lạ, chủ đề mới không có trong danh sách trên, câu quá "
    f"ngắn/thiếu ngữ cảnh để chắc chắn kể cả sau khi đọc lịch sử hội thoại — trả '{_UNCERTAIN_TAG}: "
    f"<lý do>' thay vì đoán liều. CHỈ dùng '{_OUT_TAG}' khi bạn THỰC SỰ CHẮC CHẮN; còn nghi ngờ dù "
    f"chỉ một chút thì dùng '{_UNCERTAIN_TAG}'.\n\n"
    f"CHỈ trả lời ĐÚNG 1 DÒNG theo định dạng: '{_OUT_TAG}: <lý do ngắn>' hoặc "
    f"'{_UNCERTAIN_TAG}: <lý do ngắn>' hoặc '{_IN_TAG}: <lý do ngắn>'. Không thêm chữ nào khác, "
    "không giải thích dài."
)

_scope_guardrail_agent = Agent(
    name="DevOps scope guardrail",
    model=get_model(),
    instructions=_SCOPE_INSTRUCTIONS,
    # temperature=0: đây là tác vụ PHÂN LOẠI, không phải sinh văn tự do — giảm tính ngẫu nhiên giữa
    # các lần gọi cho CÙNG 1 input (verify sống lúc điều tra bug "guardrail chặn nhầm câu hỏi tiếp
    # nối ngắn" cho thấy cùng 1 chuỗi hội thoại có lúc pass có lúc trip — kỷ luật temperature=0
    # không loại bỏ hoàn toàn nhưng giảm rõ rệt phần do sampling ngẫu nhiên).
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
    guardrail phụ không nên tự nó chặn nhầm câu hỏi DevOps hợp lệ vì lỗi parse."""
    line = (text or "").strip()
    upper = line.upper()
    reason = line.split(":", 1)[-1].strip() if ":" in line else line
    if upper.startswith(_OUT_TAG):
        return ScopeCheck(verdict="out_of_scope", reason=reason)
    if upper.startswith(_UNCERTAIN_TAG):
        return ScopeCheck(verdict="uncertain", reason=reason)
    return ScopeCheck(verdict="in_scope", reason=reason)


async def classify_scope(question, context=None):
    """Gọi bộ phân loại 3 mức TRỰC TIẾP — dùng ở chatdemo.py TRƯỚC Runner.run/run_streamed, để có
    thể tiêm hint cho mức UNCERTAIN trước khi model chính bắt đầu chạy (KHÔNG thể làm việc này sau
    khi Runner.run đã bắt đầu — @input_guardrail không có cơ chế sửa input/instructions cho lượt
    đang chạy)."""
    result = await Runner.run(_scope_guardrail_agent, question, context=context)
    return _parse_scope_check(result.final_output)


_UNCERTAIN_HINT_TEMPLATE = (
    "\n\n---\n"
    "GHI CHÚ NỘI BỘ (bộ phân loại phạm vi tự động sinh ra, KHÔNG phải lời người dùng): câu hỏi VỪA "
    "RỒI được đánh giá KHÔNG CHẮC CHẮN có thuộc phạm vi DevOps/hạ tầng hay không (lý do phân loại: "
    "{reason}). Đọc kỹ lại câu hỏi trong ngữ cảnh hội thoại: nếu thấy THẬT SỰ ngoài phạm vi, hãy "
    "giải thích ngắn gọn giới hạn của bạn (đừng trả lời bừa ngoài chủ đề DevOps); nếu vẫn có vẻ "
    "liên quan (chỉ diễn đạt lạ/thiếu ngữ cảnh riêng lẻ), hãy trả lời bình thường hoặc hỏi lại xác "
    "nhận nếu cần — ĐỪNG tự động từ chối chỉ vì cách hỏi khác thường."
)


def build_uncertain_hint(reason):
    return _UNCERTAIN_HINT_TEMPLATE.format(reason=reason or "không rõ")


@input_guardrail
async def devops_scope_guardrail(ctx, agent, input):
    """Vẫn giữ dạng @input_guardrail — dùng làm lớp bảo vệ DỰ PHÒNG cho caller gọi Runner.run trực
    tiếp không qua chatdemo.py (vd run.py CLI, xem agent.py::devops_agent), và để agent_spec.py có
    object thật tham chiếu khi xuất spec. Đường live chat (chatdemo.py::_run_streamed) KHÔNG dựa
    vào cơ chế trip này nữa — nó gọi classify_scope() trực tiếp TRƯỚC khi chạy model chính, vì cần
    tiêm hint cho mức UNCERTAIN (guardrail SDK không hỗ trợ)."""
    check = await classify_scope(input, context=ctx.context)
    return GuardrailFunctionOutput(output_info=check, tripwire_triggered=check.is_out_of_scope)
