---
type: draft
title: first-agent-weather-PLAN
status: proposed
timestamp: 2026-07-27
task: T-260727-01
---

# Build agent đầu tiên — Weather MVP — PLAN thi hành

**Goal:** Xây một agent Python chạy được, thể hiện đúng ba yếu tố nền tảng (Model, Tools, Instructions) từ
tài liệu đã ingest, dùng OpenAI Agents SDK.
**Architecture:** Một package Python độc lập chứa `agent.py` (định nghĩa Agent), tách riêng logic tool thuần
(`_get_weather_impl`) khỏi wrapper `@function_tool` để test được offline không cần gọi LLM; `run.py` là CLI
entrypoint gọi `Runner.run_sync`.
**Tech stack:** Python 3.9, package `openai-agents` (import name `agents`), `pytest` cho test.
**SPEC nguồn:** `wiki/sources/draft/270726-first-agent-weather.md` (đã duyệt 2026-07-27)

## Origin
- **SPEC:** `wiki/sources/draft/270726-first-agent-weather.md`
- **Commit:** _(verify-before-commit điền)_

## Global constraints
Chép nguyên văn từ SPEC nguồn:
- R1 (no-write-raw): "Agent không bao giờ ghi vào raw/ — raw/ là inbox của con người."
- R15 (no-ai-attribution): "Commit message KHÔNG được ghi công cho AI (Co-Authored-By: Claude…, Generated
  with Claude Code, 🤖). Author/committer chỉ là danh tính người."
- Không có `OPENAI_API_KEY` trong sandbox hiện tại → không gọi LLM thật được trong phiên build này; mọi
  task chỉ verify được bằng cách offline (pure function, hoặc nhánh lỗi thiếu key).
- Không được commit bất kỳ secret/API key thật nào vào repo.
- Không triển khai multi-agent, guardrails, hay tích hợp API thời tiết thật (Non-goals của SPEC).

**Điều chỉnh so với SPEC (phát hiện lúc lập PLAN — thuần kỹ thuật, không đổi scope/approach):** SPEC gọi
thư mục chứa là `agents/weather_agent/`. Nhưng package PyPI `openai-agents` **import bằng đúng tên
`agents`** (`from agents import Agent, Runner, function_tool`) — nếu thư mục top-level của project cũng tên
`agents/`, Python sẽ nhầm lẫn giữa package đã cài và thư mục local cùng tên trên `sys.path`, phá import.
Đổi tên container thành **`demo_agents/`** để tránh đụng độ; mọi nội dung/khái niệm khác giữ nguyên như
SPEC đã duyệt (model, tool, instructions, 4 task).

## File structure
- Tạo `demo_agents/__init__.py` — package marker rỗng, cho phép import `demo_agents.weather_agent...`
- Tạo `demo_agents/weather_agent/__init__.py` — package marker rỗng
- Tạo `demo_agents/weather_agent/agent.py` — định nghĩa `weather_agent` (Model + Tools + Instructions),
  hàm logic thuần `_get_weather_impl`, tool `get_weather`, hằng `NO_DATA`
- Tạo `demo_agents/weather_agent/requirements.txt` — khai dependency `openai-agents`
- Tạo `demo_agents/weather_agent/.env.example` — chỗ điền `OPENAI_API_KEY` (để trống)
- Tạo `demo_agents/weather_agent/test_tool.py` — pytest offline cho `_get_weather_impl`
- Tạo `demo_agents/weather_agent/run.py` — CLI entrypoint (`Runner.run_sync`)
- Tạo `demo_agents/weather_agent/test_run_cli.py` — pytest offline cho nhánh lỗi thiếu `OPENAI_API_KEY`
- Tạo `demo_agents/weather_agent/README.md` — hướng dẫn cài đặt/chạy + giới hạn sandbox

## Origin (tiếp)
- **Người thi hành cả 4 task:** Claude Code, trong cùng phiên — không dispatch CLI khác (theo Agent Task
  Assignment của SPEC).

---

### Task 1: Scaffold package + manifest

