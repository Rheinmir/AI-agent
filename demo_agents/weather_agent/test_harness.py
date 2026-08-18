import asyncio
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agents.exceptions import InputGuardrailTripwireTriggered, MaxTurnsExceeded

from demo_agents.weather_agent.guardrails import OUT_OF_SCOPE_MESSAGE, ScopeCheck, build_uncertain_hint
from demo_agents.weather_agent.harness import (
    _GREETING_REPLY,
    _is_capability_question,
    _is_greeting_only,
    run_with_harness,
    run_with_harness_streamed,
)

_REQUIRED_KEYWORDS = ["Tools", "Data Collector", "Memory", "Harness", "Context", "Evaluation"]


@pytest.fixture(autouse=True)
def _no_real_monitoring_writes():
    """harness.py giờ gọi monitoring.log_event() ở mỗi nhánh kết quả — patch thành no-op cho MỌI
    test trong file này, tránh ghi vào monitoring.sqlite3 thật khi chạy pytest."""
    with patch("demo_agents.weather_agent.harness.log_event"):
        yield


@pytest.fixture(autouse=True)
def _retrieval_gate_always_retrieves():
    """run_with_harness_streamed giờ gọi should_retrieve() (retrieval_gate.py, 1 LLM call thật)
    TRƯỚC KHI vào Runner.run_streamed — patch mặc định trả (True, ...) cho MỌI test trong file này,
    tránh gọi model thật/tốn API mỗi lần chạy pytest VÀ tránh nhánh dataclasses.replace(agent,...)
    chạy nhầm trên agent=MagicMock() (không phải dataclass thật — bug có thật gặp khi thêm gate,
    xem wiki/log.md). Test riêng cho nhánh retrieve=False nằm trong test_retrieval_gate.py."""
    with patch(
        "demo_agents.weather_agent.harness.should_retrieve",
        new_callable=AsyncMock,
        return_value=(True, "test-default"),
    ):
        yield


@pytest.fixture(autouse=True)
def _scope_check_default_in_scope():
    """run_with_harness/run_with_harness_streamed giờ gọi classify_scope() (guardrails.py, 1 LLM
    call thật) TRƯỚC KHI vào Runner.run/run_streamed — patch mặc định trả in_scope cho MỌI test
    trong file này (tránh gọi model thật + tránh short-circuit/hint-injection nhầm ở các test không
    liên quan tới phạm vi). Test riêng cho out_of_scope/uncertain override patch này tại chỗ."""
    with patch(
        "demo_agents.weather_agent.harness.classify_scope",
        new_callable=AsyncMock,
        return_value=ScopeCheck(verdict="in_scope", reason="test-default"),
    ):
        yield


@dataclass
class _FakeAgent:
    """Đứng thay Agent thật (dataclass) cho các test cần dataclasses.replace() chạy thật (hint
    UNCERTAIN nối vào instructions) — MagicMock() không phải dataclass instance, replace() sẽ lỗi."""

    name: str = "Weather agent"
    instructions: str = "BASE INSTRUCTIONS"


def _run(coro):
    """run_with_harness() giờ là async def (chạy Runner.run thay vì Runner.run_sync — cần thiết để
    dùng chung event loop với MCP server đã connect, xem harness.py). Test hermetic không cần loop
    thật đang chạy MCP, chỉ cần asyncio.run() bọc ngoài để await được."""
    return asyncio.run(coro)


@patch("demo_agents.weather_agent.harness.asyncio.sleep", new_callable=AsyncMock)
@patch("demo_agents.weather_agent.harness.Runner.run", new_callable=AsyncMock)
def test_succeeds_first_try_no_retry(mock_run, mock_sleep):
    mock_run.return_value = "ok"
    result = _run(run_with_harness(agent=MagicMock(), question="q", session=MagicMock()))
    assert result == "ok"
    mock_run.assert_called_once()
    mock_sleep.assert_not_called()


@patch("demo_agents.weather_agent.harness.asyncio.sleep", new_callable=AsyncMock)
@patch("demo_agents.weather_agent.harness.Runner.run", new_callable=AsyncMock)
def test_retries_transient_error_then_succeeds(mock_run, mock_sleep):
    mock_run.side_effect = [ConnectionError("timeout"), "ok"]
    result = _run(run_with_harness(agent=MagicMock(), question="q", session=MagicMock()))
    assert result == "ok"
    assert mock_run.call_count == 2
    mock_sleep.assert_called_once()


