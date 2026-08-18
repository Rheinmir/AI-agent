---
type: eval
id: agent-city-note-known
tags: [weather-agent, agent-level, data-collector]
timestamp: 2026-08-04
input: "Múi giờ ở Tokyo là bao nhiêu?"
expected: "Agent gọi tool get_city_note (Data Collector), trả đúng múi giờ đã thu thập sẵn cho Tokyo"
asserts:
  - 'icontains:UTC+9'
---

# agent-city-note-known

Test Ở CẤP AGENT tool `get_city_note` mới (`data_collector.py`, xem
`llmwiki/wiki/draft/orca/040826-weather-agent-3-layers.md`) — khác `get_weather` (dữ liệu thời gian
thực), đây là tập ghi chú THU THẬP SẴN (múi giờ, khí hậu chung) cho một số thành phố tiêu biểu.
Assert `icontains:UTC+9` xác nhận model thực sự gọi tool và bám đúng dữ liệu đã index, không tự
suy đoán múi giờ Nhật Bản từ kiến thức train sẵn (dù kết quả có thể trùng — điểm khác biệt thật là
INSTRUCTIONS có yêu cầu gọi tool cho câu hỏi loại này hay không).

## Origin
- **Source:** [[040826-weather-agent-3-layers]]
- **Code:** `demo_agents/weather_agent/agent.py::get_city_note`, `data_collector.py::lookup_city_note`
  qua `agents.Runner.run_sync`
