"""Harness — vòng lặp điều phối tường minh quanh Runner.run: giới hạn số turn model được gọi
(chặn agent lặp vô hạn), retry có backoff khi lỗi tạm thời (mạng, timeout gọi model), VÀ tự quyết
định khi nào KHÔNG cần gọi model (câu hỏi "bạn làm được gì" trả lời tất định, không qua LLM — xem
_is_capability_question bên dưới). Trước đây `Runner.run_sync` được gọi thẳng trong chatdemo.py với
max_turns mặc định ẩn của SDK (10, không ai chọn) và không retry — 1 lần lỗi mạng là fail thẳng, xem
wiki/concepts/agent-7-layers.md § Harness.

Đổi từ `Runner.run_sync` sang `await Runner.run` (async) khi thêm MCP fetch tool: agent có gắn MCP
server phải chạy TRÊN ĐÚNG event loop đã connect server đó (xem chatdemo.py::_MCPBridge) —
`Runner.run_sync` tự tạo event loop RIÊNG, không dùng lại loop đang chạy, sẽ vỡ kết nối MCP nếu gọi
từ bên trong 1 loop khác. `run_with_harness` giờ là `async def`, caller tự `await`/submit qua bridge.
"""

import asyncio
import dataclasses
import re
import uuid
from dataclasses import dataclass

from agents import Runner
from agents.exceptions import InputGuardrailTripwireTriggered, MaxTurnsExceeded
from openai.types.responses import ResponseTextDeltaEvent

from demo_agents.weather_agent.guardrails import OUT_OF_SCOPE_MESSAGE, build_uncertain_hint, classify_scope
from demo_agents.weather_agent.monitoring import log_event
from demo_agents.weather_agent.retrieval_gate import should_retrieve

# Tên tool TRA DỮ LIỆU ĐÃ THU THẬP — gate chỉ ẩn NHÓM NÀY khỏi agent khi retrieve=False, không đụng
# get_weather (thời gian thực, không phải "đã thu thập")/recall_last_city (memory khác, rẻ)/tool
# internet (github_search/youtube_transcript/rss_feed — không thuộc phạm vi gate này).
_RETRIEVAL_TOOL_NAMES = {"get_city_note", "ask_librarian"}

DEFAULT_MAX_TURNS = 6
DEFAULT_MAX_RETRIES = 2
_BACKOFF_S = (0.5, 1.5)


@dataclass
class RunMeta:
    """Truyền qua Runner.run_sync(context=...) — cách CHÍNH THỐNG của Agents SDK để đưa dữ liệu
    tuỳ biến (session_id, run_id) tới hooks (monitoring.py đọc lại qua context.context). run_id
    là khoá DUY NHẤT cho 1 lượt gọi harness — dùng để ghép cặp tool_start/tool_end,
    llm_start/llm_end của CÙNG 1 lượt khi tính latency, không đoán mò theo thứ tự thời gian."""

    session_id: str
    run_id: str

# Người dùng report: hỏi "bạn làm được gì" nhưng câu trả lời của MODEL (theo INSTRUCTIONS, văn tự
# do) không nhắc tên các layer thật (Tools, Data Collector, Memory, Harness...) — vì đó là văn xuôi
# LLM tự diễn giải, không đảm bảo giữ đúng từ khoá. Harness tự bắt câu hỏi loại này và trả thẳng 1
# báo cáo tất định, KHÔNG qua model — luôn đúng, luôn đủ tên layer, 0 rủi ro LLM diễn giải lệch.
_CAPABILITY_PATTERNS = (
    "làm được gì", "làm gì được", "năng lực", "giúp được gì", "giúp gì được",
    "what can you do", "help",
)