@patch("demo_agents.weather_agent.harness.asyncio.sleep", new_callable=AsyncMock)
@patch("demo_agents.weather_agent.harness.Runner.run", new_callable=AsyncMock)
def test_exhausts_retries_raises_last_error(mock_run, mock_sleep):
    mock_run.side_effect = ConnectionError("timeout")
    with pytest.raises(ConnectionError):
        _run(run_with_harness(agent=MagicMock(), question="q", session=MagicMock(), max_retries=2))
    assert mock_run.call_count == 3


@patch("demo_agents.weather_agent.harness.asyncio.sleep", new_callable=AsyncMock)
@patch("demo_agents.weather_agent.harness.Runner.run", new_callable=AsyncMock)
def test_max_turns_exceeded_not_retried(mock_run, mock_sleep):
    mock_run.side_effect = MaxTurnsExceeded("too many turns")
    with pytest.raises(MaxTurnsExceeded):
        _run(run_with_harness(agent=MagicMock(), question="q", session=MagicMock()))
    mock_run.assert_called_once()
    mock_sleep.assert_not_called()


@patch("demo_agents.weather_agent.harness.asyncio.sleep", new_callable=AsyncMock)
@patch("demo_agents.weather_agent.harness.Runner.run", new_callable=AsyncMock)
def test_out_of_scope_returns_static_refusal_without_calling_model(mock_run, mock_sleep):
    """3-tier redesign: out_of_scope tự tin được quyết định TRƯỚC Runner.run (classify_scope thủ
    công), không còn dựa vào @input_guardrail's tripwire exception nữa — khác test cũ mock Runner.run
    raise InputGuardrailTripwireTriggered (bản cũ vẫn CHẠY model rồi mới trip; bản mới không gọi
    model chính luôn khi đã tự tin ngoài phạm vi)."""
    with patch(
        "demo_agents.weather_agent.harness.classify_scope",
        new_callable=AsyncMock,
        return_value=ScopeCheck(verdict="out_of_scope", reason="hỏi địa lý, không phải thời tiết"),
    ):
        result = _run(
            run_with_harness(agent=MagicMock(), question="Atlantis nằm ở đâu?", session=MagicMock())
        )
    assert result.final_output == OUT_OF_SCOPE_MESSAGE
    mock_run.assert_not_called()
    mock_sleep.assert_not_called()


@patch("demo_agents.weather_agent.harness.Runner.run", new_callable=AsyncMock)
def test_uncertain_scope_appends_hint_and_still_calls_model(mock_run):
    """Mức UNCERTAIN (mới) — KHÔNG chặn, chỉ nối hint vào instructions của 1 bản sao agent (agent
    gốc không đổi) rồi vẫn gọi model chính bình thường — đây là điểm khác biệt cốt lõi so với 2-tier
    cũ (trước đây model sẽ tự "sáng tác" chặn hoặc guardrail chặn cứng nhầm khi mơ hồ)."""
    mock_run.return_value = "ok"
    fake_agent = _FakeAgent()
    with patch(
        "demo_agents.weather_agent.harness.classify_scope",
        new_callable=AsyncMock,
        return_value=ScopeCheck(verdict="uncertain", reason="diễn đạt lạ"),
    ):
        result = _run(run_with_harness(agent=fake_agent, question="q", session=MagicMock()))
    assert result == "ok"
    called_agent = mock_run.call_args[0][0]
    assert called_agent is not fake_agent
    assert fake_agent.instructions == "BASE INSTRUCTIONS"  # agent gốc không bị đổi
    assert build_uncertain_hint("diễn đạt lạ") in called_agent.instructions


@pytest.mark.parametrize(
    "question", ["Chào bạn", "  hi  ", "Cảm ơn nhé", "Thanks!", "ok", "Xin chào"],
)
def test_is_greeting_only_matches_short_greetings(question):
    assert _is_greeting_only(question)


@pytest.mark.parametrize(
    "question",
    ["Chào bạn, thời tiết Hà Nội thế nào?", "Thời tiết Tokyo?", "Cảm ơn vì đã tra giúp mình thông tin"],
)
def test_is_greeting_only_does_not_match_real_questions(question):
    assert not _is_greeting_only(question)


@patch("demo_agents.weather_agent.harness.Runner.run", new_callable=AsyncMock)
def test_passes_max_turns_through(mock_run):
    mock_run.return_value = "ok"
    _run(run_with_harness(agent=MagicMock(), question="q", session=MagicMock(), max_turns=4))
    _, kwargs = mock_run.call_args
    assert kwargs["max_turns"] == 4


@pytest.mark.parametrize(
    "question",
    [
        "Bạn làm được gì?",
        "  bạn có thể GIÚP ĐƯỢC GÌ  ",
        "năng lực của bạn là gì",
        "what can you do",
        "help",
    ],
)
def test_is_capability_question_matches_known_phrasings(question):
    assert _is_capability_question(question)


