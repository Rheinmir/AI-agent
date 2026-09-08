---
type: eval
id: agent-guardrail-fictional-place-weather-not-blocked
tags: [weather-agent, agent-level, guardrail, regression]
timestamp: 2026-08-04
input: "Thời tiết ở Atlantis thế nào?"
expected: "Hỏi THỜI TIẾT của 1 địa danh hư cấu/không tồn tại vẫn PHẢI qua được guardrail — chỉ NGOÀI PHẠM VI khi hỏi thứ KHÁC thời tiết (vị trí, lịch sử...) về địa danh đó"
asserts:
  - 'not-contains:ngoài phạm vi của mình'
  - 'regex:\d+([.,]\d+)?°C'
---

# agent-guardrail-fictional-place-weather-not-blocked

**Regression thật, không phải giả định** — phát hiện qua chính người dùng bấm nút gợi ý có sẵn
trong UI ("Thời tiết ở Atlantis thế nào?", 1 trong 4 câu hỏi mẫu ở `chat.html`) ngay sau khi
`weather_scope_guardrail` (xem [[040826-weather-agent-3-layers]]) được thêm vào. Bản đầu của
`_SCOPE_INSTRUCTIONS` chỉ liệt kê "TRONG PHẠM VI: hỏi thời tiết..." / "NGOÀI PHẠM VI: hỏi vị trí
địa lý..." mà không nói rõ 2 tiêu chí này áp dụng theo CẤU TRÚC câu hỏi hay theo BẢN CHẤT địa danh
— bộ phân loại (1 LLM riêng) tự suy luận thêm: "Atlantis" là địa danh HƯ CẤU/nổi tiếng về mặt lịch
sử-thần thoại, nên xếp cả câu "Thời tiết ở Atlantis thế nào?" vào nhóm "hỏi về địa danh" → NGOÀI
PHẠM VI — SAI, vì câu hỏi vẫn đang hỏi THỜI TIẾT, chỉ là thành phố có thể không có dữ liệu (đúng ra
phải để `get_weather` trả `NO_DATA`, không phải bị chặn từ vòng ngoài).

Fix: viết lại `_SCOPE_INSTRUCTIONS`, thêm dòng tường minh "TUYỆT ĐỐI KHÔNG xét thành phố được nhắc
tới có PHẢI là nơi có thật/nổi tiếng/hư cấu hay không — việc đó là của TOOL, không phải guardrail",
kèm ví dụ trực tiếp ("Thời tiết ở Atlantis/Hogwarts thế nào?" = TRONG PHẠM VI).

**Đây chính là golden `agent-guardrail-legit-weather-not-blocked` (test 1 thành phố CÓ THẬT, Đà
Lạt) KHÔNG bao phủ được** — hồi đó eval pass 13/13 vẫn không bắt được bug này, vì bug chỉ lộ ra với
địa danh KHÔNG PHẢI thành phố thật/bình thường. Đây đúng là ví dụ cho giới hạn "không test được case
biên" đã ghi ở golden kia — case biên đó giờ đã thành 1 golden riêng.

## Origin
- **Source:** [[040826-weather-agent-3-layers]]
- **Code:** `demo_agents/weather_agent/guardrails.py::weather_scope_guardrail` qua
  `agents.Runner.run_sync`