_CAPABILITY_REPORT = (
    "Báo cáo năng lực theo đúng 7 layer kiến trúc agent — câu trả lời này do **Harness** sinh ra "
    "TẤT ĐỊNH (không qua model), để luôn đủ và đúng tên từng layer:\n\n"
    "- **Tools**: `get_weather` — tra thời tiết HIỆN TẠI thật qua Open-Meteo cho bất kỳ thành phố "
    "nào trên thế giới; `github_search`/`youtube_transcript`/`rss_feed` — tìm repo GitHub/lấy phụ "
    "đề video YouTube/đọc RSS feed công khai (xem mcp_tools/README.md); nếu có MCP server kết nối "
    "được (`fetch`/`web_search_exa`/`web_fetch_exa`) thì còn đọc/tìm kiếm trang web thật qua MCP.\n"
    "- **Data Collector**: `get_city_note` — ghi chú múi giờ/khí hậu chung đã thu thập sẵn, CHỈ "
    "cho một số thành phố tiêu biểu (không phải mọi thành phố, không bịa thêm); nguồn là wiki "
    "riêng của agent này (`wiki/sources/`, xem thêm ở /wiki), human CRUD-able. Cơ chế tra cứu là "
    "khớp CHÍNH XÁC theo tên file/alias (không phải semantic search) — xem docstring get_city_note "
    "trong agent.py để biết chi tiết. `ask_librarian` — khi get_city_note NO_DATA, hỏi tiếp "
    "librarian agent THẬT (process riêng, gọi qua socket — xem demo_agents/librarian_agent/) có "
    "reasoning, hiểu diễn đạt khác cách viết file nhưng vẫn bám nội dung thật trong wiki, không "
    "bịa; cần librarian đang chạy, nếu không sẽ tự báo NO_DATA rõ lý do.\n"
    "- **Memory**: 3 loại — nhớ trong 1 cuộc trò chuyện (SQLiteSession), nhớ thành phố tra cứu "
    "gần nhất XUYÊN các cuộc trò chuyện khác nhau (`recall_last_city`, dạng gợi ý, luôn hỏi xác "
    "nhận lại trước khi coi là đúng), và wiki memory browse được tại /wiki (kiến thức thu thập "
    "sẵn, tách vật lý khỏi wiki cấp dự án).\n"
    "- **Harness**: vòng lặp giới hạn tối đa 6 bước, tự retry khi lỗi mạng tạm thời — chính đoạn "
    "báo cáo này do Harness kiểm soát, không phải model tự viết.\n"
    "- **Context/Instruction**: CHƯA có layer tự viết — vẫn dựa hoàn toàn vào việc lắp ráp prompt "
    "mặc định của Agents SDK.\n"
    "- **Evaluation**: chạy NGOÀI, offline (`harness/scripts/wikieval.py`), không nằm trong đường "
    "trả lời câu hỏi này.\n"
    "- **Model Hosting**: dùng API hosted (DeepSeek/OpenAI), không tự host GPU nên phần KV "
    "cache/VRAM không áp dụng cho demo này.\n\n"
    "KHÔNG THỂ: dự báo nhiều ngày tới, dữ liệu lịch sử, hay bất kỳ chủ đề nào ngoài thời tiết."
)


def _is_capability_question(question):
    q = question.strip().lower()
    return any(p in q for p in _CAPABILITY_PATTERNS)


# Fast-path TỐI GIẢN cho câu chào/cảm ơn — quy mô SIÊU NHỎ so với 1 graph engine tổng quát nhiều
# node/edge (không cần cho 2 demo agent hiện tại): regex TẤT ĐỊNH, KHÔNG gọi thêm 1 LLM call nào
# (rẻ hơn cả retrieval_gate.py) — chỉ khớp khi CẢ CÂU chỉ gồm 1 cụm chào/cảm ơn ngắn (fail-open về
# full loop nếu câu dài hơn/có nội dung khác kèm theo, vd "chào bạn, thời tiết Hà Nội thế nào" —
# KHÔNG được khớp nhầm, để không bỏ sót câu hỏi thật đi kèm lời chào).
_GREETING_ONLY_RE = re.compile(
    r"^(xin\s+)?(chào|hi|hello|hey|cảm ơn|cám ơn|thanks|thank you|ok|oke|okay|được rồi|ừ|ừm)"
    r"[\s,.!?]*(bạn|nhé|nha|nhá)?[\s,.!?]*$",
    re.IGNORECASE,
)
_GREETING_REPLY = (
    "Chào bạn! Mình là weather agent — hỏi mình về thời tiết hiện tại, múi giờ, hay khí hậu chung "
    "của 1 thành phố bất kỳ nhé."
)


