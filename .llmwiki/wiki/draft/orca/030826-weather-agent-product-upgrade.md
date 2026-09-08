---
type: draft
title: weather-agent-product-upgrade
status: proposed
tags: [orca-workflow, output-report]
timestamp: 2026-08-03
task: T-260727-01
---

# 030826-weather-agent-product-upgrade
**Type:** draft
**Status:** proposed
**Tags:** orca-workflow, output-report
**Proposed:** 2026-08-03

## Agent Task Assignment
| Task | Agent | Status |
|------|-------|--------|
| Tool thật (Open-Meteo, bỏ mock 4 thành phố) | Claude Code | done |
| Multi-provider model (DeepSeek/OpenAI) | Claude Code | done |
| Chatbot nhớ hội thoại (SQLiteSession) | Claude Code | done |
| Giao diện chat kiểu ChatGPT | Claude Code | done |
| Sửa lỗi double-submit khi gõ tiếng Việt (IME) | Claude Code | done |
| Agent tự khai báo năng lực qua chat | Claude Code | done |
| Product tour (spotlight) cho 4 chức năng chính | Claude Code | done |

## What
Nâng weather agent từ MVP demo (mock 4 thành phố, mỗi câu hỏi độc lập, UI form đơn giản) lên bản
"product-grade" theo yêu cầu trực tiếp của người dùng: tool gọi API thời tiết thật (Open-Meteo,
không cần key) cho bất kỳ thành phố nào trên thế giới, agent nhớ ngữ cảnh hội thoại nhiều lượt, và
giao diện chat theo phong cách ChatGPT.

## Output
- **Tool thật:** `agent.py` gọi Open-Meteo Geocoding + Forecast API thay `_WEATHER_DATA` mock.
  Test offline vẫn được nhờ mock `requests.get`/`_geocode`/`_fetch_current` (12/12 pass, không cần
  mạng thật khi chạy `pytest`).
- **Multi-provider model:** `model_provider.py` — DeepSeek (`deepseek-chat` qua endpoint
  OpenAI-compatible) nếu có `DEEPSEEK_API_KEY`, else `gpt-4o-mini` nếu có `OPENAI_API_KEY`. Key
  đọc từ `.env` local (đã `.gitignore`), không hardcode.
- **Chatbot nhớ hội thoại:** `chatdemo.py` dùng `SQLiteSession` có sẵn của Agents SDK — test thật:
  hỏi "Hà Nội" rồi hỏi tiếp "còn Hạ Long so với đó thế nào?" (không nhắc lại "Hà Nội") → agent trả
  lời đúng, tự dựng bảng so sánh hai thành phố.
- **UI kiểu ChatGPT:** `web/chat.html` viết lại hoàn toàn — sidebar tối, cột chat căn giữa, bong
  bóng tin nhắn người dùng, avatar + text thường cho agent, ô nhập tự giãn, nút "Cuộc trò chuyện
  mới", gợi ý câu hỏi mẫu, hiệu ứng "đang gõ".
- **4 bug thật phát hiện khi nối API thật (không phải giả định):**
  1. `openai-agents==0.8.4` vỡ với `openai>=2.40` (`pydantic.ValidationError` trên
     `InputTokensDetails.cache_write_tokens` thiếu) → ghim `openai==2.19.0`.
  2. Open-Meteo geocoding `language=vi` xếp hạng kết quả sai — "New York" bị lệch thành
     "York, Nebraska" (không lọt top-10 tìm bằng tiếng Việt) → đổi sang `language=en` + chọn kết
     quả dân số (population) lớn nhất trong top-5.
  3. "Atlantis" (dùng làm ví dụ "không tồn tại" khi tool còn mock) hoá ra là một thị trấn CÓ THẬT ở
     Nam Phi — Open-Meteo geocode ra tọa độ thật, guardrail NO_DATA không kích hoạt. Đổi ví dụ
     "không tồn tại" trong test + wikieval golden sang chuỗi vô nghĩa chắc chắn không phải địa danh.
  4. wikieval goldens cũ assert nhiệt độ cố định (`29°C`) — vỡ ngay khi tool trả dữ liệu thật (đổi
     theo ngày) → đổi sang `regex` cho định dạng nhiệt độ thay vì giá trị cố định.
- `python3 -m pytest demo_agents/weather_agent/ -q` → **12 passed** (tăng từ 4, thêm test mock
  network cho `_geocode`/`_fetch_current`/lỗi mạng).
- `python3 harness/scripts/wikieval.py --outputs harness/evals/weather-agent-outputs.json --write-baseline`
  → **3/3 decided-passing** (baseline mới, asserts dạng regex).
