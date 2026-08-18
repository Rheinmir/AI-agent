import asyncio
from unittest.mock import MagicMock, patch

import pytest

from demo_agents.weather_agent.agent_spec import build_weather_agent_spec
from demo_agents.weather_agent.exporters.openai_agents_exporter import build_openai_agent


def test_spec_reflects_real_agent_tools_and_guardrails():
    spec = build_weather_agent_spec()
    assert spec.name == "Weather agent"
    assert {t.name for t in spec.tools} == {"get_weather", "get_city_note", "recall_last_city"}
    assert len(spec.guardrails) == 1
    assert spec.guardrails[0].kind == "input"
    assert spec.guardrails[0].name == "weather_scope_guardrail"


def test_spec_tools_carry_real_json_schema():
    spec = build_weather_agent_spec()
    weather_tool = next(t for t in spec.tools if t.name == "get_weather")
    assert "city" in weather_tool.params_json_schema.get("properties", {})


def test_openai_exporter_rebuilds_agent_with_same_tools_and_guardrails():
    spec = build_weather_agent_spec()
    rebuilt = build_openai_agent(spec, model="fake-model")
    assert rebuilt.name == spec.name
    assert {t.name for t in rebuilt.tools} == {t.name for t in spec.tools}
    assert len(rebuilt.input_guardrails) == 1
    assert rebuilt.hooks is not None


@patch("demo_agents.weather_agent.agent._remember_last_city")
@patch("demo_agents.weather_agent.agent._fetch_current")
@patch("demo_agents.weather_agent.agent._geocode")
def test_rebuilt_tool_invokes_same_underlying_logic(mock_geocode, mock_fetch, mock_remember):
    mock_geocode.return_value = {"name": "Hà Nội", "lat": 21.03, "lon": 105.85}
    mock_fetch.return_value = {"temp_c": 29.0, "code": 3}
    spec = build_weather_agent_spec()
    rebuilt = build_openai_agent(spec, model="fake-model")
    weather_tool = next(t for t in rebuilt.tools if t.name == "get_weather")
    result = asyncio.run(weather_tool.on_invoke_tool(MagicMock(), '{"city": "Hà Nội"}'))
    assert result == "Hà Nội: 29.0°C, Nhiều mây"


def test_stub_exporters_fail_loudly_not_silently():
    from demo_agents.weather_agent.exporters import (
        azure_ai_exporter,
        claude_agent_sdk_exporter,
        langchain_exporter,
        langgraph_exporter,
    )

    spec = build_weather_agent_spec()
    for exporter, build_fn_name in [
        (langchain_exporter, "build_langchain_agent"),
        (langgraph_exporter, "build_langgraph_agent"),
        (claude_agent_sdk_exporter, "build_claude_agent"),
        (azure_ai_exporter, "build_azure_agent"),
    ]:
        build_fn = getattr(exporter, build_fn_name)
        with pytest.raises(NotImplementedError):
            build_fn(spec)
