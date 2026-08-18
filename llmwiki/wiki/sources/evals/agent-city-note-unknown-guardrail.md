---
type: eval
id: agent-city-note-unknown-guardrail
tags: [weather-agent, agent-level, data-collector, guardrail]
timestamp: 2026-08-04
input: "Cho tôi ghi chú về múi giờ và khí hậu ở Xyzzyxplorpqq"
expected: "Agent báo rõ chưa có ghi chú cho thành phố này, KHÔNG bịa thông tin múi giờ/khí hậu thay thế"
asserts:
  - 'icontains:chưa có'
  - 'not-contains:UTC'
---

# agent-city-note-unknown-guardrail

Guardrail Ở CẤP AGENT cho tool `get_city_note` — cùng tinh thần `agent-unknown-city-guardrail`
(guardrail của `get_weather`) nhưng cho nguồn dữ liệu khác: `data_collector.lookup_city_note` trả
`None`/`NO_DATA:` cho thành phố ngoài tập đã thu thập, và `INSTRUCTIONS` yêu cầu model nói rõ điều
đó thay vì tự bịa một múi giờ/đặc điểm khí hậu nghe hợp lý. `not-contains:UTC` xác nhận model không
lẻn chèn một con số múi giờ tự đoán vào đâu đó trong câu trả lời — assert chặt hơn `icontains` một
chiều, kiểm cả việc KHÔNG xuất hiện định dạng dữ liệu mà chỉ tool thật mới trả về được.

## Origin
- **Source:** [[040826-weather-agent-3-layers]]
- **Code:** `demo_agents/weather_agent/agent.py::get_city_note`, `data_collector.py::lookup_city_note`
  qua `agents.Runner.run_sync`