- **Bug thật thứ 5 — double-submit khi gõ tiếng Việt:** người dùng báo tin nhắn bị nhân đôi ("thời
  tiết harmburg hôm nay thế nào" gửi kèm một bản rút gọn "nào" ngay sau). Nguyên nhân: bấm Enter
  trong lúc IME còn đang ghép dấu (composition) kích hoạt submit sớm với nội dung dở dang. Sửa bằng
  `compositionstart`/`compositionend` + kiểm `e.isComposing`/`keyCode 229` trước khi submit bằng
  Enter, cộng thêm cờ `sending` chặn double-submit khi request trước chưa xong (defense-in-depth).
- **Agent tự khai báo năng lực:** `INSTRUCTIONS` thêm đoạn xử lý câu hỏi "bạn làm được gì?" — agent
  trả lời đúng năng lực thật (tra thời tiết hiện tại mọi thành phố, nhớ hội thoại) và giới hạn thật
  (không dự báo nhiều ngày, không dữ liệu lịch sử), không phóng đại. Test thật qua `/api/chat`: hỏi
  "Bạn làm được gì?" → agent liệt kê đúng, không bịa thêm chức năng.
- **Product tour:** dùng skill `tour-guide` (port sang vanilla JS vì trang không dùng React) — overlay
  spotlight SVG-mask đánh dấu 4 điểm: giới thiệu agent (sidebar), nút "Cuộc trò chuyện mới", câu hỏi
  mẫu, ô nhập câu hỏi. Tự hiện lần đầu mở trang (`localStorage`), có nút "?" mở lại bất kỳ lúc nào.

## Files
| File | Action |
|------|--------|
| `demo_agents/weather_agent/agent.py` | rewritten (Open-Meteo thật, multi-provider model) |
| `demo_agents/weather_agent/model_provider.py` | created |
| `demo_agents/weather_agent/test_tool.py` | rewritten (mock network, 11 test) |
| `demo_agents/weather_agent/test_run_cli.py` | edited (hermetic — cô lập khỏi `.env` thật) |
| `demo_agents/weather_agent/run.py` | edited (check `has_any_key()` thay vì chỉ `OPENAI_API_KEY`) |
| `demo_agents/weather_agent/chatdemo.py` | rewritten (SQLiteSession, `/api/reset`) |
| `demo_agents/weather_agent/webdemo.py` | edited (bỏ ref `_WEATHER_DATA` đã xoá) |
| `demo_agents/weather_agent/web/chat.html` | rewritten (giao diện ChatGPT-style, fix IME double-submit, product tour) |
| `demo_agents/weather_agent/web/index.html` | edited (copy cập nhật, bỏ danh sách 4 thành phố cố định) |
| `demo_agents/weather_agent/requirements.txt` | edited (ghim `openai==2.19.0`, thêm `requests`) |
| `demo_agents/weather_agent/README.md` | rewritten |
| `demo_agents/weather_agent/.env.example` | edited (thêm `DEEPSEEK_API_KEY`) |
| `.gitignore` | edited (`.env`, `chat_sessions.sqlite3*`) |
| `llmwiki/wiki/sources/evals/weather-known-city.md` | edited (regex thay vì giá trị cố định) |
| `llmwiki/wiki/sources/evals/weather-case-insensitive.md` | edited |
| `llmwiki/wiki/sources/evals/weather-unknown-city.md` | edited (đổi input, bỏ "Atlantis") |
| `harness/evals/weather-agent-outputs.json` | regenerated |
| `harness/metrics/eval-baseline.json` | regenerated |
| `wiki/index.md`, `wiki/log.md` | modified |

## Notes
- Invoked via: hội thoại trực tiếp với người dùng (không qua `/orca-workflow` propose→gate chính
  thức) — người dùng phản hồi rõ ràng UI "quá xấu" và agent "quá đối phó", rồi xác nhận hướng đi
  (Open-Meteo, nhớ hội thoại) qua `AskUserQuestion` trước khi code. Coi phản hồi đó là gate tương
  đương phê duyệt, theo đúng judgement call đã dùng cho `T-260727-01` trước đây.
- Người dùng dán API key DeepSeek thật trực tiếp vào chat để test — đã ghi vào `.env` local
  (`.gitignore`, không commit); key vẫn còn nguyên văn trong lịch sử hội thoại — người dùng xác
  nhận không cần xoay lại vì chỉ là key test.
- Chưa commit — theo quy tắc an toàn chung, chờ người dùng xác nhận.

## Origin
- **Draft:** `wiki/draft/orca/030826-weather-agent-product-upgrade.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
