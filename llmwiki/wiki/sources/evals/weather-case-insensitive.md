---
type: eval
id: weather-case-insensitive
tags: [weather-agent, tools]
timestamp: 2026-08-01
input: "  HÀ NỘI  "
expected: "Hà Nội: 29°C, Nhiều mây"
asserts:
  - 'contains:Hà Nội'
---

# weather-case-insensitive

Golden cho `_normalize()` (`.strip().lower()`): input có khoảng trắng thừa và toàn chữ hoa vẫn phải
khớp key dict `_WEATHER_DATA` (giữ dấu tiếng Việt — bug thật đã sửa lúc build, xem
[[huong-dan-xay-dung-agent-thuc-te]]).

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
- **Code:** `demo_agents/weather_agent/agent.py::_get_weather_impl`
