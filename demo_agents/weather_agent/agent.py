"""Weather agent — minh hoạ 3 yếu tố nền tảng: Model, Tools, Instructions — mở rộng thêm 4 layer
của wiki/concepts/agent-7-layers.md: Data Collector (get_city_note, đọc từ wiki/sources/ CỦA RIÊNG
agent này — xem data_collector.py và chatdemo.py::/wiki), Memory dài hạn xuyên phiên
(recall_last_city, khác SQLiteSession chỉ nhớ trong 1 phiên — xem chatdemo.py), Harness tường minh
(giới hạn vòng lặp + retry — xem harness.py), input guardrail thật (chặn câu hỏi ngoài phạm vi
TRƯỚC khi model chính tự "sáng tác" cách từ chối — xem guardrails.py), lifecycle hooks cho
monitoring (mỗi tool call/LLM call/kết thúc lượt được ghi lại — xem monitoring.py). Định nghĩa agent
trung lập framework để xuất sang SDK khác — xem agent_spec.py + exporters/.

Tool gọi API thời tiết THẬT (Open-Meteo — miễn phí, không cần API key) cho bất kỳ thành phố nào
trên thế giới, thay vì bảng tra mock. Xem wiki/concepts/agent.md, model-selection.md, tools.md,
instructions.md.

MCP fetch (đọc-only 1 URL cụ thể qua mcp-server-fetch, xem mcp_tools/README.md): build_agent_with_mcp()
bên dưới — CÙNG pattern với demo_agents/devops_agent/agent.py, không viết logic riêng.

ask_librarian: gọi SANG process librarian_agent (2 thực thể tách rời, giao tiếp qua Unix socket
tham khảo herdrdev/herdr — xem demo_agents/librarian_agent/README.md) khi get_city_note đã NO_DATA.
Librarian là agent thật CÓ reasoning, khác get_city_note (khớp CHÍNH XÁC) — xem docstring tool bên
dưới. Đây là TOOL THÊM, KHÔNG thay thế get_city_note."""

import dataclasses
from pathlib import Path

import requests

from agents import Agent, function_tool

from demo_agents.librarian_agent import client as librarian_client
from demo_agents.librarian_agent.client import LibrarianUnavailable
from demo_agents.weather_agent.data_collector import lookup_city_note
from demo_agents.weather_agent.guardrails import weather_scope_guardrail
from demo_agents.weather_agent.memory import recall_last_city as _recall_last_city
from demo_agents.weather_agent.memory import remember_last_city as _remember_last_city
from demo_agents.weather_agent.model_provider import get_model
from demo_agents.weather_agent.monitoring import WeatherAgentHooks
from mcp_tools.channels import github_search_impl, rss_read_impl, youtube_transcript_impl

NO_DATA = "NO_DATA"

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT_S = 8

_WMO_DESCRIPTIONS = {
    0: "Trời quang", 1: "Ít mây", 2: "Có mây", 3: "Nhiều mây",
    45: "Sương mù", 48: "Sương mù đóng băng",
    51: "Mưa phùn nhẹ", 53: "Mưa phùn", 55: "Mưa phùn dày",
    56: "Mưa phùn đóng băng nhẹ", 57: "Mưa phùn đóng băng dày",
    61: "Mưa nhẹ", 63: "Mưa vừa", 65: "Mưa to",
    66: "Mưa đóng băng nhẹ", 67: "Mưa đóng băng nặng",
    71: "Tuyết rơi nhẹ", 73: "Tuyết rơi vừa", 75: "Tuyết rơi dày", 77: "Hạt tuyết",
    80: "Mưa rào nhẹ", 81: "Mưa rào vừa", 82: "Mưa rào dữ dội",
    85: "Mưa tuyết rào nhẹ", 86: "Mưa tuyết rào dày",
    95: "Dông", 96: "Dông kèm mưa đá nhẹ", 99: "Dông kèm mưa đá nặng",
}


