---
type: eval
id: agent-multiturn-memory
tags: [weather-agent, agent-level, memory]
timestamp: 2026-08-03
input: "Lượt 1: \"Thời tiết ở Hà Nội thế nào?\" (cùng session) — Lượt 2: \"Còn Hạ Long thì so với đó thế nào?\""
expected: "Lượt 2 hiểu \"đó\" = Hà Nội (không cần nhắc lại tên), trả lời có cả Hạ Long lẫn so sánh với Hà Nội"
asserts:
  - 'contains:Hạ Long'
  - 'contains:Hà Nội'
  - 'regex:\d+([.,]\d+)?°C'
---

# agent-multiturn-memory

Test `SQLiteSession` — tính năng KHÔNG THỂ test ở cấp tool (hàm `_get_weather_impl` không có khái
niệm "session"/"lượt trước"). Candidate output sinh ra bằng cách gọi `Runner.run_sync` HAI LẦN với
CÙNG một `SQLiteSession`: lượt 1 hỏi thời tiết Hà Nội (không lưu vào baseline), lượt 2 hỏi "còn Hạ
Long thì so với đó thế nào?" — KHÔNG nhắc lại "Hà Nội". Chỉ output của lượt 2 được chấm.

`asserts` đòi cả 3: tên Hạ Long (câu hỏi mới), tên Hà Nội (chứng minh nhớ ngữ cảnh — nếu agent
"quên", nó sẽ hỏi lại "so với đâu?" thay vì tự hiểu, và assert `contains:Hà Nội` sẽ fail), và một
giá trị nhiệt độ hợp lệ (chứng minh vẫn gọi tool thật cho Hạ Long, không chỉ nhắc lại số cũ).

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
- **Code:** `demo_agents/weather_agent/chatdemo.py` (cách dùng `SQLiteSession` thật trong sản phẩm)