@pytest.mark.parametrize("question", ["Thời tiết ở Hà Nội thế nào?", "Múi giờ ở Tokyo?", ""])
def test_is_capability_question_does_not_match_weather_questions(question):
    assert not _is_capability_question(question)


@patch("demo_agents.weather_agent.harness.Runner.run", new_callable=AsyncMock)
def test_capability_question_short_circuits_without_calling_model(mock_run):
    result = _run(run_with_harness(agent=MagicMock(), question="Bạn làm được gì?", session=MagicMock()))
    mock_run.assert_not_called()
    for keyword in _REQUIRED_KEYWORDS:
        assert keyword in result.final_output


@patch("demo_agents.weather_agent.harness.Runner.run", new_callable=AsyncMock)
def test_capability_report_names_all_tools_and_limitations(mock_run):
    result = _run(run_with_harness(agent=MagicMock(), question="what can you do", session=MagicMock()))
    text = result.final_output
    assert "get_weather" in text
    assert "get_city_note" in text
    assert "recall_last_city" in text
    assert "KHÔNG THỂ" in text


# ---- run_with_harness_streamed — bản stream dùng cho live chat (chatdemo.py), xem plan/wiki/log.md
# entry liên quan. Fake event shape khớp ĐÚNG những gì đã verify SỐNG bằng Runner.run_streamed()
# thật lúc build tính năng này (KHÔNG bịa shape) — event.item.raw_item.name cho tool_called,
# event.data.delta cho raw_response_event, result.final_output đọc được sau khi stream_events() xong.


class _FakeTextDelta:
    """Đứng thay cho openai.types.responses.ResponseTextDeltaEvent — patch thẳng tên trong module
    harness để test không phụ thuộc field bắt buộc thật của pydantic model đó (item_id, output_index...),
    chỉ cần đúng field `delta` mà harness.py thực sự đọc."""

    def __init__(self, delta):
        self.delta = delta


class _FakeToolCallItem:
    def __init__(self, name):
        self.raw_item = SimpleNamespace(name=name)


class _FakeRunItemEvent:
    type = "run_item_stream_event"

    def __init__(self, name, item):
        self.name = name
        self.item = item


class _FakeRawResponseEvent:
    type = "raw_response_event"

    def __init__(self, data):
        self.data = data


class _FakeStreamResult:
    def __init__(self, events, final_output=None, trip_after=None):
        self._events = events
        self.final_output = final_output
        self._trip_after = trip_after  # exception raise SAU khi phát hết `events` — mô phỏng đúng
        # thứ đã quan sát SỐNG: guardrail/max_turns có thể trip SAU KHI vài delta đã chảy ra.

    async def stream_events(self):
        for e in self._events:
            yield e
        if self._trip_after is not None:
            raise self._trip_after


def _run_gen(agen):
    async def _collect():
        return [item async for item in agen]

    return asyncio.run(_collect())


@patch("demo_agents.weather_agent.harness.ResponseTextDeltaEvent", _FakeTextDelta)
@patch("demo_agents.weather_agent.harness.Runner.run_streamed")
def test_streamed_yields_tool_start_text_delta_done_in_order(mock_run_streamed):
    events = [
        _FakeRunItemEvent("tool_called", _FakeToolCallItem("get_weather")),
        _FakeRawResponseEvent(_FakeTextDelta("Hi")),
        _FakeRawResponseEvent(_FakeTextDelta(" there")),
    ]
    mock_run_streamed.return_value = _FakeStreamResult(events, final_output="Hi there")
    results = _run_gen(
        run_with_harness_streamed(agent=MagicMock(), question="q", session=MagicMock())
    )
    assert results == [
        ("tool_start", "get_weather"),
        ("text_delta", "Hi"),
        ("text_delta", " there"),
        ("done", "Hi there"),
    ]


@patch("demo_agents.weather_agent.harness.ResponseTextDeltaEvent", _FakeTextDelta)
@patch("demo_agents.weather_agent.harness.Runner.run_streamed")
def test_streamed_ignores_non_tool_call_run_item_events(mock_run_streamed):
    """message_output_created/tool_output... (các run-item khác ngoài tool_called) không sinh
    event nào phía client — chỉ tool_called mới đáng hiện step indicator."""
    events = [_FakeRunItemEvent("message_output_created", SimpleNamespace(raw_item=None))]
    mock_run_streamed.return_value = _FakeStreamResult(events, final_output="ok")
    results = _run_gen(
        run_with_harness_streamed(agent=MagicMock(), question="q", session=MagicMock())
    )
    assert results == [("done", "ok")]