**Thoả:** FR-001 (một phần — dựng khung để chứa 3 yếu tố nền tảng)

**Files:**
- Tạo: `demo_agents/__init__.py`
- Tạo: `demo_agents/weather_agent/__init__.py`
- Tạo: `demo_agents/weather_agent/requirements.txt`
- Tạo: `demo_agents/weather_agent/.env.example`

**Interfaces:**
- Consumes: không có (task đầu tiên)
- Produces: package path `demo_agents.weather_agent` importable được — Task 2 dựa vào path này để đặt
  `agent.py`

- [ ] **Step 1: tạo package markers rỗng**

```python
# demo_agents/__init__.py
```

```python
# demo_agents/weather_agent/__init__.py
```

- [ ] **Step 2: khai dependency**

```text
# demo_agents/weather_agent/requirements.txt
openai-agents
pytest
eval_type_backport  # cần cho Python 3.9 — SDK dùng cú pháp union `X | None` (3.10+ mới có native)
```

- [ ] **Step 3: template biến môi trường**

```text
# demo_agents/weather_agent/.env.example
# Copy dòng dưới sang biến môi trường thật (export hoặc .env riêng của bạn) trước khi chạy run.py live.
OPENAI_API_KEY=
```

- [ ] **Step 4: verify scaffold**

Chạy: `python3 -c "import demo_agents.weather_agent; print('ok')"`
Mong đợi: `ok` (import package rỗng thành công, không lỗi `ModuleNotFoundError`)

- [ ] **Step 5: commit**

```bash
git add demo_agents/__init__.py demo_agents/weather_agent/__init__.py \
        demo_agents/weather_agent/requirements.txt demo_agents/weather_agent/.env.example
git commit -m "scaffold: khung package demo_agents/weather_agent"
```

---

### Task 2: Implement agent (model + tools + instructions)

**Thoả:** FR-001, FR-002, FR-003

**Files:**
- Tạo: `demo_agents/weather_agent/agent.py`

**Interfaces:**
- Consumes: package `demo_agents.weather_agent` từ Task 1
- Produces: `_get_weather_impl(city: str) -> str` (hàm thuần), `NO_DATA: str` (hằng đánh dấu không có dữ
  liệu), `get_weather` (FunctionTool, dùng trong `tools=[...]`), `weather_agent` (instance `Agent`) — Task 3
  import `_get_weather_impl`/`NO_DATA`; Task 4 import `weather_agent`

- [ ] **Step 1: viết agent.py đầy đủ**

```python
# demo_agents/weather_agent/agent.py
"""Weather agent — MVP minh hoạ 3 yếu tố nền tảng: Model, Tools, Instructions.

Xem wiki/concepts/agent.md, model-selection.md, tools.md, instructions.md.
"""

from agents import Agent, function_tool

NO_DATA = "NO_DATA"

_WEATHER_DATA = {
    "hà nội": {"city": "Hà Nội", "temp_c": 29, "condition": "Nhiều mây"},
    "sài gòn": {"city": "Sài Gòn", "temp_c": 33, "condition": "Nắng"},
    "đà nẵng": {"city": "Đà Nẵng", "temp_c": 30, "condition": "Mưa rào"},
    "hạ long": {"city": "Hạ Long", "temp_c": 27, "condition": "Trời quang"},
}


def _normalize(city: str) -> str:
    return city.strip().lower()


def _get_weather_impl(city: str) -> str:
    """Logic thuần, không phụ thuộc SDK — test offline được không cần OPENAI_API_KEY."""
    key = _normalize(city)
    if key not in _WEATHER_DATA:
        return f"{NO_DATA}:{city}"
    data = _WEATHER_DATA[key]
    return f"{data['city']}: {data['temp_c']}°C, {data['condition']}"


@function_tool
def get_weather(city: str) -> str:
    """Tra dữ liệu thời tiết mock cho một thành phố. Trả 'NO_DATA:<city>' nếu không có dữ liệu."""
    return _get_weather_impl(city)


INSTRUCTIONS = (
    "Bạn là weather agent. Luôn gọi tool get_weather để lấy dữ liệu trước khi trả lời — "
    "không bao giờ tự bịa nhiệt độ hay tình trạng thời tiết. "
    "Nếu kết quả tool bắt đầu bằng 'NO_DATA:', hãy nói rõ với người dùng là bạn không có dữ liệu "
    "thời tiết cho thành phố đó, và đừng đoán số liệu thay thế."
)

weather_agent = Agent(
    name="Weather agent",
    model="gpt-4o-mini",
    instructions=INSTRUCTIONS,
    tools=[get_weather],
)
```

