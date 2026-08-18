"""Test cho build_agent_with_mcp() — hermetic, KHÔNG spawn MCP server thật (dùng object giả có
thuộc tính .name để đứng vào mcp_servers=[...]). Verify SỐNG thật (spawn mcp-server-fetch thật, gọi
Runner.run thật) đã làm tay lúc build — xem wiki/log.md "wire-mcp-fetch-into-agents" — không lặp lại
ở đây vì cần servers-venv/ cài sẵn (máy CI không có), không hermetic được."""

from demo_agents.devops_agent.agent import (
    INSTRUCTIONS,
    _MCP_INSTRUCTIONS_ADDENDUM,
    build_agent_with_mcp,
    devops_agent,
)


class _FakeMCPServer:
    name = "fake-fetch"


def test_base_agent_has_no_mcp_servers():
    """devops_agent gốc KHÔNG được tự ý gắn mcp_servers — chỉ build_agent_with_mcp() mới thêm,
    tránh agent tự nhận vơ khả năng fetch khi không ai gắn server thật."""
    assert devops_agent.mcp_servers == []


def test_base_agent_instructions_do_not_mention_fetch():
    assert "fetch" not in INSTRUCTIONS.lower()


def test_build_agent_with_mcp_attaches_servers():
    fake = _FakeMCPServer()
    augmented = build_agent_with_mcp([fake])
    assert augmented.mcp_servers == [fake]


def test_build_agent_with_mcp_does_not_mutate_base_agent():
    build_agent_with_mcp([_FakeMCPServer()])
    assert devops_agent.mcp_servers == []


def test_build_agent_with_mcp_extends_instructions_not_replaces():
    augmented = build_agent_with_mcp([_FakeMCPServer()])
    assert augmented.instructions == INSTRUCTIONS + _MCP_INSTRUCTIONS_ADDENDUM
    assert augmented.instructions.startswith(INSTRUCTIONS)


def test_build_agent_with_mcp_keeps_same_tools_and_guardrails():
    augmented = build_agent_with_mcp([_FakeMCPServer()])
    assert augmented.tools == devops_agent.tools
    assert augmented.input_guardrails == devops_agent.input_guardrails
    assert augmented.model == devops_agent.model
