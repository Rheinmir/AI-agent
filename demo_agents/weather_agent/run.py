import argparse
import asyncio
import sys

from agents import Runner
from agents.mcp import MCPServerManager

from demo_agents.weather_agent.agent import build_agent_with_mcp, weather_agent
from demo_agents.weather_agent.model_provider import has_any_key


async def _run_async(question: str) -> str:
    """Cùng pattern với demo_agents/devops_agent/run.py — MCPServerManager tự loại server không
    connect được (drop_failed_servers=True mặc định), agent vẫn chạy nếu mcp-server-fetch/Exa chưa
    connect được."""
    from mcp_tools.exa_server import build_exa_mcp_server
    from mcp_tools.fetch_server import build_fetch_mcp_server

    servers = [build_fetch_mcp_server(), build_exa_mcp_server()]
    async with MCPServerManager(servers) as manager:
        agent = build_agent_with_mcp(manager.active_servers) if manager.active_servers else weather_agent
        result = await Runner.run(agent, question)
        return result.final_output


def main() -> int:
    if not has_any_key():
        print(
            "Lỗi: thiếu DEEPSEEK_API_KEY hoặc OPENAI_API_KEY.\n"
            "Xem demo_agents/weather_agent/.env.example — điền một trong hai key vào "
            "demo_agents/weather_agent/.env (file này bị .gitignore, không commit) trước khi chạy live.",
            file=sys.stderr,
        )
        return 1

    parser = argparse.ArgumentParser(
        description="Chạy weather agent (demo Model+Tools+Instructions, + đọc trang web qua MCP fetch)."
    )
    parser.add_argument("question", help='Ví dụ: "Thời tiết ở Hà Nội thế nào?"')
    args = parser.parse_args()

    print(asyncio.run(_run_async(args.question)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