def _wmo_description(code: int) -> str:
    return _WMO_DESCRIPTIONS.get(code, f"mã thời tiết {code}")


def _geocode(city: str):
    """Gọi Open-Meteo Geocoding API thật. Trả {"name","lat","lon"} hoặc None nếu không tìm thấy
    hoặc lỗi mạng — tách riêng khỏi _get_weather_impl để mock độc lập lúc test.

    Lưu ý bug thật gặp phải: `language=vi` làm API xếp hạng kết quả khác hẳn `language=en` (vd
    "New York" bị lệch thành "York, Nebraska" — không có trong top-10 khi tìm bằng tiếng Việt,
    nhưng là kết quả #1 khi tìm bằng tiếng Anh). Dùng `language=en` để tra cứu ổn định, đồng thời
    lấy top-5 rồi chọn kết quả có dân số (population) lớn nhất — tránh chọn nhầm một địa danh nhỏ
    trùng tên với thành phố lớn nổi tiếng hơn."""
    try:
        resp = requests.get(
            _GEOCODE_URL,
            params={"name": city, "count": 5, "language": "en", "format": "json"},
            timeout=_TIMEOUT_S,
        )
        resp.raise_for_status()
        results = resp.json().get("results") or []
    except requests.RequestException:
        return None
    if not results:
        return None
    top = max(results, key=lambda r: r.get("population") or 0)
    return {"name": top.get("name", city), "lat": top["latitude"], "lon": top["longitude"]}


def _fetch_current(lat: float, lon: float):
    """Gọi Open-Meteo Forecast API thật. Trả {"temp_c","code"} hoặc None nếu lỗi mạng/dữ liệu
    thiếu trường mong đợi."""
    try:
        resp = requests.get(
            _FORECAST_URL,
            params={"latitude": lat, "longitude": lon, "current": "temperature_2m,weather_code"},
            timeout=_TIMEOUT_S,
        )
        resp.raise_for_status()
        current = resp.json().get("current") or {}
    except requests.RequestException:
        return None
    if "temperature_2m" not in current or "weather_code" not in current:
        return None
    return {"temp_c": current["temperature_2m"], "code": current["weather_code"]}


def _get_weather_impl(city: str) -> str:
    """Tra thời tiết HIỆN TẠI thật qua Open-Meteo (geocode -> forecast). Không phụ thuộc Agent
    SDK — test được bằng cách mock _geocode/_fetch_current hoặc requests.get, không cần
    DEEPSEEK_API_KEY/OPENAI_API_KEY (đó là key cho Model, không phải cho tool này)."""
    city = city.strip()
    if not city:
        return f"{NO_DATA}:{city}"
    place = _geocode(city)
    if place is None:
        return f"{NO_DATA}:{city}"
    weather = _fetch_current(place["lat"], place["lon"])
    if weather is None:
        return f"{NO_DATA}:{city}"
    _remember_last_city(place["name"])
    return f"{place['name']}: {weather['temp_c']}°C, {_wmo_description(weather['code'])}"


@function_tool
def get_weather(city: str) -> str:
    """Tra thời tiết HIỆN TẠI thật cho một thành phố bất kỳ trên thế giới (qua Open-Meteo).
    Trả 'NO_DATA:<city>' nếu không tìm thấy thành phố hoặc lỗi gọi API."""
    return _get_weather_impl(city)


