---
type: concept
title: Agent
tags: [agent, llm, autonomy]
timestamp: 2026-07-27
---

# Agent

Agent là hệ thống có thể độc lập hoàn thành một [[workflow]] thay mặt người dùng, với mức độ tự chủ cao —
khác với phần mềm thông thường vốn chỉ giúp người dùng tinh gọn/tự động hóa workflow chứ không tự thực
thi nó.

Ứng dụng tích hợp LLM nhưng không dùng LLM để kiểm soát việc thực thi workflow (chatbot đơn giản, LLM
một lượt, bộ phân loại cảm xúc) **không phải** là agent.

## Hai đặc điểm cốt lõi

1. **Agent tận dụng LLM để quản lý việc thực thi và ra quyết định của workflow.** Nó nhận biết khi workflow
   hoàn tất, có thể chủ động sửa hành động nếu cần, và khi thất bại có thể dừng thực thi để chuyển quyền
   kiểm soát lại cho người dùng.
2. **Agent có quyền truy cập nhiều tools để tương tác với hệ thống bên ngoài** — vừa thu thập ngữ cảnh, vừa
   thực hiện hành động — và tự chọn tool phù hợp theo trạng thái hiện tại của workflow, luôn hoạt động trong
   các [[guardrails]] được xác định rõ.

## Ba thành phần nền tảng

Ở dạng nền tảng nhất, một agent gồm: [[model-selection|model]] (năng lực suy luận/ra quyết định),
[[tools]] (hàm/API để hành động), và [[instructions]] (hướng dẫn + guardrail xác định cách hành xử).

Góc nhìn hạ tầng/vận hành mở rộng 3 thành phần này thành [[agent-7-layers|7 layer]] phải cân bằng cùng
một ngân sách latency: Model Hosting, Tools, Memory, Context/Instruction, Data Collector, Harness,
Evaluation.

## Khi nào nên xây dựng agent

Agent phù hợp nhất với các workflow từng khó tự động hóa bằng cách tiếp cận tất định/rule-based:

| Tiêu chí | Ví dụ |
|---|---|
| Ra quyết định phức tạp — phán đoán tinh tế, ngoại lệ, quyết định phụ thuộc ngữ cảnh | Phê duyệt hoàn tiền trong chăm sóc khách hàng |
| Quy tắc khó bảo trì — bộ quy tắc lớn, cập nhật tốn kém/dễ lỗi | Đánh giá bảo mật nhà cung cấp |
| Phụ thuộc nhiều dữ liệu phi cấu trúc — diễn giải ngôn ngữ tự nhiên, trích xuất ý nghĩa từ tài liệu | Xử lý yêu cầu bồi thường bảo hiểm nhà |

Ví dụ minh họa: phân tích gian lận thanh toán — một rules engine hoạt động như danh sách kiểm tra
(đánh dấu theo tiêu chí định sẵn), còn agent giống một điều tra viên dày dạn: đánh giá ngữ cảnh, cân nhắc
các mẫu tinh vi, phát hiện hoạt động đáng ngờ ngay cả khi không vi phạm quy tắc rõ ràng.

Nếu ca sử dụng không đáp ứng các tiêu chí trên, một giải pháp tất định thường đã đủ — không cần agent.

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
