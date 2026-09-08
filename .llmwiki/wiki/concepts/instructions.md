---
type: concept
title: Instructions (cho agent)
tags: [agent, instructions, prompt-engineering]
timestamp: 2026-07-27
---

# Instructions (cho agent)

Instructions là các hướng dẫn và guardrail rõ ràng xác định cách một [[agent]] hành xử. Instructions chất
lượng cao giảm mơ hồ và cải thiện quyết định của agent, giúp workflow chạy mượt hơn và ít lỗi hơn — yếu tố
thiết yếu với mọi ứng dụng LLM, đặc biệt quan trọng với agents.

## Thực hành tốt

1. **Dùng tài liệu hiện có** — dựa vào quy trình vận hành, kịch bản hỗ trợ, hoặc tài liệu chính sách sẵn có để
   tạo routine thân thiện với LLM (ví dụ routine chăm sóc khách hàng tương ứng sát từng bài viết trong
   knowledge base).
2. **Yêu cầu agent chia nhỏ tác vụ** — các bước nhỏ hơn, rõ ràng hơn từ tài nguyên dày đặc giúp giảm mơ hồ
   và giúp model theo instructions tốt hơn.
3. **Định nghĩa hành động rõ ràng** — mọi bước trong routine nên tương ứng một hành động hoặc đầu ra cụ
   thể (hỏi người dùng mã đơn hàng, gọi API lấy chi tiết tài khoản...); nói rõ cả cách diễn đạt thông điệp gửi
   người dùng để giảm khoảng trống cho lỗi diễn giải.
4. **Bao quát edge cases** — dự đoán các biến thể phổ biến (thiếu thông tin, câu hỏi bất ngờ) và có
   instructions xử lý bằng bước điều kiện/nhánh.

## Tự động sinh instructions

Có thể dùng các model suy luận nâng cao (ví dụ o1, o3-mini) để tự động chuyển tài liệu help center hiện có
thành một tập instructions dạng danh sách đánh số, rõ ràng, không mơ hồ — bằng một prompt mẫu yêu cầu
model đóng vai "chuyên gia viết instructions cho LLM agent".

## Prompt templates

Một chiến lược hiệu quả để quản lý độ phức tạp mà chưa cần chuyển sang hệ đa agent là dùng **prompt
templates**: một base prompt linh hoạt nhận các biến chính sách, thay vì duy trì nhiều prompt riêng cho từng
ca sử dụng. Cách này đơn giản hóa bảo trì và eval; khi ca sử dụng mới xuất hiện chỉ cần cập nhật biến thay
vì viết lại toàn bộ workflow. Xem thêm [[orchestration]].

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
