---
type: concept
title: Orchestration (agent)
tags: [agent, orchestration, single-agent, multi-agent]
timestamp: 2026-07-27
---

# Orchestration (agent)

Sau khi đã có các thành phần nền tảng ([[model-selection]], [[tools]], [[instructions]]), các mẫu
orchestration giúp [[agent]] thực thi [[workflow]] hiệu quả. Khách hàng của OpenAI thường thành công hơn
với cách tiếp cận tăng dần thay vì xây ngay một agent tự chủ hoàn toàn với kiến trúc phức tạp.

Hai nhóm mẫu orchestration:

1. **Hệ thống một agent** — một model duy nhất được trang bị tools và instructions phù hợp, thực thi
   workflow trong một vòng lặp.
2. **Hệ thống đa agent** — việc thực thi workflow được phân tán cho nhiều agent phối hợp với nhau, qua
   [[manager-pattern]] hoặc [[handoff-pattern]].

## Hệ thống một agent và vòng lặp "run"

Một agent duy nhất có thể xử lý nhiều tác vụ bằng cách thêm dần tools, giữ độ phức tạp dễ quản lý và đơn
giản hóa eval/bảo trì. Mọi cách orchestration đều cần khái niệm **"run"** — một vòng lặp cho phép agent hoạt
động đến khi đạt điều kiện thoát. Điều kiện thoát phổ biến: tool call cụ thể, một đầu ra có cấu trúc nhất định,
lỗi, hoặc đạt số lượt tối đa.

Trong OpenAI Agents SDK, `Runner.run()` lặp qua LLM cho đến khi:
1. Một final-output tool được gọi (định nghĩa bởi kiểu đầu ra cụ thể), hoặc
2. Model trả về phản hồi không có tool call nào (tin nhắn trực tiếp cho người dùng).

Trong hệ đa agent, có thể có chuỗi tool calls và handoffs giữa các agent, nhưng vẫn cho phép model chạy
nhiều bước đến khi đạt điều kiện thoát.

## Khi nào nên tạo nhiều agent

Khuyến nghị chung: **trước tiên tối đa hóa năng lực của một agent duy nhất**. Nhiều agent tạo sự tách biệt
khái niệm trực quan nhưng cũng thêm độ phức tạp/overhead — một agent có tools thường là đủ.

Hai dấu hiệu nên tách agent:

| Dấu hiệu | Mô tả |
|---|---|
| **Logic phức tạp** | Prompt chứa nhiều nhánh if-then-else, prompt templates khó mở rộng → chia từng đoạn logic cho agent riêng |
| **Quá tải tools** | Không chỉ số lượng mà cả mức chồng lấn giữa tools — một số hệ quản tốt >15 tools rõ ràng, số khác khó với <10 tools chồng lấn. Chỉ tách agent nếu cải thiện tên/tham số/mô tả tool vẫn không đủ |

## Đồ thị declarative vs non-declarative

Một số framework mang tính **declarative**: developer phải định nghĩa trước mọi nhánh, vòng lặp, điều kiện
qua đồ thị nút (agent) và cạnh (handoff tất định/động) — trực quan nhưng cồng kềnh khi workflow phức tạp,
thường cần học domain-specific language riêng.

OpenAI Agents SDK ưu tiên **code-first**: developer biểu đạt trực tiếp logic workflow bằng cấu trúc lập trình
quen thuộc, không cần định nghĩa trước toàn bộ đồ thị — linh hoạt và dễ thích ứng hơn.

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
