---
type: eval
id: agent-capability-declaration
tags: [weather-agent, agent-level]
timestamp: 2026-08-03
input: "Bạn làm được gì?"
expected: "Agent tự khai báo đúng năng lực thật — nhắc Open-Meteo, không phóng đại thêm chức năng"
asserts:
  - 'icontains:Open-Meteo'
  - 'icontains:thời tiết'
---

# agent-capability-declaration

Test đoạn `INSTRUCTIONS` bổ sung riêng cho việc tự khai báo năng lực (agent.py, mục "Khi người
dùng hỏi bạn làm được gì..."). Assert `icontains:Open-Meteo` để chắc agent không bịa ra một nguồn
dữ liệu khác hay chức năng không có thật — Open-Meteo là chi tiết cụ thể chỉ xuất hiện nếu model
thực sự bám theo INSTRUCTIONS thay vì trả lời chung chung kiểu "tôi là AI hữu ích".

**Lưu ý (2026-08-04):** người dùng report văn xuôi LLM không luôn nhắc đúng tên từng layer kiến
trúc (Data Collector, Memory, Harness...) khi trả lời câu hỏi này — nên đường đi PRODUCTION thật
(qua `chatdemo.py`) giờ KHÔNG còn gọi model cho câu hỏi loại này nữa: `harness.py` tự bắt
(`_is_capability_question`) và trả `_CAPABILITY_REPORT` tất định, liệt kê đủ tên 7 layer, không qua
LLM. Golden này vẫn hữu ích — nó test riêng đường MODEL FALLBACK (gọi `Runner.run_sync` trực tiếp,
bỏ qua harness) cho trường hợp câu hỏi không khớp `_is_capability_question` (phrasing lạ) nhưng
INSTRUCTIONS vẫn phải tự xử lý hợp lý. Test đường harness ngắn mạch (đường thật user đi) nằm ở
`demo_agents/weather_agent/test_harness.py` — pytest thường, không cần wikieval vì hoàn toàn tất
định, không có biến thiên LLM để chấm.

## Origin
- **Source:** [[instructions]]
- **Code:** `demo_agents/weather_agent/agent.py::INSTRUCTIONS` qua `agents.Runner.run_sync`
  (đường model fallback — đường harness ngắn mạch xem `harness.py::_CAPABILITY_REPORT`)
