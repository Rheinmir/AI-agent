---
type: eval
id: agent-guardrail-legit-weather-not-blocked
tags: [weather-agent, agent-level, guardrail]
timestamp: 2026-08-04
input: "Thời tiết ở Đà Lạt thế nào?"
expected: "Câu hỏi thời tiết hợp lệ KHÔNG bị guardrail chặn — agent trả lời thời tiết bình thường, không phải OUT_OF_SCOPE_MESSAGE"
asserts:
  - 'regex:\d+([.,]\d+)?°C'
  - 'not-contains:ngoài phạm vi của mình'
---

# agent-guardrail-legit-weather-not-blocked

Golden BẮT BUỘC phải có cạnh 2 golden guardrail kia — không có nó, bộ eval chỉ chứng minh được
"guardrail CÓ THỂ chặn", không chứng minh được "guardrail không chặn NHẦM câu hỏi hợp lệ" (false
positive). 1 guardrail chặn quá tay (chặn cả câu hỏi thời tiết bình thường) tệ ngang hoặc tệ hơn
guardrail không chặn được gì — golden này là bài kiểm false-positive tối thiểu.

`asserts` đòi CẢ 2: có số nhiệt độ hợp lệ kèm `°C` (chứng minh tool `get_weather` thật đã chạy,
không phải rơi vào nhánh guardrail) VÀ `not-contains` cụm mở đầu của `OUT_OF_SCOPE_MESSAGE` (chứng
minh chắc chắn không phải bị chặn rồi trả lời kiểu gần giống).

## Phạm vi thật của eval này
Chỉ test 1 câu hỏi thời tiết "sạch" (không mơ hồ). KHÔNG test các câu hỏi BIÊN — vd câu hỏi vừa có
từ khoá thời tiết vừa có ý địa lý lồng vào nhau ("thời tiết ở thủ đô nước Pháp" — đòi suy luận thủ
đô Pháp là Paris trước khi tra thời tiết, guardrail có thể phân loại sai theo cả 2 hướng). Bộ 3
golden guardrail hiện tại (2 trip + 1 không trip) đủ để phát hiện lỗi RÕ RÀNG (guardrail hỏng hoàn
toàn, hoặc chặn/không-chặn ngược hẳn ý định) — không đủ để đo độ chính xác phân loại trên diện rộng
theo đúng nghĩa 1 bài eval classifier thật.

## Origin
- **Source:** [[040826-weather-agent-3-layers]]
- **Code:** `demo_agents/weather_agent/guardrails.py::weather_scope_guardrail`,
  `demo_agents/weather_agent/agent.py::get_weather` qua `agents.Runner.run_sync`
