"""Retrieval gate — quyết định RẺ, TẤT ĐỊNH-HOÁ (temperature=0) TRƯỚC KHI vào guardrail/model
chính: lượt hỏi này có thực sự cần agent tra dữ liệu đã thu thập sẵn (get_city_note/ask_librarian)
hay không? Câu chào, câu hỏi chung chung, câu hỏi tiếp nối không cần data mới — không cần trả về
"cần tra cứu". Đây là 1 quyết định KHÁC guardrail (guardrail = có nằm trong phạm vi thời tiết hay
không; gate này = có cần ĐỤNG tới data đã thu thập hay không) — 2 câu hỏi độc lập, không thay thế
nhau.

Không bắt buộc TIẾT KIỆM được gì lớn cho weather_agent hiện tại (get_city_note vốn đã RẺ, không
gọi model chính), nhưng đây là bước NỀN TẢNG đúng đắn: model chính vẫn tự quyết định gọi tool nào
qua INSTRUCTIONS — gate này chỉ cho THÊM 1 gợi ý sớm trong system context để tránh việc model tự
ý gọi `get_city_note`/`ask_librarian` cho câu hỏi rõ ràng không cần (vd 'cảm ơn nhé', 'bạn khoẻ
không') — giảm tool-call thừa, không thay đổi hành vi câu hỏi thật cần data.

Fail-OPEN (retrieve=True) nếu lỗi gọi model/parse JSON — 1 gate phụ không nên tự nó chặn mất thông
tin, thà tra thừa còn hơn bỏ sót (cùng kỷ luật fail-open đã áp cho guardrail parse lỗi)."""

import json

from agents import Agent, ModelSettings, Runner

from demo_agents.weather_agent.model_provider import get_model

_GATE_PROMPT = (
    "Bạn là bộ gác cổng RẺ cho 1 weather agent — quyết định lượt hỏi này có cần agent tra dữ liệu "
    "đã thu thập sẵn (ghi chú múi giờ/khí hậu 1 thành phố) hay KHÔNG. Chỉ trả lời ĐÚNG 1 dòng JSON, "
    "không thêm chữ nào khác:\n"
    '{"retrieve": true/false, "reason": "<5 từ>"}\n\n'
    "true nếu câu hỏi nhắc tới hoặc ngầm hỏi về múi giờ/khí hậu/đặc điểm 1 thành phố cụ thể (kể cả "
    "câu tiếp nối ngắn như 'còn Đà Nẵng thì sao'). false nếu chỉ là lời chào/cảm ơn/xã giao, câu "
    "hỏi thời tiết HIỆN TẠI thuần (dùng get_weather, không phải data đã thu thập), hoặc câu hỏi "
    "hoàn toàn không liên quan thành phố nào."
)

_gate_agent = Agent(
    name="Weather retrieval gate",
    model=get_model(),
    instructions=_GATE_PROMPT,
    model_settings=ModelSettings(temperature=0),
)


async def should_retrieve(question: str) -> tuple[bool, str]:
    """Trả (retrieve?, reason). Fail-open (True, ...) nếu model lỗi/JSON méo."""
    try:
        result = await Runner.run(_gate_agent, question)
        text = (result.final_output or "").strip()
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            return True, "gate không trả JSON — fail-open"
        decision = json.loads(text[start : end + 1])
        return bool(decision.get("retrieve", True)), str(decision.get("reason", ""))
    except Exception as exc:  # noqa: BLE001 — gate phụ, KHÔNG được làm crash lượt chat thật
        return True, f"gate lỗi ({type(exc).__name__}) — fail-open"
