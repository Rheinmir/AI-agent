---
type: concept
title: Handoff pattern (mẫu phi tập trung)
tags: [agent, multi-agent, orchestration, handoff]
timestamp: 2026-07-27
---

# Handoff pattern (mẫu phi tập trung)

Mẫu [[orchestration]] đa agent thứ hai. Nhiều agent hoạt động **ngang hàng**, handoff tác vụ cho nhau dựa
trên chuyên môn của từng agent — khác [[manager-pattern]] vốn có một manager trung tâm giữ quyền kiểm
soát.

**Handoff** là quá trình chuyển giao một chiều cho phép một agent ủy quyền cho agent khác. Trong OpenAI
Agents SDK, handoff là một loại tool/function: nếu agent gọi hàm handoff, hệ thống lập tức bắt đầu thực thi
trên agent mới được chuyển giao, đồng thời chuyển cả trạng thái hội thoại mới nhất.

Mô hình hóa như đồ thị: agent là nút, **cạnh biểu thị handoffs** chuyển việc thực thi giữa các agent.

Lựa chọn tối ưu khi không cần một agent duy nhất giữ quyền kiểm soát/tổng hợp trung tâm — mỗi agent có
thể tiếp quản việc thực thi và tương tác trực tiếp với người dùng khi cần. Đặc biệt hiệu quả cho phân loại
hội thoại (triage) hoặc khi muốn agent chuyên biệt tiếp quản hoàn toàn một số tác vụ.

Ví dụ điển hình: một `triage_agent` làm điểm tiếp xúc đầu tiên, `handoffs=[technical_support_agent,
sales_assistant_agent, order_management_agent]` — nhận input về đơn hàng, triage_agent gọi handoff tới
`order_management_agent` và chuyển quyền kiểm soát. Tùy chọn có thể trang bị handoff quay lại agent ban
đầu, cho phép chuyển quyền kiểm soát lần nữa nếu cần.

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
