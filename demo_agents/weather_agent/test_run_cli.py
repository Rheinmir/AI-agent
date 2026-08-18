import os
import subprocess
import sys


def test_missing_api_key_exits_nonzero_with_clear_message(tmp_path):
    # WEATHER_AGENT_ENV_FILE trỏ tới file không tồn tại — cô lập test khỏi .env thật của máy dev
    # (nếu có), để test luôn hermetic bất kể máy chạy đã cấu hình key thật hay chưa.
    env = {k: v for k, v in os.environ.items() if k not in ("OPENAI_API_KEY", "DEEPSEEK_API_KEY")}
    env["WEATHER_AGENT_ENV_FILE"] = str(tmp_path / "nonexistent.env")
    result = subprocess.run(
        [sys.executable, "-m", "demo_agents.weather_agent.run", "Thời tiết ở Hà Nội thế nào?"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "API_KEY" in result.stderr