def _is_greeting_only(question):
    return bool(_GREETING_ONLY_RE.match(question.strip()))


class _StaticResult:
    """Bọc 1 chuỗi tĩnh cùng interface với RunResult của SDK (chỉ cần .final_output) — để
    chatdemo.py không cần biết câu trả lời tới từ Harness ngắn mạch hay từ model thật."""

    def __init__(self, text):
        self.final_output = text


async def run_with_harness(
    agent, question, session, session_id=None, max_turns=DEFAULT_MAX_TURNS, max_retries=DEFAULT_MAX_RETRIES
):
    """Chạy agent qua Runner.run (async) với giới hạn vòng lặp tường minh + retry backoff cho lỗi
    tạm thời. MaxTurnsExceeded KHÔNG retry — đó là lỗi tất định (agent thật sự lặp quá số vòng cho
    phép), thử lại sẽ lặp lại đúng kết quả đó. Câu hỏi "làm được gì" được trả lời tất định, không
    gọi model (xem _CAPABILITY_REPORT) — trường hợp ngắn mạch này KHÔNG được lưu vào session vì
    không thuộc luồng hội thoại thời tiết thật.

    Phạm vi câu hỏi được phân loại 3 mức qua `classify_scope()` (guardrails.py) TRƯỚC khi chạy model
    chính — KHÔNG dựa vào @input_guardrail's tripwire nữa (đường này cần TIÊM hint cho mức UNCERTAIN
    trước khi Runner.run bắt đầu, guardrail SDK không hỗ trợ sửa input cho lượt đang chạy). OUT_OF_
    SCOPE (tự tin) → chặn cứng, trả OUT_OF_SCOPE_MESSAGE, không gọi model chính. UNCERTAIN → KHÔNG
    chặn, chỉ nối thêm 1 đoạn ghi chú vào instructions của bản sao agent (dataclasses.replace, agent
    gốc không đổi) gợi ý model tự cân nhắc hỏi lại thay vì tự chối cứng. `weather_scope_guardrail`
    (@input_guardrail, vẫn gắn trên `agent`) vẫn còn đó làm lớp dự phòng cho caller không qua harness
    (vd run.py) — bắt lại đây cho chắc, dù hiếm khi trip khi đã qua bước phân loại thủ công này.

    `async def` (không phải sync) — caller PHẢI `await`, chạy trên ĐÚNG event loop đã connect MCP
    server của `agent` (nếu có), xem chatdemo.py::_MCPBridge/run.py::_run_async. `session_id` (tên
    phiên chat, khác `session` là object SQLiteSession) được ghi kèm mọi sự kiện monitoring để
    dashboard /monitor phân tích được theo từng phiên — mỗi lần gọi tự sinh `run_id` mới (UUID) để
    ghép cặp sự kiện của ĐÚNG lượt này khi tính latency. Raise lỗi cuối cùng sau khi hết lượt retry."""
    run_id = uuid.uuid4().hex[:12]
    meta = RunMeta(session_id=session_id or "", run_id=run_id)
    if _is_capability_question(question):
        log_event(agent.name, "harness_capability_shortcut", session_id=session_id, run_id=run_id)
        return _StaticResult(_CAPABILITY_REPORT)
    scope = await classify_scope(question, context=meta)
    log_event(
        agent.name, "scope_check", {"verdict": scope.verdict, "reason": scope.reason}, session_id, run_id
    )
    if scope.verdict == "out_of_scope":
        log_event(agent.name, "harness_guardrail_tripped", session_id=session_id, run_id=run_id)
        return _StaticResult(OUT_OF_SCOPE_MESSAGE)
    run_agent = agent
    if scope.verdict == "uncertain":
        run_agent = dataclasses.replace(agent, instructions=agent.instructions + build_uncertain_hint(scope.reason))
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return await Runner.run(
                run_agent, question, context=meta, session=session, max_turns=max_turns
            )
        except InputGuardrailTripwireTriggered:
            log_event(agent.name, "harness_guardrail_tripped", session_id=session_id, run_id=run_id)
            return _StaticResult(OUT_OF_SCOPE_MESSAGE)
        except MaxTurnsExceeded:
            log_event(agent.name, "harness_max_turns_exceeded", session_id=session_id, run_id=run_id)
            raise
        except Exception as e:
            last_error = e
            log_event(
                agent.name,
                "harness_retry",
                {"attempt": attempt, "error": str(e)[:200]},
                session_id,
                run_id,
            )
            if attempt < max_retries:
                await asyncio.sleep(_BACKOFF_S[min(attempt, len(_BACKOFF_S) - 1)])
    log_event(
        agent.name, "harness_retries_exhausted", {"error": str(last_error)[:200]}, session_id, run_id
    )
    raise last_error