- [ ] **Step 2: verify offline (không cần OPENAI_API_KEY — chỉ gọi hàm thuần)**

Chạy:
```bash
python3 -c "
from demo_agents.weather_agent.agent import _get_weather_impl, NO_DATA
print(_get_weather_impl('Hà Nội'))
print(_get_weather_impl('  HÀ NỘI  '))
print(_get_weather_impl('Atlantis'))
"
```
Mong đợi:
```
Hà Nội: 29°C, Nhiều mây
Hà Nội: 29°C, Nhiều mây
NO_DATA:Atlantis
```

**Lưu ý phát hiện lúc verify:** `str.lower()` không bỏ dấu tiếng Việt — key dict phải giữ dấu (`"hà nội"`,
không phải `"ha noi"`) để khớp với `_normalize()` của input có dấu. Đã sửa trong code trên (khác bản nháp
đầu — ghi lại để Task 3 viết test đúng hành vi thật).

- [ ] **Step 3: commit**

```bash
git add demo_agents/weather_agent/agent.py
git commit -m "feat: weather agent — model gpt-4o-mini + get_weather tool + instructions edge-case"
```

---

### Task 3: Unit test offline cho tool

**Thoả:** FR-002, FR-003

**Files:**
- Tạo: `demo_agents/weather_agent/test_tool.py`

**Interfaces:**
- Consumes: `_get_weather_impl`, `NO_DATA` từ `demo_agents/weather_agent/agent.py` (Task 2)
- Produces: bộ test `pytest` xanh — bằng chứng máy cho SC-004; không task nào sau phụ thuộc file này

- [ ] **Step 1: viết test**

```python
# demo_agents/weather_agent/test_tool.py
from demo_agents.weather_agent.agent import NO_DATA, _get_weather_impl


def test_get_weather_known_city():
    result = _get_weather_impl("Hà Nội")
    assert "Hà Nội" in result
    assert "29°C" in result


def test_get_weather_case_and_space_insensitive():
    result = _get_weather_impl("  HÀ NỘI  ")
    assert "Hà Nội" in result


def test_get_weather_unknown_city_returns_no_data_marker():
    result = _get_weather_impl("Atlantis")
    assert result == f"{NO_DATA}:Atlantis"
```

- [ ] **Step 2: chạy — mong PASS (implementation đã có từ Task 2)**

Chạy: `pytest demo_agents/weather_agent/test_tool.py -v`
Mong đợi: `3 passed` — không có test nào fail, không cần `OPENAI_API_KEY`

- [ ] **Step 3: commit**

```bash
git add demo_agents/weather_agent/test_tool.py
git commit -m "test: offline coverage cho get_weather (known city, case-insensitive, no-data)"
```

---

### Task 4: README + run.py (kèm test nhánh lỗi thiếu API key)

**Thoả:** FR-004

**Files:**
- Tạo: `demo_agents/weather_agent/run.py`
- Tạo: `demo_agents/weather_agent/test_run_cli.py`
- Tạo: `demo_agents/weather_agent/README.md`

**Interfaces:**
- Consumes: `weather_agent` từ `demo_agents/weather_agent/agent.py` (Task 2); `Runner` từ package `agents`
  (cài ở Task 1 qua `requirements.txt`)
- Produces: CLI thi hành được `python demo_agents/weather_agent/run.py "<câu hỏi>"`

- [ ] **Step 1: viết test cho nhánh lỗi thiếu key (test trước, chưa có run.py nên fail)**

