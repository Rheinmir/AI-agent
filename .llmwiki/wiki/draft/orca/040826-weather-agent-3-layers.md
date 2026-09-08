---
type: draft
title: weather-agent-3-layers
status: proposed
tags: [orca-workflow, output-report]
timestamp: 2026-08-04
task: T-260727-01
---

# 040826-weather-agent-3-layers
**Type:** draft
**Status:** proposed
**Tags:** orca-workflow, output-report
**Proposed:** 2026-08-04

## Agent Task Assignment
| Task | Agent | Status |
|------|-------|--------|
| Harness tường minh (max_turns + retry backoff) | Claude Code | done |
| Data Collector thật (ghi chú thu thập sẵn theo thành phố) | Claude Code | done |
| Long-term memory (nhớ xuyên phiên, khác SQLiteSession trong-phiên) | Claude Code | done |
| Cập nhật INSTRUCTIONS/README phản ánh đúng năng lực mới | Claude Code | done |

## What
Người dùng hỏi vì sao "Bạn làm được gì?" chỉ báo 2 năng lực trong khi wiki mô tả 5 layer bọc quanh
model — trả lời (không tô hồng): chỉ Tools + Memory (trong-phiên) là thật, Context/Harness chỉ dựa
mặc định của SDK, Data Collector chưa có. Yêu cầu tiếp theo: triển khai TẤT CẢ, theo thứ tự an toàn
nhất trước. Thực hiện theo thứ tự: Harness (cơ học nhất, ít rủi ro thiết kế nhất) → Data Collector
(nguồn dữ liệu curated nhỏ, tách biệt rõ) → Long-term memory (nhiều quyết định thiết kế nhất, làm
sau cùng).

## Output
- **Harness (`harness.py`, mới):** `run_with_harness()` bọc `Runner.run_sync` — `max_turns=6` tường
  minh (thay mặc định ẩn 10 của SDK), retry backoff (0.5s, 1.5s) tối đa 2 lần cho lỗi tạm thời;
  `MaxTurnsExceeded` KHÔNG retry (lỗi tất định). `chatdemo.py` gọi qua harness thay vì
  `Runner.run_sync` trực tiếp, có nhánh lỗi riêng cho `MaxTurnsExceeded`. 5 test mock
  (`test_harness.py`).
- **Data Collector (`data_collector.py`, mới):** `lookup_city_note()` — dict 11 thành phố tiêu biểu
  (Hà Nội, TP.HCM, Đà Nẵng, Tokyo, New York, London, Paris, Singapore...), ghi chú thực tế ổn định
  (múi giờ, đặc điểm khí hậu chung theo mùa) — KHÁC `get_weather` (thời gian thực). Đơn giản hoá so
  với RAG đầy đủ: index bằng dict từ khoá, không vector DB — nhưng đúng luồng thu thập→làm
  sạch→index→tra cứu. Thành phố ngoài danh sách trả `None`, không bịa. Tool mới `get_city_note`
  trong `agent.py`. 4 test (`test_data_collector.py`).
- **Long-term memory (`memory.py`, mới):** `remember_last_city`/`recall_last_city` — SQLite riêng
  (`long_term_memory.sqlite3`), lưu GLOBAL (demo local 1 user, không có đăng nhập) thành phố tra
  cứu thời tiết THÀNH CÔNG gần nhất, sống sót qua mọi `session_id` và cả restart server — khác hẳn
  `SQLiteSession` (chỉ nhớ trong 1 phiên). `_get_weather_impl` tự ghi nhớ sau mỗi lần tra cứu thành
  công. Tool mới `recall_last_city` — INSTRUCTIONS yêu cầu CHỈ dùng làm gợi ý, luôn hỏi xác nhận lại
  với người dùng, không tự ý coi là câu trả lời đúng. 4 test (`test_memory.py`).
- **`INSTRUCTIONS` (agent.py):** cập nhật hướng dẫn dùng 2 tool mới + khai báo lại năng lực thật —
  từ 2 mục (tra thời tiết, nhớ trong phiên) lên 4 mục (thêm ghi chú thành phố + nhớ xuyên phiên dạng
  gợi ý), vẫn giữ kỷ luật "không phóng đại, không bịa chức năng không có".
- **`README.md`:** bảng năng lực mở rộng từ 3 hàng (Model/Tools/Instructions) lên 6 hàng, nêu rõ
  Context/Instruction và Evaluation vẫn còn thiếu/nằm ngoài thư mục — không tô hồng phần chưa làm.
- **Test:** 12 → 25 test, tất cả hermetic (mock network + SQLite qua `tmp_path`, không ghi vào
  `long_term_memory.sqlite3` thật khi chạy `pytest`).

## Files
| File | Action |
|------|--------|
| `demo_agents/weather_agent/harness.py` | created |
| `demo_agents/weather_agent/test_harness.py` | created |
| `demo_agents/weather_agent/data_collector.py` | created |
| `demo_agents/weather_agent/test_data_collector.py` | created |
| `demo_agents/weather_agent/memory.py` | created |
| `demo_agents/weather_agent/test_memory.py` | created |
| `demo_agents/weather_agent/agent.py` | edited |
| `demo_agents/weather_agent/chatdemo.py` | edited |
| `demo_agents/weather_agent/test_tool.py` | edited |
| `demo_agents/weather_agent/README.md` | edited |
| `wiki/index.md`, `wiki/log.md` | updated |

## Notes
- Invoked via: người dùng hỏi thẳng vì sao capability declaration chỉ có 2, rồi yêu cầu triển khai
  đủ "theo thứ tự chắc trước" — thứ tự Harness→Data Collector→Memory là lựa chọn của Claude Code
  (giải thích rõ với người dùng), dựa trên mức độ rủi ro thiết kế tăng dần, không phải yêu cầu tường
  minh về thứ tự cụ thể.
- Chưa làm: Context/Instruction layer tự viết (hiện vẫn dựa hoàn toàn vào assembly ngầm của Agents
  SDK) — không nằm trong 3 việc được yêu cầu lần này.
- Chưa bổ sung wikieval goldens cho 2 tool mới (`get_city_note`, `recall_last_city`) — cần gọi
  DeepSeek/OpenAI thật để sinh candidate output như 4 golden agent-level trước đó, chưa làm vì
  không nằm trong yêu cầu "triển khai 3 layer" — đề xuất làm tiếp nếu người dùng đồng ý (harness R10
  docs-gate sẽ hỏi).

## Origin
- **Draft:** `wiki/draft/orca/040826-weather-agent-3-layers.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
