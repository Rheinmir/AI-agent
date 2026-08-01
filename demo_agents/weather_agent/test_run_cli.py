import os
import subprocess
import sys


def test_missing_api_key_exits_nonzero_with_clear_message():
    env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
    result = subprocess.run(
        [sys.executable, "-m", "demo_agents.weather_agent.run", "Thời tiết ở Hà Nội thế nào?"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "OPENAI_API_KEY" in result.stderr