@patch("demo_agents.weather_agent.harness.ResponseTextDeltaEvent", _FakeTextDelta)
@patch("demo_agents.weather_agent.harness.Runner.run_streamed")
def test_streamed_guardrail_trip_mid_stream_overrides_with_static_refusal(mock_run_streamed):
    """Xác nhận SỐNG lúc build: guardrail chạy song song lượt gọi model đầu tiên nên text_delta có
    thể đã chảy ra TRƯỚC KHI biết trip — "done" cuối cùng vẫn PHẢI là OUT_OF_SCOPE_MESSAGE, ghi đè
    lên preview trước đó (client coi "done" là nguồn sự thật duy nhất)."""
    events = [_FakeRawResponseEvent(_FakeTextDelta("partial nonsense"))]
    mock_run_streamed.return_value = _FakeStreamResult(
        events, trip_after=InputGuardrailTripwireTriggered(MagicMock())
    )
    results = _run_gen(
        run_with_harness_streamed(agent=MagicMock(), question="off topic", session=MagicMock())
    )
    assert ("text_delta", "partial nonsense") in results
    assert results[-1] == ("done", OUT_OF_SCOPE_MESSAGE)


@patch("demo_agents.weather_agent.harness.ResponseTextDeltaEvent", _FakeTextDelta)
@patch("demo_agents.weather_agent.harness.Runner.run_streamed")
def test_streamed_out_of_scope_short_circuits_before_retrieval_gate_or_model(mock_run_streamed):
    """out_of_scope tự tin: chặn TRƯỚC CẢ retrieval gate — không tốn thêm lượt gọi nào ngoài chính
    classify_scope, khác hẳn hành vi cũ (guardrail chạy song song lượt gọi model đầu tiên)."""
    with patch(
        "demo_agents.weather_agent.harness.classify_scope",
        new_callable=AsyncMock,
        return_value=ScopeCheck(verdict="out_of_scope", reason="hỏi địa lý"),
    ), patch("demo_agents.weather_agent.harness.should_retrieve") as mock_gate:
        results = _run_gen(
            run_with_harness_streamed(agent=MagicMock(), question="Atlantis ở đâu?", session=MagicMock())
        )
        mock_gate.assert_not_called()
    mock_run_streamed.assert_not_called()
    assert results == [("done", OUT_OF_SCOPE_MESSAGE)]


@patch("demo_agents.weather_agent.harness.ResponseTextDeltaEvent", _FakeTextDelta)
@patch("demo_agents.weather_agent.harness.Runner.run_streamed")
def test_streamed_uncertain_scope_appends_hint_and_still_streams(mock_run_streamed):
    mock_run_streamed.return_value = _FakeStreamResult([], final_output="ok")
    fake_agent = _FakeAgent()
    with patch(
        "demo_agents.weather_agent.harness.classify_scope",
        new_callable=AsyncMock,
        return_value=ScopeCheck(verdict="uncertain", reason="diễn đạt lạ"),
    ):
        results = _run_gen(
            run_with_harness_streamed(agent=fake_agent, question="q", session=MagicMock())
        )
    assert results == [("done", "ok")]
    called_agent = mock_run_streamed.call_args[0][0]
    assert called_agent is not fake_agent
    assert build_uncertain_hint("diễn đạt lạ") in called_agent.instructions


@patch("demo_agents.weather_agent.harness.Runner.run_streamed")
def test_streamed_max_turns_exceeded_reraises_not_swallowed(mock_run_streamed):
    mock_run_streamed.return_value = _FakeStreamResult([], trip_after=MaxTurnsExceeded("too many"))
    with pytest.raises(MaxTurnsExceeded):
        _run_gen(run_with_harness_streamed(agent=MagicMock(), question="q", session=MagicMock()))


def test_streamed_capability_question_short_circuits_single_done_event():
    results = _run_gen(
        run_with_harness_streamed(agent=MagicMock(), question="Bạn làm được gì?", session=MagicMock())
    )
    assert len(results) == 1
    assert results[0][0] == "done"
    for keyword in _REQUIRED_KEYWORDS:
        assert keyword in results[0][1]


def test_streamed_greeting_short_circuits_before_retrieval_gate_or_model():
    """Fast-path RẺ NHẤT (WS7) — không được gọi should_retrieve/Runner.run_streamed cho câu chào
    thuần, khác câu hỏi thật (đã test ở các case khác trong file này, luôn gọi gate trước)."""
    with patch("demo_agents.weather_agent.harness.should_retrieve") as mock_gate:
        results = _run_gen(
            run_with_harness_streamed(agent=MagicMock(), question="Cảm ơn nhé!", session=MagicMock())
        )
        mock_gate.assert_not_called()
    assert results == [("done", _GREETING_REPLY)]
