"""Cấu hình MCP server DÙNG CHUNG cho mọi agent trong demo_agents/ — 1 nguồn sự thật duy nhất, không
duplicate cấu hình `MCPServerStdio` riêng cho từng agent. Xem README.md ở thư mục này cho lý do chọn
mcp-server-fetch (không phải agent-reach) và các bug thật gặp lúc build.

YÊU CẦU Python 3.10+ (thư viện `mcp` client — import trong agents.mcp.server — pin
requires-python>=3.10 ở MỌI phiên bản trên PyPI, không có ngoại lệ)."""

from pathlib import Path

_SERVERS_VENV_BIN = Path(__file__).parent / "servers-venv" / "bin"
FETCH_SERVER_BIN = _SERVERS_VENV_BIN / "mcp-server-fetch"


def fetch_server_available() -> bool:
    """True nếu mcp-server-fetch đã cài trong servers-venv/ — dùng để agent tự kiểm tra trước khi
    thử kết nối, tránh lỗi mơ hồ nếu ai đó chưa chạy bước setup trong README.md."""
    return FETCH_SERVER_BIN.is_file()


def build_fetch_mcp_server(name: str = "fetch"):
    """Dựng 1 MCPServerStdio TRỎ TỚI mcp-server-fetch — chưa connect (caller phải `async with` hoặc
    dùng qua `agents.mcp.MCPServerManager`, xem cách dùng trong run.py/chatdemo.py của từng agent).
    Import trễ (bên trong hàm) vì agents.mcp.server cần Python 3.10+ — agent nào vẫn muốn giữ khả
    năng chạy được trên máy chỉ có 3.9 (không có MCP) thì không nên import module này ở top-level.
    """
    from agents.mcp.server import MCPServerStdio

    return MCPServerStdio(
        name=name,
        params={"command": str(FETCH_SERVER_BIN), "args": []},
    )


# Tên hàm CHUNG mọi module mcp_tools/*.py đều phải có — monolith_agent_deploy_converter.py gọi
# ĐÚNG tên này (không phải build_fetch_mcp_server) để bundle nhiều loại MCP server khác nhau (mỗi
# module 1 tên hàm riêng, khó đoán) qua CÙNG 1 đường code trong standalone_server.py sinh ra.
build_mcp_server = build_fetch_mcp_server
