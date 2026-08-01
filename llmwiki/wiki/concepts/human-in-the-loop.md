---
type: concept
title: Can thiệp của con người (human-in-the-loop)
tags: [agent, guardrails, human-in-the-loop]
timestamp: 2026-07-27
---

# Can thiệp của con người (human-in-the-loop)

Một lớp bảo vệ then chốt bên cạnh [[guardrails]] tự động, giúp cải thiện hiệu năng thực tế của [[agent]] mà
không làm giảm trải nghiệm người dùng. Đặc biệt quan trọng ở giai đoạn đầu triển khai: giúp nhận diện thất
bại, phát hiện edge case, và xây dựng chu kỳ eval vững chắc.

Cơ chế này cho phép agent chuyển quyền kiểm soát êm ái khi không thể hoàn thành tác vụ — trong chăm sóc
khách hàng nghĩa là chuyển vấn đề cho nhân viên; với coding agent nghĩa là trả quyền kiểm soát lại cho
người dùng.

## Hai trigger chính

1. **Vượt ngưỡng thất bại** — đặt giới hạn số lần retry hoặc hành động của agent; vượt giới hạn (ví dụ nhiều
   lần không hiểu intent khách hàng) → chuyển cho con người.
2. **Hành động rủi ro cao** — hành động nhạy cảm, không thể đảo ngược hoặc hệ quả lớn (hủy đơn hàng, phê
   duyệt hoàn tiền lớn, thực hiện thanh toán) nên kích hoạt giám sát con người cho đến khi độ tin cậy của
   agent tăng lên. Liên quan trực tiếp tới mức rủi ro tool trong [[guardrails]] (bảo vệ tools).

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