@function_tool
def get_city_note(city: str) -> str:
    """Tra ghi chú thực tế đã thu thập sẵn (múi giờ, đặc điểm khí hậu chung theo mùa) cho MỘT SỐ
    thành phố tiêu biểu — khác get_weather (dữ liệu thời tiết THỜI GIAN THỰC).

    CƠ CHẾ TRA CỨU (để không coi đây là hộp đen/semantic search): nguồn là các file
    demo_agents/weather_agent/wiki/sources/*.md, mỗi thành phố 1 file, khớp theo TÊN FILE hoặc
    `aliases:` khai trong frontmatter — so khớp CHÍNH XÁC sau khi hạ chữ thường + gộp khoảng trắng
    (vd 'Hà Nội', 'ha noi', 'HANOI' đều khớp file hanoi.md nếu file đó khai alias tương ứng) —
    KHÔNG phải tìm kiếm ngữ nghĩa/gần đúng. Thành phố viết đúng chính tả nhưng KHÔNG khớp bất kỳ
    alias nào đã khai vẫn trả NO_DATA, dù về mặt địa lý thành phố đó có tồn tại.

    Trả 'NO_DATA:<city>' nếu thành phố không có trong tập dữ liệu đã thu thập — KHÔNG bịa ghi chú
    thay thế."""
    note = lookup_city_note(city)
    return note if note else f"{NO_DATA}:{city}"


@function_tool
def ask_librarian(query: str) -> str:
    """Nhờ librarian agent (process RIÊNG, gọi qua socket — xem
    demo_agents/librarian_agent/README.md) tìm hộ trong wiki của bạn khi get_city_note đã trả
    NO_DATA nhưng câu hỏi vẫn có vẻ liên quan tới ghi chú thành phố đã thu thập. Khác get_city_note
    (khớp CHÍNH XÁC tên/alias), librarian là agent thật CÓ REASONING — hiểu được câu hỏi diễn đạt
    khác cách viết trong file, nhưng vẫn bám sát nội dung thật trong wiki, không bịa. CHỈ gọi tool
    này SAU KHI get_city_note đã NO_DATA — đừng gọi trước để tiết kiệm (get_city_note rẻ và tất
    định hơn). Trả 'NO_DATA:<lý do>' nếu librarian không khả dụng (chưa chạy) hoặc cũng không tìm
    thấy gì liên quan."""
    try:
        result = librarian_client.ask_search("weather", query)
    except LibrarianUnavailable as e:
        return f"{NO_DATA}:librarian không khả dụng ({e})"
    answer = (result.get("answer") or "").strip()
    return answer if answer and answer != "NO_DATA" else f"{NO_DATA}:{query}"


@function_tool
def recall_last_city() -> str:
    """Tra thành phố agent tra cứu thời tiết THÀNH CÔNG gần nhất — ở BẤT KỲ cuộc trò chuyện nào
    trước đó, kể cả sau khi khởi động lại server (nhớ XUYÊN phiên, khác trí nhớ trong-phiên có
    sẵn). Trả 'NO_DATA' nếu chưa từng tra cứu thành công lần nào. CHỈ dùng để GỢI Ý — luôn xác nhận
    lại với người dùng trước khi coi đây là thành phố họ đang hỏi, không tự ý dùng làm câu trả lời."""
    city = _recall_last_city()
    return city if city else NO_DATA


# 3 tool từ mcp_tools/channels.py (KHÔNG PHẢI MCP — xem docstring module đó) — cùng convention với
# demo_agents/devops_agent/agent.py, LUÔN có trong weather_agent gốc (không cần build_agent_with_mcp).
@function_tool
def github_search(query: str) -> str:
    """Tìm kiếm repo GitHub công khai. Trả 'NO_DATA:<lý do>' nếu gh CLI chưa cài/chưa auth trên máy
    này, hoặc không có kết quả — KHÔNG bịa tên repo thay thế."""
    return github_search_impl(query)


@function_tool
def youtube_transcript(url: str) -> str:
    """Lấy phụ đề (transcript) của 1 video YouTube cụ thể (vd giải thích hiện tượng thời tiết) — trả
    về text thuần. Trả 'NO_DATA:<lý do>' nếu video không có phụ đề hoặc yt-dlp chưa cài."""
    return youtube_transcript_impl(url)


@function_tool
def rss_feed(feed_url: str) -> str:
    """Đọc các mục mới nhất của 1 RSS/Atom feed CỤ THỂ (vd feed tin thời tiết). Trả 'NO_DATA:<lý
    do>' nếu URL không phải feed hợp lệ."""
    return rss_read_impl(feed_url)


