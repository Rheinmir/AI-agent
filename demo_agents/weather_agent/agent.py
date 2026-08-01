"""Weather agent — MVP minh hoạ 3 yếu tố nền tảng: Model, Tools, Instructions.

Xem wiki/concepts/agent.md, model-selection.md, tools.md, instructions.md.
"""

from agents import Agent, function_tool

NO_DATA = "NO_DATA"

_WEATHER_DATA = {
    "hà nội": {"city": "Hà Nội", "temp_c": 29, "condition": "Nhiều mây"},
    "sài gòn": {"city": "Sài Gòn", "temp_c": 33, "condition": "Nắng"},
    "đà nẵng": {"city": "Đà Nẵng", "temp_c": 30, "condition": "Mưa rào"},
    "hạ long": {"city": "Hạ Long", "temp_c": 27, "condition": "Trời quang"},
}


def _normalize(city: str) -> str:
    return city.strip().lower()


def _get_weather_impl(city: str) -> str:
    """Logic thuần, không phụ thuộc SDK — test offline được không cần OPENAI_API_KEY."""
    key = _normalize(city)
    if key not in _WEATHER_DATA:
        return f"{NO_DATA}:{city}"
    data = _WEATHER_DATA[key]
    return f"{data['city']}: {data['temp_c']}°C, {data['condition']}"


@function_tool
def get_weather(city: str) -> str:
    """Tra dữ liệu thời tiết mock cho một thành phố. Trả 'NO_DATA:<city>' nếu không có dữ liệu."""
    return _get_weather_impl(city)


INSTRUCTIONS = (
    "Bạn là weather agent. Luôn gọi tool get_weather để lấy dữ liệu trước khi trả lời — "
    "không bao giờ tự bịa nhiệt độ hay tình trạng thời tiết. "
    "Nếu kết quả tool bắt đầu bằng 'NO_DATA:', hãy nói rõ với người dùng là bạn không có dữ liệu "
    "thời tiết cho thành phố đó, và đừng đoán số liệu thay thế."
)

weather_agent = Agent(
    name="Weather agent",
    model="gpt-4o-mini",
    instructions=INSTRUCTIONS,
    tools=[get_weather],
)
