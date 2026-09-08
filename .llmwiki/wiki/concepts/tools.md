---
type: concept
title: Tools (cho agent)
tags: [agent, tools, api]
timestamp: 2026-07-27
---

# Tools (cho agent)

Tools mở rộng năng lực của [[agent]] bằng cách dùng API từ các ứng dụng hoặc hệ thống nền. Với hệ thống cũ
không có API, agent có thể dùng computer-use models để tương tác trực tiếp với ứng dụng/hệ thống qua giao
diện web và ứng dụng — giống như con người.

Mỗi tool nên có một định nghĩa chuẩn hóa, cho phép quan hệ linh hoạt nhiều-nhiều giữa tools và agents.
Tools được tài liệu hóa tốt, kiểm thử kỹ, tái sử dụng được sẽ dễ khám phá hơn, đơn giản hóa quản lý phiên
bản và tránh định nghĩa trùng lặp.

## Ba loại tools

| Loại | Vai trò | Ví dụ |
|---|---|---|
| **Data** | Giúp agent truy xuất ngữ cảnh/thông tin cần thiết để thực thi workflow | Truy vấn cơ sở dữ liệu giao dịch/CRM, đọc PDF, tìm kiếm web |
| **Action** | Giúp agent tương tác với hệ thống để thực hiện hành động | Gửi email/tin nhắn, cập nhật bản ghi CRM, chuyển ticket cho con người |
| **Orchestration** | Bản thân agent đóng vai trò tool cho agent khác | Refund agent, Research agent, Writing agent — xem [[manager-pattern]] |

Ví dụ (OpenAI Agents SDK) trang bị cho một agent cả `WebSearchTool()` (data) lẫn một `@function_tool`
tùy chỉnh để lưu kết quả (action).

Khi số lượng tools cần thiết tăng lên, cân nhắc chia tác vụ cho nhiều agent — xem [[orchestration]].

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
