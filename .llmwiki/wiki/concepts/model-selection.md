---
type: concept
title: Chọn model cho agent
tags: [agent, model, cost, latency]
timestamp: 2026-07-27
---

# Chọn model cho agent

Model cung cấp năng lực suy luận và ra quyết định cho một [[agent]]. Các model khác nhau có điểm mạnh và
đánh đổi khác nhau về độ phức tạp tác vụ, độ trễ và chi phí — trong một [[workflow]], có thể dùng nhiều loại
model cho các tác vụ khác nhau (xem [[orchestration]]).

Không phải tác vụ nào cũng cần model thông minh nhất:
- Tác vụ truy xuất đơn giản hoặc phân loại intent → model nhỏ, nhanh hơn.
- Tác vụ khó (ví dụ quyết định có phê duyệt hoàn tiền hay không) → model mạnh hơn.

## Cách làm hiệu quả

Xây dựng prototype agent với model mạnh nhất cho **mọi** tác vụ trước, để thiết lập baseline hiệu năng.
Sau đó thử thay bằng model nhỏ hơn ở từng tác vụ để xem còn đạt kết quả chấp nhận được không. Cách này
tránh giới hạn năng lực agent quá sớm, và giúp chẩn đoán chính xác nơi model nhỏ thành công hoặc thất bại.

## Ba nguyên tắc

1. Thiết lập evals để tạo baseline hiệu năng.
2. Tập trung đạt mục tiêu độ chính xác bằng các model tốt nhất hiện có.
3. Tối ưu chi phí và độ trễ bằng cách thay model lớn bằng model nhỏ hơn khi có thể.

Đây là góc nhìn chọn model theo TÁC VỤ. Góc nhìn chọn model theo HẠ TẦNG (KV cache, VRAM còn lại, so
sánh vendor theo margin) là một bài toán khác — xem [[model-hosting]].

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
