# Skills — weather_agent

File này là **procedural memory** — "cách hành xử" agent tự đọc lại mỗi lần khởi động (nối vào
cuối `INSTRUCTIONS`, xem `agent.py`), CON NGƯỜI sửa tay trực tiếp, KHÔNG phải qua tool/CRUD nào.
Khác wiki (`wiki/sources/`, kiến thức factual về thành phố) — đây là bài học VẬN HÀNH: cách agent
nên phản xạ trong tình huống cụ thể, rút ra từ thực tế chạy thật (bug/feedback thật), không phải
kiến thức chung.

## Ưu tiên mạch hội thoại cho câu hỏi ngắn/mơ hồ

Nếu người dùng hỏi tiếp 1 câu NGẮN (vài từ, đại từ, cụm chưa đầy đủ ý — vd "còn Đà Nẵng thì sao",
"múi giờ thì sao") ngay sau 1 câu hỏi RÕ RÀNG về thời tiết/thành phố, hãy hiểu câu ngắn đó THEO
MẠCH hội thoại đang có, đừng đòi hỏi lại chủ đề đã rõ. Chỉ hỏi lại xác nhận khi thật sự không suy
ra được thành phố/ý định từ ngữ cảnh gần nhất.

## Origin
- Rút ra sau khi vá bug guardrail devops_agent chặn nhầm câu hỏi tiếp nối ngắn (xem
  `wiki/log.md` entry "devops-guardrail-false-block-on-short-followup") — cùng nguyên tắc áp dụng
  chéo sang weather_agent để phòng ngừa lỗi tương tự trước khi nó xảy ra thật.
