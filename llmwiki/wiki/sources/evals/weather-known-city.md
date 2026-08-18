---
type: eval
id: weather-known-city
tags: [weather-agent, tools]
timestamp: 2026-08-03
input: "Hà Nội"
expected: "Hà Nội: <nhiệt độ thật>°C, <mô tả WMO>"
asserts:
  - 'contains:Hà Nội'
  - 'regex:\d+([.,]\d+)?°C'
---

# weather-known-city

Golden cho `_get_weather_impl` trong `demo_agents/weather_agent/agent.py`: thành phố tồn tại phải
trả đúng tên (giữ dấu) + một giá trị nhiệt độ hợp lệ. Từ 2026-08-03 tool gọi **Open-Meteo thật**
(không còn mock cố định), nên golden dùng `regex` cho định dạng nhiệt độ thay vì một con số cố
định — nhiệt độ thật đổi theo ngày, chỉ định dạng ("số°C") là bất biến.

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
- **Code:** `demo_agents/weather_agent/agent.py::_get_weather_impl`
