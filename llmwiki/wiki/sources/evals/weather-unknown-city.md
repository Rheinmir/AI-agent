---
type: eval
id: weather-unknown-city
tags: [weather-agent, tools, guardrail]
timestamp: 2026-08-01
input: "Atlantis"
expected: "NO_DATA:Atlantis"
asserts:
  - 'equals:NO_DATA:Atlantis'
---

# weather-unknown-city

Golden cho guardrail "không bịa số liệu": thành phố không có trong `_WEATHER_DATA` phải trả đúng
marker `NO_DATA:<city>`, để instructions của agent phát hiện và báo rõ với người dùng thay vì đoán
số liệu — xem [[instructions]].

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
- **Code:** `demo_agents/weather_agent/agent.py::_get_weather_impl`
