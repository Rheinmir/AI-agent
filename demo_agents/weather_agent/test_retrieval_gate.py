import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from demo_agents.weather_agent.retrieval_gate import should_retrieve


def _run(coro):
    return asyncio.run(coro)


@patch("demo_agents.weather_agent.retrieval_gate.Runner.run", new_callable=AsyncMock)
def test_parses_true_decision(mock_run):
    mock_run.return_value = MagicMock(final_output='{"retrieve": true, "reason": "hỏi múi giờ Tokyo"}')
    retrieve, reason = _run(should_retrieve("Múi giờ Tokyo là gì?"))
    assert retrieve is True
    assert reason == "hỏi múi giờ Tokyo"


@patch("demo_agents.weather_agent.retrieval_gate.Runner.run", new_callable=AsyncMock)
def test_parses_false_decision(mock_run):
    mock_run.return_value = MagicMock(final_output='{"retrieve": false, "reason": "chỉ chào hỏi"}')
    retrieve, reason = _run(should_retrieve("Cảm ơn bạn nhé!"))
    assert retrieve is False
    assert reason == "chỉ chào hỏi"


@patch("demo_agents.weather_agent.retrieval_gate.Runner.run", new_callable=AsyncMock)
def test_fails_open_on_malformed_json(mock_run):
    mock_run.return_value = MagicMock(final_output="not json at all")
    retrieve, reason = _run(should_retrieve("bất kỳ câu gì"))
    assert retrieve is True
    assert "fail-open" in reason


@patch("demo_agents.weather_agent.retrieval_gate.Runner.run", new_callable=AsyncMock)
def test_fails_open_on_model_error(mock_run):
    mock_run.side_effect = ConnectionError("network down")
    retrieve, reason = _run(should_retrieve("bất kỳ câu gì"))
    assert retrieve is True
    assert "fail-open" in reason


@patch("demo_agents.weather_agent.retrieval_gate.Runner.run", new_callable=AsyncMock)
def test_missing_retrieve_key_defaults_true(mock_run):
    """JSON hợp lệ nhưng THIẾU key 'retrieve' — fail-open theo hướng AN TOÀN (vẫn tra cứu) thay vì
    coi thiếu key = False (im lặng bỏ sót data)."""
    mock_run.return_value = MagicMock(final_output='{"reason": "không rõ"}')
    retrieve, _ = _run(should_retrieve("một câu hỏi"))
    assert retrieve is True
