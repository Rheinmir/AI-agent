"""Agent Spec — mô tả devops_agent theo cấu trúc trung lập, cùng convention với
demo_agents/weather_agent/agent_spec.py (xem wiki/concepts/agent-portability.md). Lý do thêm file
này dù devops_agent đang scope tối thiểu ("hỏi đáp thuần"): để tái dùng
harness/scripts/monolith_agent_deploy_converter.py — cách nhanh nhất có sẵn để có 1 chat web UI test
được, thay vì viết riêng 1 chatdemo.py mới.

Spec KHÔNG định nghĩa lại logic — tham chiếu trực tiếp FunctionTool đã dựng sẵn trong agent.py (qua
@function_tool) và devops_scope_guardrail đã có trong guardrails.py.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class ToolSpec:
    name: str
    description: str
    params_json_schema: dict
    func: Callable


@dataclass
class GuardrailSpec:
    name: str
    kind: str  # "input" | "output"
    description: str
    guardrail: Any


@dataclass
class AgentSpec:
    name: str
    instructions: str
    tools: list = field(default_factory=list)
    guardrails: list = field(default_factory=list)
    hooks: Optional[Any] = None
    accent_color: Optional[str] = None
    """Màu thương hiệu của agent — mặc định lấy màu CÔNG NGHỆ XƯƠNG SỐNG của domain agent theo
    (vd Kubernetes blue #326CE5 cho devops_agent, vì phần lớn cheatsheet xoay quanh K8s), KHÔNG
    dùng chung 1 màu mặc định cho mọi agent. Optional vì không phải agent nào cũng cần khai báo —
    exporter/converter fallback về màu trung tính nếu None (xem
    harness/scripts/monolith_agent_deploy_converter.py § _GENERIC_CHAT_HTML)."""
    mcp_tool_names: list = field(default_factory=list)
    """Tên các module trong mcp_tools/ (vd "fetch_server") mà agent này cần — converter đọc field
    này để (1) bundle mcp_tools/ (trừ servers-venv/, machine-specific) vào standalone export, (2)
    sinh standalone_server.py tự connect MCP qua agents.mcp.MCPServerManager. Rỗng = agent không
    dùng MCP, converter bỏ qua bước này (không phải mọi agent cần)."""


def build_devops_agent_spec():
    """Dựng AgentSpec từ CHÍNH các object thật đã có trong agent.py/guardrails.py — import trễ để
    tránh vòng lặp import."""
    from demo_agents.devops_agent import agent as agent_module
    from demo_agents.devops_agent.guardrails import devops_scope_guardrail, OUT_OF_SCOPE_MESSAGE

    def _tool_spec(function_tool, plain_func):
        return ToolSpec(
            name=function_tool.name,
            description=function_tool.description,
            params_json_schema=function_tool.params_json_schema,
            func=plain_func,
        )

    return AgentSpec(
        name=agent_module.devops_agent.name,
        # Spec xuất ra LUÔN gồm addendum MCP — bundle standalone sẽ tự connect fetch tool (nếu bundle
        # đó chạy được servers-venv/, xem mcp_tools/README.md), khớp đúng hành vi mặc định của
        # chatdemo.py/run.py (không phải 2 hành vi khác nhau giữa "chạy tại chỗ" và "đóng gói").
        instructions=agent_module.INSTRUCTIONS + agent_module._MCP_INSTRUCTIONS_ADDENDUM,
        # tools rỗng CHỦ Ý — TOOL DUY NHẤT đọc wiki của agent này (ask_librarian) gọi sang 1 PROCESS
        # RIÊNG qua socket (librarian_agent/), không phải hàm Python thuần độc lập export được như
        # get_cheatsheet trước đây — converter/standalone export chưa có cách bundle 1 process khác
        # kèm theo (khác get_weather/get_city_note của weather_agent, gọi API HTTP không cần process
        # nội bộ nào). Export lại khi converter hỗ trợ bundle multi-process.
        tools=[],
        guardrails=[
            GuardrailSpec(
                name=devops_scope_guardrail.get_name(),
                kind="input",
                description=(
                    "Chặn câu hỏi ngoài phạm vi DevOps hoặc yêu cầu thực thi hành động trên hệ "
                    f"thống thật — trả OUT_OF_SCOPE_MESSAGE cố định ({OUT_OF_SCOPE_MESSAGE[:40]}...)."
                ),
                guardrail=devops_scope_guardrail,
            )
        ],
        hooks=None,
        accent_color="#326CE5",  # Kubernetes blue — công nghệ xương sống của cheatsheet hiện có
        mcp_tool_names=["fetch_server", "exa_server"],
    )
