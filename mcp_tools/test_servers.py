"""Test hermetic cho fetch_server.py/exa_server.py — chỉ verify cấu hình dựng đúng, KHÔNG spawn
process/connect mạng thật (đã verify sống lúc build, xem wiki/log.md). Không cần servers-venv/ cài
sẵn để chạy test này (chỉ test construction, không test connect())."""

from mcp_tools.exa_server import build_exa_mcp_server
from mcp_tools.exa_server import build_mcp_server as exa_build_mcp_server
from mcp_tools.fetch_server import FETCH_SERVER_BIN, build_fetch_mcp_server
from mcp_tools.fetch_server import build_mcp_server as fetch_build_mcp_server


def test_fetch_server_has_generic_alias_for_converter():
    """monolith_agent_deploy_converter.py gọi build_mcp_server() (tên chung), không phải
    build_fetch_mcp_server() — bug thật sẽ xảy ra nếu 2 hàm này lệch nhau."""
    assert fetch_build_mcp_server is build_fetch_mcp_server


def test_exa_server_has_generic_alias_for_converter():
    assert exa_build_mcp_server is build_exa_mcp_server


def test_fetch_server_points_at_servers_venv_binary():
    server = build_fetch_mcp_server()
    assert server.params.command == str(FETCH_SERVER_BIN)
    assert "servers-venv" in str(FETCH_SERVER_BIN)


def test_exa_server_points_at_remote_mcp_endpoint():
    server = build_exa_mcp_server()
    assert server.params["url"] == "https://mcp.exa.ai/mcp"


def test_fetch_server_and_exa_server_have_distinct_default_names():
    assert build_fetch_mcp_server().name == "fetch"
    assert build_exa_mcp_server().name == "exa"
