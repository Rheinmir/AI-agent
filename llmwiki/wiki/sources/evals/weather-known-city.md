---
type: eval
id: weather-known-city
tags: [weather-agent, tools]
timestamp: 2026-08-01
input: "Hà Nội"
expected: "Hà Nội: 29°C, Nhiều mây"
asserts:
  - 'contains:Hà Nội'
  - 'contains:29°C'
---

# weather-known-city

Golden cho `_get_weather_impl` trong `demo_agents/weather_agent/agent.py`: thành phố có trong
`_WEATHER_DATA` phải trả đúng tên thành phố (giữ dấu) + nhiệt độ.

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
- **Code:** `demo_agents/weather_agent/agent.py::_get_weather_impl`
