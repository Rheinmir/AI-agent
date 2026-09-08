---
type: concept
title: Manager pattern (agents như tools)
tags: [agent, multi-agent, orchestration]
timestamp: 2026-07-27
---

# Manager pattern (agents như tools)

Một trong hai mẫu [[orchestration]] đa agent phổ biến. Một agent **"manager"** trung tâm điều phối nhiều
agent chuyên biệt qua **tool calls**, mỗi agent xử lý một tác vụ hoặc miền cụ thể — tương ứng loại
tool "Orchestration" trong [[tools]].

Manager thông minh giao tác vụ cho đúng agent vào đúng thời điểm và tổng hợp kết quả thành một tương
tác thống nhất, không để mất ngữ cảnh hay quyền kiểm soát — đảm bảo trải nghiệm người dùng mượt mà
trong khi vẫn có năng lực chuyên biệt sẵn sàng khi cần.

Mô hình hóa như đồ thị: agent là nút, **cạnh biểu thị tool calls** (khác [[handoff-pattern]] nơi cạnh biểu thị
handoffs).

Lý tưởng cho workflow mà bạn chỉ muốn **một agent duy nhất kiểm soát việc thực thi và có quyền truy cập
người dùng** — ví dụ: một manager_agent nhận yêu cầu "dịch 'hello' sang Tây Ban Nha, Pháp và Ý", rồi gọi các
tool `spanish_agent.as_tool(...)`, `french_agent.as_tool(...)`, `italian_agent.as_tool(...)` tương ứng.

Trong OpenAI Agents SDK, một agent chuyên biệt được biến thành tool cho manager bằng
`<agent>.as_tool(tool_name=..., tool_description=...)`.

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
