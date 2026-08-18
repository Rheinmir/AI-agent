"""Agent Spec — mô tả agent theo CẤU TRÚC TRUNG LẬP, không phụ thuộc framework nào, để "định nghĩa
1 lần, xuất ra nhiều cấu trúc" thay vì viết lại toàn bộ agent mỗi khi đổi/thử framework khác. Trả
lời trực tiếp yêu cầu "bộ converter để chuyển đổi linh hoạt giữa các cấu trúc".

KHÔNG phải converter đọc-ngược 2 chiều từ code LangChain/LangGraph thật (bài toán đó lớn hơn hẳn —
mỗi framework có mô hình khác nhau: LangGraph là graph/state-machine, LangChain là Chain/
AgentExecutor, Agents SDK là Agent+Runner+Tool, Claude Agent SDK dùng @tool decorator riêng, Azure
AI Agent Service/Semantic Kernel dùng KernelFunction — không có 1 cấu trúc trung gian nào biểu diễn
được ĐẦY ĐỦ mọi khái niệm của mọi framework). Cách tiếp cận đã chọn (xác nhận qua AskUserQuestion):
định nghĩa 1 spec trung lập TỐI THIỂU (đủ cho tool-calling agent: tên, instructions, tools,
guardrail input), rồi viết exporter mỏng cho từng đích — `exporters/openai_agents_exporter.py`
CHẠY THẬT (SDK đang dùng), 4 exporter còn lại là STUB có sơ đồ ánh xạ rõ ràng, điền code thật khi
nào project thực sự cần chạy trên framework đó.

Spec ở đây KHÔNG định nghĩa lại logic — nó THAM CHIẾU trực tiếp các FunctionTool đã dựng sẵn trong
agent.py (qua @function_tool, đã có name/description/params_json_schema tự sinh) và
weather_scope_guardrail đã có trong guardrails.py — một nguồn sự thật duy nhất, không có 2 chỗ định
nghĩa "chức năng của tool X" dễ lệch nhau theo thời gian.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class ToolSpec:
    name: str
    description: str
    params_json_schema: dict
    func: Callable
    """Hàm python THUẦN đứng sau tool — không có gì thuộc riêng 1 framework (không nhận
    ToolContext, không trả FunctionTool...) — đây là phần thật sự "chuyển đổi được" qua framework
    khác, vì logic nghiệp vụ độc lập với cách 1 framework cụ thể gọi tool."""


@dataclass
class GuardrailSpec:
    name: str
    kind: str  # "input" | "output"
    description: str
    guardrail: Any
    """Object guardrail gốc (vd InputGuardrail của Agents SDK) — exporter của từng framework tự
    biết cách map object này sang cấu trúc guardrail/validator riêng của framework đó."""


@dataclass
class AgentSpec:
    name: str
    instructions: str
    tools: list = field(default_factory=list)
    guardrails: list = field(default_factory=list)
    hooks: Optional[Any] = None
    accent_color: Optional[str] = None
    """Màu thương hiệu của agent — quy ước: màu CÔNG NGHỆ XƯƠNG SỐNG của domain agent theo, không
    dùng chung 1 màu mặc định cho mọi agent (xem devops_agent/agent_spec.py — dùng Kubernetes blue
    thay vì copy màu này). Optional; converter fallback về màu trung tính nếu None."""
    mcp_tool_names: list = field(default_factory=list)
    """Tên các module trong mcp_tools/ mà agent này cần — xem devops_agent/agent_spec.py cho giải
    thích đầy đủ (converter dùng field này để bundle mcp_tools/ + sinh standalone_server.py tự
    connect MCP)."""


def build_weather_agent_spec():
    """Dựng AgentSpec từ CHÍNH các object thật đã có trong agent.py/guardrails.py/monitoring.py —
    import trễ (bên trong hàm) để tránh vòng lặp import (agent.py sẽ import agent_spec.py ở các
    bước sau khi cần dùng exporter, agent_spec.py lại cần đọc object từ agent.py)."""
    from demo_agents.weather_agent import agent as agent_module
    from demo_agents.weather_agent.guardrails import weather_scope_guardrail, OUT_OF_SCOPE_MESSAGE
    from demo_agents.weather_agent.monitoring import WeatherAgentHooks

    def _tool_spec(function_tool, plain_func):
        return ToolSpec(
            name=function_tool.name,
            description=function_tool.description,
            params_json_schema=function_tool.params_json_schema,
            func=plain_func,
        )

    return AgentSpec(
        name=agent_module.weather_agent.name,
        # Spec xuất ra LUÔN gồm addendum MCP — khớp hành vi mặc định của chatdemo.py/run.py (xem
        # devops_agent/agent_spec.py cho lý do đầy đủ).
        instructions=agent_module.INSTRUCTIONS + agent_module._MCP_INSTRUCTIONS_ADDENDUM,
        tools=[
            _tool_spec(agent_module.get_weather, agent_module._get_weather_impl),
            _tool_spec(agent_module.get_city_note, agent_module.lookup_city_note),
            _tool_spec(agent_module.recall_last_city, agent_module._recall_last_city),
        ],
        guardrails=[
            GuardrailSpec(
                name=weather_scope_guardrail.get_name(),
                kind="input",
                description=(
                    "Chặn câu hỏi ngoài phạm vi thời tiết — trả OUT_OF_SCOPE_MESSAGE cố định "
                    f"({OUT_OF_SCOPE_MESSAGE[:40]}...) thay vì để model tự diễn giải."
                ),
                guardrail=weather_scope_guardrail,
            )
        ],
        hooks=WeatherAgentHooks,
        accent_color="#10a37f",  # màu đã khoá trong web/design.md (ChatGPT-style vibe), không map
        # theo hãng/công nghệ backbone cụ thể nào — Open-Meteo (API dùng) không có brand color rõ.
        mcp_tool_names=["fetch_server", "exa_server"],
    )
