# Weather agent — MVP đầu tiên

Minh hoạ 3 yếu tố nền tảng của một agent (xem `llmwiki/wiki/concepts/agent.md`):

| Yếu tố | Ở đâu trong code |
|---|---|
| Model | `agent.py` — `model="gpt-4o-mini"` |
| Tools | `agent.py` — `get_weather` (`@function_tool`) |
| Instructions | `agent.py` — biến `INSTRUCTIONS` |

## Cài đặt
```bash
pip install -r demo_agents/weather_agent/requirements.txt
```

Python 3.9 cần thêm `eval_type_backport` (đã có trong `requirements.txt`) vì `openai-agents` dùng cú pháp
union `X | None` chỉ native từ Python 3.10.

## Chạy test offline (không cần API key)
```bash
python -m pytest demo_agents/weather_agent/test_tool.py demo_agents/weather_agent/test_run_cli.py -v
```

## Chạy live (cần OPENAI_API_KEY của riêng bạn)
Chạy bằng `-m` từ thư mục gốc repo (không chạy trực tiếp `python demo_agents/weather_agent/run.py` — sẽ
lỗi `ModuleNotFoundError` vì repo root không tự vào `sys.path` khi gọi file trực tiếp kiểu đó):

```bash
export OPENAI_API_KEY=sk-...   # xem .env.example
python -m demo_agents.weather_agent.run "Thời tiết ở Hà Nội thế nào?"
```

## Giới hạn đã biết
Phiên build này **không có `OPENAI_API_KEY`** trong sandbox, nên phần gọi LLM thật (`Runner.run_sync`)
chưa được chạy thử trực tiếp — chỉ verify được: (1) logic tool `_get_weather_impl` qua `test_tool.py`, và
(2) nhánh báo lỗi khi thiếu key qua `test_run_cli.py`. Muốn xác nhận toàn bộ vòng lặp LLM thật, tự thêm key
của bạn rồi chạy lệnh ở mục "Chạy live".