INSTRUCTIONS = (
    "Bạn là weather agent. Luôn gọi tool get_weather để lấy dữ liệu trước khi trả lời — "
    "không bao giờ tự bịa nhiệt độ hay tình trạng thời tiết. "
    "Nếu kết quả tool bắt đầu bằng 'NO_DATA:', hãy nói rõ với người dùng là bạn không có dữ liệu "
    "thời tiết cho thành phố đó, và đừng đoán số liệu thay thế.\n\n"
    "Nếu người dùng hỏi mà không nêu rõ thành phố (vd 'còn hôm nay thì sao', 'ở đó thế nào') và "
    "đây là tin nhắn ĐẦU TIÊN trong cuộc trò chuyện này (không có lượt trước để suy ra), hãy gọi "
    "tool recall_last_city để xem có gợi ý nào không. Nếu có, HỎI XÁC NHẬN lại với người dùng "
    "('Bạn có phải đang hỏi về <thành phố> — nơi bạn hỏi lần gần nhất không?') thay vì tự ý coi đó "
    "là câu trả lời — nó chỉ là gợi ý, có thể sai. Nếu recall_last_city trả 'NO_DATA', hỏi lại "
    "người dùng muốn xem thời tiết thành phố nào.\n\n"
    "Nếu người dùng hỏi thêm về múi giờ hoặc đặc điểm khí hậu chung của một thành phố (khác câu "
    "hỏi thời tiết HIỆN TẠI), gọi tool get_city_note TRƯỚC (rẻ, tất định). Nếu get_city_note trả "
    "'NO_DATA:' NHƯNG câu hỏi vẫn nghe như có thể liên quan tới ghi chú đã thu thập (vd người dùng "
    "diễn đạt khác cách viết trong wiki), gọi tiếp tool ask_librarian trước khi kết luận không có — "
    "librarian hiểu diễn đạt tự nhiên hơn get_city_note. Nếu CẢ HAI đều NO_DATA, nói rõ bạn chưa có "
    "ghi chú cho thành phố đó — KHÔNG tự bịa thông tin múi giờ/khí hậu thay thế. Nếu người dùng hỏi "
    "TẠI SAO một thành phố không có ghi chú dù nghe hợp lý (vd viết đúng tên), giải thích ĐÚNG cơ "
    "chế: đây là danh sách nhỏ đã thu thập sẵn (wiki riêng của bạn, xem /wiki), get_city_note khớp "
    "CHÍNH XÁC theo tên/alias đã khai, ask_librarian có reasoning nhưng vẫn chỉ bám nội dung thật "
    "trong wiki — cả 2 đều không bịa, nên NO_DATA từ cả hai nghĩa là thật sự chưa thu thập.\n\n"
    "Khi người dùng hỏi bạn làm được gì / năng lực của bạn / help (vd 'bạn làm được gì?', "
    "'bạn có thể giúp gì?', 'what can you do'), hãy tự khai báo ĐÚNG năng lực thật, không phóng "
    "đại và không bịa thêm chức năng không có:\n"
    "- CÓ THỂ: (1) tra thời tiết HIỆN TẠI (nhiệt độ, tình trạng trời) cho bất kỳ thành phố nào "
    "trên thế giới qua tool get_weather (dữ liệu thật từ Open-Meteo); (2) nhớ ngữ cảnh hội thoại "
    "trong phiên hiện tại (có thể hỏi tiếp không cần nhắc lại tên thành phố); (3) tra ghi chú múi "
    "giờ/khí hậu chung cho MỘT SỐ thành phố tiêu biểu đã thu thập sẵn (get_city_note, khớp chính "
    "xác) + hỏi librarian agent tìm hộ nếu diễn đạt khác cách viết trong wiki (ask_librarian, cần "
    "librarian đang chạy); (4) nhớ (dạng gợi ý, luôn hỏi xác nhận lại) thành phố bạn hỏi gần nhất ở "
    "LẦN TRÒ CHUYỆN TRƯỚC, kể cả sau khi đóng và mở lại cuộc trò chuyện mới; (5) tìm repo GitHub "
    "công khai (tool github_search — cần gh CLI cài/auth trên máy chạy); (6) lấy phụ đề 1 video "
    "YouTube cụ thể (tool youtube_transcript); (7) đọc 1 RSS/Atom feed cụ thể (tool rss_feed).\n"
    "- KHÔNG THỂ: dự báo nhiều ngày tới, dữ liệu lịch sử, hay bất kỳ chủ đề nào ngoài thời tiết — "
    "nếu người dùng hỏi ngoài phạm vi này, nói rõ đây là giới hạn hiện tại thay vì cố trả lời."
)