async def run_with_harness_streamed(agent, question, session, session_id=None, max_turns=DEFAULT_MAX_TURNS):
    """Bản STREAM của run_with_harness — async generator yield ("tool_start", tool_name) /
    ("text_delta", chunk) / ("done", full_text), dùng cho đường LIVE CHAT (chatdemo.py) để UI hiện
    bubble trạng thái theo từng tool + text chạy theo chunk thay vì chờ xong hẳn mới dump 1 cục.
    Dùng `Runner.run_streamed()` (khác `Runner.run` của bản gốc) — verify SỐNG event shape thật
    trước khi viết hàm này (không đoán API): `run_item_stream_event` tên `tool_called` mang
    `item.raw_item.name`; `raw_response_event` với `data` là `ResponseTextDeltaEvent` mang
    `data.delta`; `result.final_output` đọc được sau khi vòng lặp `stream_events()` xong.

    KHÔNG retry-on-network-error như `run_with_harness` gốc — retry giữa chừng 1 stream đã gửi 1
    phần text cho client là vô nghĩa (client sẽ thấy text lặp/gãy), đây là đánh đổi CHỦ Ý cho đường
    live chat, không phải thiếu sót; `run_with_harness` (không streamed) vẫn giữ nguyên cho CLI/
    test cần retry.

    **Cạnh khó verify sống**: TRƯỚC BẢN 3-TIER này, input guardrail chạy SONG SONG với lượt gọi
    model đầu tiên (giảm latency) nên text_delta CÓ THỂ đã chảy ra trước khi biết trip hay không.
    Từ khi đổi sang `classify_scope()` thủ công (xem docstring module + guardrails.py) — decision
    này BẮT BUỘC PHẢI xong TRƯỚC khi Runner.run_streamed bắt đầu (mới tiêm được hint cho mức
    UNCERTAIN vào instructions) — nên với đường stream này, phân loại phạm vi không còn "song song"
    nữa, đây là đánh đổi CHỦ Ý (thêm ~1 lượt gọi model tuần tự) để đổi lấy khả năng KHÔNG chặn cứng
    khi mơ hồ. `"done"` vẫn là nguồn sự thật cuối cùng phía client như cũ (đề phòng
    InputGuardrailTripwireTriggered dự phòng bên dưới, dù hiếm khi trip khi đã qua bước này)."""
    run_id = uuid.uuid4().hex[:12]
    meta = RunMeta(session_id=session_id or "", run_id=run_id)
    if _is_greeting_only(question):
        log_event(agent.name, "harness_greeting_shortcut", session_id=session_id, run_id=run_id)
        yield ("done", _GREETING_REPLY)
        return
    if _is_capability_question(question):
        log_event(agent.name, "harness_capability_shortcut", session_id=session_id, run_id=run_id)
        yield ("done", _CAPABILITY_REPORT)
        return
    # Phạm vi 3 mức (guardrails.py::classify_scope) — chạy TRƯỚC retrieval gate (rẻ hơn quyết định
    # trước, đắt hơn quyết định sau): OUT_OF_SCOPE tự tin → chặn cứng ngay, không tốn thêm lượt gọi
    # retrieval gate/model chính nào. UNCERTAIN → không chặn, chỉ nối hint vào instructions.
    scope = await classify_scope(question, context=meta)
    log_event(
        agent.name, "scope_check", {"verdict": scope.verdict, "reason": scope.reason}, session_id, run_id
    )
    if scope.verdict == "out_of_scope":
        log_event(agent.name, "harness_guardrail_tripped", session_id=session_id, run_id=run_id)
        yield ("done", OUT_OF_SCOPE_MESSAGE)
        return
    run_agent = agent
    if scope.verdict == "uncertain":
        run_agent = dataclasses.replace(agent, instructions=agent.instructions + build_uncertain_hint(scope.reason))
    # Retrieval gate — quyết định RẺ, temperature=0 (xem retrieval_gate.py): lượt này có cần tool
    # tra dữ liệu đã thu thập không? Nếu KHÔNG, ẩn HẲN 2 tool đó khỏi agent cho lượt này (dựng bản
    # sao qua dataclasses.replace, CÙNG pattern build_agent_with_mcp — nối tiếp trên run_agent ở
    # trên, không phải agent gốc) — model khi đó KHÔNG THỂ gọi nhầm tool thừa, không chỉ là gợi ý
    # suông trong prompt. Fail-open (gate lỗi → giữ nguyên đủ tool) nên KHÔNG có rủi ro mất khả năng
    # nếu gate bản thân trục trặc.
    retrieve, gate_reason = await should_retrieve(question)
    log_event(
        agent.name, "retrieval_gate",
        {"retrieve": retrieve, "reason": gate_reason}, session_id, run_id,
    )
    if not retrieve:
        filtered_tools = [t for t in run_agent.tools if getattr(t, "name", None) not in _RETRIEVAL_TOOL_NAMES]
        run_agent = dataclasses.replace(run_agent, tools=filtered_tools)
    # Đếm iteration = số lần model YÊU CẦU tool (không tính lượt trả lời cuối) — cùng định nghĩa
    # "vòng lặp reason→act→observe" mà bất kỳ agent loop nào cũng có (kể cả loop viết tay), chỉ
    # khác ở chỗ mình đọc số này từ event streaming của Agents SDK thay vì tự đếm trong 1 for-loop
    # lộ liễu. Ghi kèm args/output ĐẦY ĐỦ (không chỉ tên tool) vào monitoring.sqlite3 qua log_event
    # đã có sẵn — KHÔNG mở thêm cơ chế lưu trữ mới (JSONL riêng) chỉ để có "trace xem được từng
    # bước": bảng `events` + cột run_id đã đủ ghép lại đúng thứ tự 1 lượt chat, xem qua /monitor.
    iteration = 0
    try:
        result = Runner.run_streamed(run_agent, question, context=meta, session=session, max_turns=max_turns)
        async for event in result.stream_events():
            if event.type == "run_item_stream_event" and event.name == "tool_called":
                raw_item = getattr(getattr(event, "item", None), "raw_item", None)
                name = getattr(raw_item, "name", None)
                if name:
                    iteration += 1
                    args = getattr(raw_item, "arguments", None)
                    log_event(
                        agent.name, "tool_call",
                        {"tool": name, "args": args, "iteration": iteration},
                        session_id, run_id,
                    )
                    yield ("tool_start", name)
            elif event.type == "run_item_stream_event" and event.name == "tool_output":
                output = getattr(getattr(event, "item", None), "output", None)
                log_event(
                    agent.name, "tool_result",
                    {"output": str(output)[:500] if output is not None else None, "iteration": iteration},
                    session_id, run_id,
                )
            elif event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                yield ("text_delta", event.data.delta)
        yield ("done", result.final_output)
    except InputGuardrailTripwireTriggered:
        log_event(agent.name, "harness_guardrail_tripped", session_id=session_id, run_id=run_id)
        yield ("done", OUT_OF_SCOPE_MESSAGE)
    except MaxTurnsExceeded:
        log_event(agent.name, "harness_max_turns_exceeded", session_id=session_id, run_id=run_id)
        raise
