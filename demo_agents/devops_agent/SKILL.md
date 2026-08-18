# Skills — devops_agent

File này là **procedural memory** — "cách hành xử" agent tự đọc lại mỗi lần khởi động (nối vào
cuối `INSTRUCTIONS`, xem `agent.py`), CON NGƯỜI sửa tay trực tiếp, KHÔNG phải qua tool/CRUD nào.
Khác wiki (`wiki/sources/`, cheatsheet DevOps đã kiểm chứng) — đây là bài học VẬN HÀNH: cách agent
nên phản xạ trong tình huống cụ thể, rút ra từ thực tế chạy thật (bug/feedback thật), không phải
kiến thức chung.

## Ưu tiên mạch hội thoại cho câu hỏi ngắn/mơ hồ

Nếu người dùng hỏi tiếp 1 câu NGẮN (vài từ, đại từ, cụm chưa đầy đủ ý — vd "về stage", "còn canary
thì sao") ngay sau 1 câu hỏi RÕ RÀNG về DevOps, hãy hiểu câu ngắn đó THEO MẠCH hội thoại đang có,
đừng vội coi là ngoài phạm vi chỉ vì nó ngắn/thiếu ngữ cảnh riêng lẻ.

## Origin
- Rút ra TRỰC TIẾP từ bug thật: guardrail chặn nhầm 3 tin nhắn liên tiếp (kể cả tin nhắn chứa gần
  nguyên văn cụm từ đã khai TRONG PHẠM VI) vì thiếu đoạn chỉ dẫn ưu tiên ngữ cảnh — xem
  `wiki/log.md` entry "devops-guardrail-false-block-on-short-followup". Đoạn chỉ dẫn tương đương
  đã thêm thẳng vào `guardrails.py::_SCOPE_INSTRUCTIONS`; đặt LẶP LẠI ở đây (procedural memory)
  để INSTRUCTIONS chính lẫn phần "kỹ năng đã học" đều nhất quán, và để con người sửa/mở rộng thêm
  bài học tương lai mà không phải sửa trực tiếp code.
