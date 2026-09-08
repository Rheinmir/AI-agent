---
type: concept
title: Guardrails
tags: [agent, safety, guardrails, security]
timestamp: 2026-07-27
---

# Guardrails

Guardrails được thiết kế tốt giúp quản lý rủi ro về quyền riêng tư dữ liệu (ví dụ ngăn rò rỉ system prompt)
hoặc rủi ro uy tín (ví dụ đảm bảo hành vi model phù hợp thương hiệu). Là thành phần then chốt của mọi triển
khai [[agent]] dựa trên LLM, nhưng cần đi kèm giao thức xác thực/phân quyền vững chắc, kiểm soát truy cập
nghiêm ngặt và các biện pháp bảo mật phần mềm tiêu chuẩn — guardrail không thay thế các lớp bảo mật đó.

**Nguyên tắc:** xem guardrails như phòng thủ **nhiều lớp** — một guardrail đơn lẻ khó bảo vệ đủ, nhưng
nhiều guardrail chuyên biệt kết hợp (LLM-based, rule-based như regex, OpenAI moderation API) sẽ tạo ra
agent bền vững hơn.

## Các loại guardrails

| Loại | Vai trò | Ví dụ |
|---|---|---|
| Bộ phân loại mức liên quan | Đánh dấu truy vấn ngoài chủ đề | "Tòa Empire State cao bao nhiêu?" hỏi một call-center agent |
| Bộ phân loại an toàn | Phát hiện input không an toàn (jailbreak/prompt injection) | Yêu cầu agent "nhập vai" để lộ system instructions |
| Bộ lọc PII | Ngăn lộ thông tin định danh cá nhân qua kiểm tra output | — |
| Moderation | Đánh dấu nội dung độc hại/không phù hợp (thù ghét, quấy rối, bạo lực) | — |
| Bảo vệ tools | Gán mức rủi ro (thấp/trung bình/cao) cho từng tool dựa trên read-only vs write, khả năng đảo ngược, quyền tài khoản, tác động tài chính | Tạm dừng kiểm tra guardrail hoặc chuyển người trước khi thực thi hàm rủi ro cao |
| Bảo vệ dựa trên quy tắc | Biện pháp tất định đơn giản: blocklist, giới hạn độ dài input, regex | Ngăn SQL injection, thuật ngữ bị cấm |
| Xác thực output | Đảm bảo phản hồi phù hợp giá trị thương hiệu qua prompt engineering + kiểm tra nội dung | — |

## Xây dựng guardrails — heuristic

1. Tập trung vào quyền riêng tư dữ liệu và an toàn nội dung trước.
2. Thêm guardrail mới dựa trên edge case và lỗi thực tế gặp phải.
3. Tối ưu cả bảo mật lẫn trải nghiệm người dùng, tinh chỉnh guardrail khi agent phát triển.

## Optimistic execution (OpenAI Agents SDK)

Agents SDK xem guardrails là khái niệm hạng nhất, mặc định dựa vào **optimistic execution**: agent chính
chủ động tạo output trong khi guardrail chạy đồng thời, và raise exception
(`GuardrailTripwireTriggered`/`InputGuardrailTripwireTriggered`) nếu ràng buộc bị vi phạm. Guardrail có thể
triển khai dưới dạng function hoặc agent riêng (ví dụ một `churn_detection_agent` với
`output_type=ChurnDetectionOutput`, gắn vào `input_guardrails=[...]` của agent chính) để thực thi chính sách
như ngăn jailbreak, xác thực mức liên quan, lọc từ khóa, blocklist, phân loại an toàn.

Xem thêm [[human-in-the-loop]] — lớp bảo vệ bổ sung khi guardrail tự động chưa đủ.

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
