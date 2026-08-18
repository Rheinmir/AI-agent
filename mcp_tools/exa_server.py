"""Exa search — MCP server THẬT, REMOTE (HTTP, không phải subprocess local như fetch_server.py),
trả lời đúng câu hỏi "sao không tự search được?" — mcp-server-fetch (fetch_server.py) chỉ đọc 1 URL
CỤ THỂ, không tìm kiếm. Exa MCP (`https://mcp.exa.ai/mcp`) expose 2 tool: `web_search_exa` (tìm
kiếm ngữ nghĩa, trả kết quả thật) + `web_fetch_exa` (đọc nội dung 1/nhiều URL, tương tự fetch_server
nhưng có thể batch nhiều URL 1 lần).

MIỄN PHÍ, KHÔNG CẦN API KEY — verify sống qua `mcporter call exa.web_search_exa query="..."` trước
khi wire vào agent (xem README.md). Cấu hình 1 lần qua `mcporter config add exa
https://mcp.exa.ai/mcp` (đã làm — lưu ở `~/.mcporter/mcporter.json`, máy-cục-bộ, không phải thứ cần
bundle theo agent vì bản thân kết nối trực tiếp URL, không qua mcporter runtime khi dùng qua
agents.mcp.MCPServerStreamableHttp).

YÊU CẦU Python 3.10+ (cùng lý do với fetch_server.py — thư viện `mcp` client)."""


def build_exa_mcp_server(name: str = "exa"):
    """Dựng 1 MCPServerStreamableHttp trỏ tới Exa MCP remote — chưa connect (caller `async with`
    hoặc dùng qua agents.mcp.MCPServerManager, xem cách dùng trong run.py/chatdemo.py của từng
    agent). Import trễ vì agents.mcp cần Python 3.10+."""
    from agents.mcp.server import MCPServerStreamableHttp

    return MCPServerStreamableHttp(name=name, params={"url": "https://mcp.exa.ai/mcp"})


# Tên hàm CHUNG mọi module mcp_tools/*.py đều phải có — xem fetch_server.py::build_mcp_server.
build_mcp_server = build_exa_mcp_server
