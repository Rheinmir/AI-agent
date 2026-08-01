import argparse
import os
import sys

from agents import Runner

from demo_agents.weather_agent.agent import weather_agent


def main() -> int:
    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "Lỗi: thiếu OPENAI_API_KEY trong biến môi trường.\n"
            "Xem demo_agents/weather_agent/.env.example — export OPENAI_API_KEY=<key-của-bạn> "
            "trước khi chạy live.",
            file=sys.stderr,
        )
        return 1

    parser = argparse.ArgumentParser(
        description="Chạy weather agent (demo Model+Tools+Instructions)."
    )
    parser.add_argument("question", help='Ví dụ: "Thời tiết ở Hà Nội thế nào?"')
    args = parser.parse_args()

    result = Runner.run_sync(weather_agent, args.question)
    print(result.final_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
