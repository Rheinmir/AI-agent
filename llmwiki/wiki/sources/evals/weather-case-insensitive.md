---
type: eval
id: weather-case-insensitive
tags: [weather-agent, tools]
timestamp: 2026-08-03
input: "  HÀ NỘI  "
expected: "Hà Nội: <nhiệt độ thật>°C, <mô tả WMO>"
asserts:
  - 'contains:Hà Nội'
  - 'regex:\d+([.,]\d+)?°C'
---

# weather-case-insensitive

Golden cho việc `city.strip()` trước khi gọi Open-Meteo geocoding: input có khoảng trắng thừa và
toàn chữ hoa vẫn phải resolve đúng "Hà Nội" (Open-Meteo tự xử lý case-insensitivity ở phía server,
`agent.py` chỉ cần `strip()` khoảng trắng trước khi gửi request — xem
[[huong-dan-xay-dung-agent-thuc-te]]).

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
- **Code:** `demo_agents/weather_agent/agent.py::_get_weather_impl`
