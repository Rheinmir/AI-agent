---
type: eval
id: weather-unknown-city
tags: [weather-agent, tools, guardrail]
timestamp: 2026-08-03
input: "Xyzzyxplorpqq"
expected: "NO_DATA:Xyzzyxplorpqq"
asserts:
  - 'equals:NO_DATA:Xyzzyxplorpqq'
---

# weather-unknown-city

Golden cho guardrail "không bịa số liệu": chuỗi vô nghĩa không geocode được thành nơi thật nào
phải trả đúng marker `NO_DATA:<city>`, để instructions của agent phát hiện và báo rõ với người
dùng thay vì đoán số liệu — xem [[instructions]].

**Lưu ý bug thật phát hiện lúc chuyển sang Open-Meteo:** input cũ "Atlantis" (dùng khi tool còn
mock) hoá ra là tên một thị trấn CÓ THẬT (Atlantis, Nam Phi) — Open-Meteo geocode ra tọa độ thật,
guardrail không kích hoạt. Đổi golden sang một chuỗi chắc chắn không phải địa danh nào.

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
- **Code:** `demo_agents/weather_agent/agent.py::_get_weather_impl`
