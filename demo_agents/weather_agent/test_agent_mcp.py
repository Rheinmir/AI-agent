"""Test cho build_agent_with_mcp() — hermetic, KHÔNG spawn MCP server thật. Cùng convention với
demo_agents/devops_agent/test_agent_mcp.py. Verify SỐNG thật đã làm tay lúc build — xem
wiki/log.md "wire-mcp-fetch-into-agents"."""

from demo_agents.weather_agent.agent import (
    INSTRUCTIONS,
    _MCP_INSTRUCTIONS_ADDENDUM,
    build_agent_with_mcp,
    weather_agent,
)


class _FakeMCPServer:
    name = "fake-fetch"


def test_base_agent_has_no_mcp_servers():
    assert weather_agent.mcp_servers == []


def test_base_agent_instructions_do_not_mention_fetch():
    assert "fetch" not in INSTRUCTIONS.lower()


def test_build_agent_with_mcp_attaches_servers():
    fake = _FakeMCPServer()
    augmented = build_agent_with_mcp([fake])
    assert augmented.mcp_servers == [fake]


def test_build_agent_with_mcp_does_not_mutate_base_agent():
    build_agent_with_mcp([_FakeMCPServer()])
    assert weather_agent.mcp_servers == []


def test_build_agent_with_mcp_extends_instructions_not_replaces():
    augmented = build_agent_with_mcp([_FakeMCPServer()])
    assert augmented.instructions == INSTRUCTIONS + _MCP_INSTRUCTIONS_ADDENDUM
    assert augmented.instructions.startswith(INSTRUCTIONS)


def test_build_agent_with_mcp_keeps_same_tools_guardrails_hooks():
    augmented = build_agent_with_mcp([_FakeMCPServer()])
    assert augmented.tools == weather_agent.tools
    assert augmented.input_guardrails == weather_agent.input_guardrails
    assert augmented.hooks == weather_agent.hooks
    assert augmented.model == weather_agent.model