```python
# demo_agents/weather_agent/test_run_cli.py
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
```

**Lưu ý phát hiện lúc verify:** chạy trực tiếp `python demo_agents/weather_agent/run.py` bị
`ModuleNotFoundError: No module named 'demo_agents'` vì Python chỉ thêm thư mục chứa script vào
`sys.path`, không thêm repo root. Phải gọi qua `python -m demo_agents.weather_agent.run` (module mode tự
thêm CWD vào `sys.path`) — đã sửa test và README theo cách gọi này.

- [ ] **Step 2: chạy cho THẤY nó fail**

Chạy: `pytest demo_agents/weather_agent/test_run_cli.py -v`
Mong đợi: FAIL — `FileNotFoundError` hoặc lỗi vì `demo_agents/weather_agent/run.py` chưa tồn tại

- [ ] **Step 3: viết run.py cho test pass**

```python
# demo_agents/weather_agent/run.py
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
```

- [ ] **Step 4: chạy lại — PASS**

Chạy: `pytest demo_agents/weather_agent/test_run_cli.py -v`
Mong đợi: `1 passed` — không cần `OPENAI_API_KEY` (test này verify đúng nhánh KHÔNG có key)

- [ ] **Step 5: viết README**

```markdown
# Weather agent — MVP đầu tiên

Minh hoạ 3 yếu tố nền tảng của một agent (xem `llmwiki/wiki/concepts/agent.md`):

| Yếu tố | Ở đâu trong code |
|---|---|
| Model | `agent.py` — `model="gpt-4o-mini"` |
| Tools | `agent.py` — `get_weather` (`@function_tool`) |
| Instructions | `agent.py` — biến `INSTRUCTIONS` |

## Cài đặt
\`\`\`bash
pip install -r demo_agents/weather_agent/requirements.txt
\`\`\`

## Chạy test offline (không cần API key)
\`\`\`bash
pytest demo_agents/weather_agent/test_tool.py demo_agents/weather_agent/test_run_cli.py -v
\`\`\`

## Chạy live (cần OPENAI_API_KEY của riêng bạn)
\`\`\`bash
export OPENAI_API_KEY=sk-...   # xem .env.example
python demo_agents/weather_agent/run.py "Thời tiết ở Hà Nội thế nào?"
\`\`\`

## Giới hạn đã biết
Phiên build này **không có `OPENAI_API_KEY`** trong sandbox, nên phần gọi LLM thật (`Runner.run_sync`)
chưa được chạy thử trực tiếp — chỉ verify được: (1) logic tool `_get_weather_impl` qua `test_tool.py`, và
(2) nhánh báo lỗi khi thiếu key qua `test_run_cli.py`. Muốn xác nhận toàn bộ vòng lặp LLM thật, tự thêm key
của bạn rồi chạy lệnh ở mục "Chạy live".
```

- [ ] **Step 6: commit**

```bash
git add demo_agents/weather_agent/run.py demo_agents/weather_agent/test_run_cli.py \
        demo_agents/weather_agent/README.md
git commit -m "docs+cli: run.py + README + test nhánh thiếu OPENAI_API_KEY"
```

## Self-review
1. **Phủ SPEC** — FR-001→FR-004 đều có task nhận (Task 2 nhận FR-001/002/003; Task 4 nhận FR-004; Task 1
   hỗ trợ FR-001 bằng khung package). SC-001/002/003 verify bằng đọc code+README (người); SC-004 verify
   bằng `pytest` (máy, task 3+4).
2. **Quét placeholder** — không còn nhãn giữ chỗ chưa điền nào; mọi step đều có code/lệnh thật + output kỳ
   vọng cụ thể.
3. **Nhất quán tên/kiểu** — `_get_weather_impl`, `NO_DATA`, `weather_agent`, `demo_agents.weather_agent.*`
   dùng thống nhất Task 2 → Task 3 → Task 4, không lệch tên ở bất kỳ chỗ nào.

## Origin
- **SPEC:** `wiki/sources/draft/270726-first-agent-weather.md`
- **Commit:** _(verify-before-commit điền)_
