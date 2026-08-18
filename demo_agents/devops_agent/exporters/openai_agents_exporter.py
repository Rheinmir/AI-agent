"""Exporter THẬT — copy nguyên từ demo_agents/weather_agent/exporters/openai_agents_exporter.py
(module hoàn toàn generic — nhận AgentSpec bất kỳ, không có gì riêng cho weather_agent). Dựng lại 1
`agents.Agent` chạy được từ `AgentSpec` trung lập — dùng bởi monolith_agent_deploy_converter.py.
"""

import json

from agents import Agent, FunctionTool


def _wrap_tool(tool_spec):
    async def on_invoke_tool(ctx, args_json):
        args = json.loads(args_json) if args_json else {}
        return tool_spec.func(**args)

    return FunctionTool(
        name=tool_spec.name,
        description=tool_spec.description,
        params_json_schema=tool_spec.params_json_schema,
        on_invoke_tool=on_invoke_tool,
    )


def build_openai_agent(spec, model=None, mcp_servers=None):
    """Dựng `agents.Agent` thật từ AgentSpec. `model` truyền tay (không tự gọi get_model()) — export
    không nên tự ý quyết định provider, để caller chọn. `mcp_servers` (list server MCP ĐÃ CONNECT) —
    optional, dùng bởi monolith_agent_deploy_converter.py khi spec.mcp_tool_names không rỗng."""
    return Agent(
        name=spec.name,
        model=model,
        instructions=spec.instructions,
        tools=[_wrap_tool(t) for t in spec.tools],
        input_guardrails=[g.guardrail for g in spec.guardrails if g.kind == "input"],
        hooks=spec.hooks() if spec.hooks else None,
        mcp_servers=list(mcp_servers) if mcp_servers else [],
    )
