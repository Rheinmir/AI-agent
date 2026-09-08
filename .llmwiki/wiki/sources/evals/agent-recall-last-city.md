---
type: eval
id: agent-recall-last-city
tags: [weather-agent, agent-level, memory, guardrail]
timestamp: 2026-08-04
input: "Thiết lập (không chấm điểm): memory.remember_last_city('Đà Lạt') gọi TRỰC TIẾP, không qua hội thoại — cô lập đúng phần cần test khỏi việc model có tự gọi get_weather đúng hay không. Session MỚI (chấm điểm, session_id khác hẳn, không liên quan gì tới session thiết lập): \"Còn hôm nay thời tiết ở đó thì sao?\""
expected: "Session mới không nêu tên thành phố nào — agent gọi tool recall_last_city, nhận 'Đà Lạt', HỎI XÁC NHẬN lại thay vì tự ý trả lời thời tiết luôn"
asserts:
  - 'icontains:Đà Lạt'
  - 'regex:\?'
  - 'not-contains:°C'
---

# agent-recall-last-city

Test long-term memory (`memory.py`, xem `llmwiki/wiki/draft/orca/040826-weather-agent-3-layers.md`)
— tính năng KHÁC HẲN `agent-multiturn-memory` (test `SQLiteSession`, chỉ nhớ TRONG 1 session).
Golden này cố tình dùng **2 session hoàn toàn độc lập** (không chung `session_id`, không chung lịch
sử hội thoại) để chứng minh trí nhớ đến từ layer Memory dài hạn riêng (SQLite global, sống sót qua
restart) chứ không phải từ ngữ cảnh hội thoại trong-phiên.

Candidate output sinh bằng cách: (1) gọi `memory.remember_last_city('Đà Lạt')` trực tiếp trên 1 DB
tạm (`tempfile`, KHÔNG đụng tới `long_term_memory.sqlite3` thật của demo — tránh để lại trạng thái
phụ trên máy chạy thật) để thiết lập trạng thái "đã nhớ" một cách tất định, không phụ thuộc model có
tự gọi `get_weather` đúng city ở một lượt trước hay không; (2) mở session hoàn toàn mới, hỏi "Còn
hôm nay thời tiết ở đó thì sao?" — không nêu thành phố. Chỉ output của bước (2) được chấm.

`asserts` đòi cả 3: tên Đà Lạt xuất hiện (chứng minh gọi đúng `recall_last_city` và dùng kết quả),
một dấu `?` (chứng minh đang HỎI XÁC NHẬN đúng theo `INSTRUCTIONS`, không khẳng định chắc chắn), và
KHÔNG có `°C` (chứng minh chưa tự ý trả lời thời tiết luôn khi chưa được xác nhận — nếu agent bỏ
qua bước xác nhận và tự gọi `get_weather` cho "Đà Lạt" ngay, assert `not-contains:°C` sẽ fail, đúng
ý đồ guardrail trong `INSTRUCTIONS`: "recall_last_city... CHỈ dùng để GỢI Ý").

## Origin
- **Source:** [[040826-weather-agent-3-layers]]
- **Code:** `demo_agents/weather_agent/agent.py::recall_last_city`, `memory.py` qua
  `agents.Runner.run_sync`
