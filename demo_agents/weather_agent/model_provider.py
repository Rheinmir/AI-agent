"""Chọn model provider theo API key có sẵn — DeepSeek (endpoint OpenAI-compatible) ưu tiên khi
có DEEPSEEK_API_KEY, mặc định gpt-4o-mini khi có OPENAI_API_KEY. Không hardcode một provider duy
nhất vì sandbox phát triển chỉ có DEEPSEEK_API_KEY để test, còn người dùng cuối có thể dùng
OPENAI_API_KEY thật.

`WEATHER_AGENT_ENV_FILE` cho phép trỏ tới một .env khác (hoặc file không tồn tại) — dùng trong
test để cô lập khỏi .env thật của máy dev, không liên quan tới hành vi chạy live bình thường.
"""
import os
from pathlib import Path

_DEFAULT_ENV_PATH = Path(__file__).parent / ".env"


def _env_path() -> Path:
    override = os.environ.get("WEATHER_AGENT_ENV_FILE")
    return Path(override) if override else _DEFAULT_ENV_PATH


def _load_dotenv() -> None:
    path = _env_path()
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def has_any_key() -> bool:
    _load_dotenv()
    return bool(os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY"))


def get_model():
    """Trả về model cho Agent(model=...), hoặc None nếu không có key nào (caller tự báo lỗi)."""
    _load_dotenv()
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    if deepseek_key:
        from agents import AsyncOpenAI, OpenAIChatCompletionsModel

        client = AsyncOpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")
        return OpenAIChatCompletionsModel(model="deepseek-chat", openai_client=client)
    if os.environ.get("OPENAI_API_KEY"):
        return "gpt-4o-mini"
    return None
