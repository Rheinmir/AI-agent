---
type: concept
title: "Debug \"hành vi sống không đổi dù đã sửa code\" — kiểm tra process cũ trước khi nghi code"
tags: [debugging, harness, best-practice]
timestamp: 2026-08-05
---

# debugging-stale-process

Khi sửa code của 1 server đang chạy nền (chat demo, API server, bất kỳ process nào bind vào 1
port cố định), rồi "restart" bằng cách `kill` process cũ + chạy lại process mới — nếu hành vi
quan sát được qua HTTP (`curl`, request test) **vẫn y hệt như trước khi sửa**, đừng vội kết luận
code fix không có tác dụng hay bug vẫn còn.

**Kiểm tra trước:** có process KHÁC đang giữ đúng port đó không, bằng `lsof -i :<port>` (hoặc
tương đương trên hệ khác) — xem CHÍNH XÁC PID nào đang ở trạng thái `LISTEN` trên port đó.

## Vì sao lỗi này dễ xảy ra và dễ đánh lừa

Khi `kill` 1 process cũ rồi khởi động process mới bind vào CÙNG port, nếu vì lý do nào đó (process
cũ chưa thực sự chết, hoặc có 1 process KHÁC — không liên quan tới lần chạy trước đó của chính bạn
— đã và đang giữ port từ trước) mà process MỚI không bind được, nhiều framework server đơn giản
(vd `http.server` của Python) sẽ báo lỗi "address already in use" ra `stderr`/exit code khác 0 —
nhưng nếu log không được kiểm tra kỹ (chạy nền, redirect ra file, không nhìn trực tiếp), lỗi bind
này bị BỎ QUA ÂM THẦM. Mọi request test sau đó vẫn đang hit đúng process CŨ (hoặc process không
liên quan) đang thực sự phục vụ port đó — tạo cảm giác sai lầm rằng "code đã sửa không có tác
dụng" hoặc "bug vẫn còn nguyên", trong khi process ĐANG PHỤC VỤ request chưa từng chạy code mới.

## Áp dụng khi nào

Bất kỳ lúc nào quan sát được: đã sửa code + đã "restart" (kill + start lại) một server đang chạy
nền, nhưng hành vi live qua HTTP/API vẫn giống hệt bản TRƯỚC khi sửa — dù chỉ 1 lần, đây là dấu
hiệu ĐỦ ĐỂ dừng lại kiểm tra process-ownership của port TRƯỚC KHI tiếp tục nghi ngờ logic code.
Đây là bước chẩn đoán RẺ (1 lệnh `lsof`), nên làm SỚM trong chuỗi debug, không phải bước cuối cùng.

**Lưu ý phạm vi:** đây là bài học rút ra từ MỘT sự cố cụ thể (xem Origin) — trình bày như một dấu
hiệu-nên-nghi-ngờ hữu ích, KHÔNG phải quy luật đã được kiểm chứng qua nhiều lần lặp lại độc lập.

## Notes
- **Council verdict (qua skill `/wiki-create`, 2026-08-05):** 3 giám khảo độc lập — lăng kính CHÍNH
  XÁC: `AMEND_EXISTING` (candidate ban đầu có 1 chi tiết PID cụ thể KHÔNG có nguồn trong wiki — đã
  bỏ khỏi trang này; đề nghị trình bày như bài học từ 1 sự cố, không phải quy luật đã kiểm chứng
  nhiều lần — đã áp dụng ở mục "Áp dụng khi nào" phía trên). Lăng kính KHÔNG TRÙNG LẶP: `APPROVE`
  (đã grep toàn bộ `wiki/concepts/` — không trang nào cùng chủ đề debug process/port). Lăng kính
  GIÁ TRỊ TÁI DÙNG: `AMEND_EXISTING` (nội dung đã tồn tại trong `wiki/log.md` dưới dạng nhật ký
  ngày-tháng — đề nghị NÂNG CẤP thành trang concept độc lập, dễ tra cứu hơn, thay vì để chôn trong
  log). Quyết định cuối: nâng cấp — trang này CHÍNH THỨC HOÁ bài học đã có trong log.md, không phải
  tuyên bố kiến thức mới độc lập.
- Domain screen: `IN_DOMAIN` (kinh nghiệm debug trực tiếp trên tiến trình MCP server của
  weather_agent/devops_agent trong dự án này).

## Origin
- **Sự cố gốc:** `wiki/log.md`, entry "2026-08-04 — orca-workflow — mcp-internet-access-for-agents"
  — sửa `guardrails.py` của `weather_agent`, kill process `chatdemo.py` cũ, khởi động lại; `curl`
  liên tục trả kết quả CŨ; phát hiện qua `lsof -i :8767` thấy process Python 3.9 khác (chạy từ đầu
  phiên làm việc, trước khi bắt đầu sửa) vẫn giữ port — mọi lần "restart" sau đó bind thất bại âm
  thầm.
- **Nâng cấp thành trang concept qua:** skill `/wiki-create` (xem
  `~/.claude/skills/wiki-create/SKILL.md`), council 3 giám khảo (accuracy/novelty/value).
