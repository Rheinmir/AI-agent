---
type: entity
title: OpenAI Agents SDK
tags: [sdk, openai, agent, python]
timestamp: 2026-07-27
---

# OpenAI Agents SDK

Thư viện code-first của [[openai]] để xây dựng và điều phối [[agent]], dùng làm ví dụ minh họa xuyên suốt
tài liệu "Hướng dẫn xây dựng Agent thực tế". Các khái niệm cốt lõi trong hướng dẫn được ánh xạ trực tiếp
vào SDK:

- `Agent(name=..., instructions=..., tools=[...])` — định nghĩa agent với [[model-selection|model]],
  [[instructions]], và [[tools]].
- `@function_tool` — decorator biến một hàm Python thành tool cho agent.
- `Runner.run(agent, input)` — khởi chạy vòng lặp "run" của [[orchestration]], lặp đến khi có final-output
  tool call hoặc phản hồi không kèm tool call.
- `<agent>.as_tool(tool_name=..., tool_description=...)` — biến một agent thành tool cho agent khác, dùng
  trong [[manager-pattern]].
- `handoffs=[...]` trên `Agent(...)` — cơ chế handoff dùng trong [[handoff-pattern]].
- `@input_guardrail`, `Guardrail(guardrail_function=...)`, `GuardrailFunctionOutput`,
  `GuardrailTripwireTriggered` — cơ chế [[guardrails]] hạng nhất, chạy theo mô hình optimistic execution.

SDK ưu tiên cách tiếp cận **code-first, không cần đồ thị declarative** — developer biểu đạt logic workflow
trực tiếp bằng cấu trúc lập trình quen thuộc thay vì định nghĩa trước toàn bộ đồ thị nút/cạnh.

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]]