# Addendum CHỈ áp dụng cho bản agent có gắn MCP fetch tool (xem build_agent_with_mcp) — cùng quy ước
# với demo_agents/devops_agent/agent.py, KHÔNG đưa vào INSTRUCTIONS gốc để weather_agent (bản KHÔNG
# có mcp_servers) không tự nhận vơ khả năng tools=[...] của nó không thật sự có.
_MCP_INSTRUCTIONS_ADDENDUM = (
    "\n\nBạn CÓ THÊM 2 khả năng internet THẬT, đọc-only, qua MCP — CHỈ dùng khi câu hỏi thật sự liên "
    "quan thời tiết:\n"
    "- 'web_search_exa' (Exa) — TÌM KIẾM thật trên internet theo mô tả tự nhiên (vd 'tin bão mới "
    "nhất ở khu vực X', 'cảnh báo thời tiết cực đoan gần đây') — không cần URL sẵn.\n"
    "- 'fetch'/'web_fetch_exa' — đọc nội dung MỘT trang web CỤ THỂ khi người dùng đưa URL rõ ràng "
    "(vd bài viết thời tiết), trả về nội dung dạng markdown.\n"
    "Luôn nói rõ thông tin lấy từ tìm kiếm/trang web, không lẫn với dữ liệu Open-Meteo (get_weather)."
)

_SKILL_PATH = Path(__file__).parent / "SKILL.md"


def _load_skill_addendum() -> str:
    """Procedural memory — đọc SKILL.md (con người sửa tay trực tiếp, KHÔNG qua tool/CRUD) lúc
    khởi tạo agent, nối vào cuối INSTRUCTIONS dưới dạng 1 section riêng. Fail-open (chuỗi rỗng)
    nếu file không tồn tại/đọc lỗi — thiếu procedural memory không nên chặn agent khởi động."""
    try:
        text = _SKILL_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    if not text:
        return ""
    return f"\n\n## Kỹ năng đã học (procedural memory, sửa tay được — xem SKILL.md)\n{text}"


INSTRUCTIONS += _load_skill_addendum()

weather_agent = Agent(
    name="Weather agent",
    model=get_model(),
    instructions=INSTRUCTIONS,
    tools=[get_weather, get_city_note, ask_librarian, recall_last_city, github_search, youtube_transcript, rss_feed],
    input_guardrails=[weather_scope_guardrail],
    hooks=WeatherAgentHooks(),
)


def build_agent_with_mcp(mcp_servers):
    """Trả về BẢN SAO của weather_agent có gắn thêm mcp_servers (list server ĐÃ CONNECT — xem
    agents.mcp.MCPServerManager, dùng trong run.py/chatdemo.py). Cùng pattern với
    demo_agents/devops_agent/agent.py::build_agent_with_mcp — dataclasses.replace(), không định
    nghĩa lại model/tools/guardrails/hooks. `weather_agent` gốc KHÔNG đổi."""
    return dataclasses.replace(
        weather_agent,
        instructions=INSTRUCTIONS + _MCP_INSTRUCTIONS_ADDENDUM,
        mcp_servers=list(mcp_servers),
    )
