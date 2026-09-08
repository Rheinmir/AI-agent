---
type: eval
id: agent-known-city
tags: [weather-agent, agent-level]
timestamp: 2026-08-03
input: "Thời tiết ở Hà Nội thế nào?"
expected: "Câu trả lời tự nhiên của AGENT THẬT (không phải hàm tool), nhắc tên thành phố + nhiệt độ hợp lệ"
asserts:
  - 'contains:Hà Nội'
  - 'regex:\d+([.,]\d+)?°C'
---

# agent-known-city

**Khác `weather-known-city` (tier tool-only) ở chỗ:** candidate output ở đây lấy từ
`Runner.run_sync(weather_agent, input)` THẬT — tức là qua cả Model (quyết định có gọi tool không)
lẫn Instructions (soạn câu trả lời), không phải gọi thẳng `_get_weather_impl()`. Đây là phản hồi
trực tiếp cho nhận xét "evaluation của dự án chứ đâu phải của wiki" — golden cũ chỉ test hàm nội
bộ, golden này test đúng cái người dùng thật sẽ thấy.

Golden xác nhận: agent thật, khi được hỏi tự nhiên, có tự quyết định gọi tool và trả lời có chứa
tên thành phố + một con số nhiệt độ hợp lệ (không bịa, không bỏ qua bước gọi tool).

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
- **Code:** `demo_agents/weather_agent/agent.py::weather_agent` qua `agents.Runner.run_sync`
