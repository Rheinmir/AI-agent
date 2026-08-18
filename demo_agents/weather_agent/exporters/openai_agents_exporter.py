"""Exporter THẬT — dựng lại 1 `agents.Agent` chạy được từ `AgentSpec` trung lập. Chứng minh
round-trip: spec lấy dữ liệu TỪ agent.py, exporter này dựng NGƯỢC LẠI 1 Agent tương đương — nếu
2 chiều khớp nhau (cùng tên tool, cùng guardrail), spec đủ trung thực để dùng làm nguồn cho exporter
framework khác.
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
    không nên tự ý quyết định provider, để caller chọn (hoặc dùng agent thật đã có trong agent.py
    thay vì gọi hàm này trong sản phẩm — hàm này phục vụ chứng minh khả năng chuyển đổi, không thay
    thế `agent.py::weather_agent`). `mcp_servers` (list server MCP ĐÃ CONNECT, xem
    agents.mcp.MCPServerManager) — optional, dùng bởi monolith_agent_deploy_converter.py khi
    spec.mcp_tool_names không rỗng; None/rỗng thì agent dựng ra không có MCP, hành vi y hệt trước
    khi thêm tham số này (tương thích ngược)."""
    return Agent(
        name=spec.name,
        model=model,
        instructions=spec.instructions,
        tools=[_wrap_tool(t) for t in spec.tools],
        input_guardrails=[g.guardrail for g in spec.guardrails if g.kind == "input"],
        hooks=spec.hooks() if spec.hooks else None,
        mcp_servers=list(mcp_servers) if mcp_servers else [],
    )
