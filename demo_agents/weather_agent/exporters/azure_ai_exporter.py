"""STUB — sandbox này CHƯA cài Azure AI Foundry SDK (`azure-ai-projects`/`azure-ai-agents`). Sơ đồ
ánh xạ (Azure AI Agent Service, kiểu Assistants API — không phải Semantic Kernel, khác framework):

  AgentSpec.name/instructions -> `AgentsClient.create_agent(model=..., name=spec.name,
                                  instructions=spec.instructions)`.
  AgentSpec.tools[i]          -> `FunctionTool` của Azure SDK (`azure.ai.agents.models.FunctionTool`)
                                  — nhận trực tiếp 1 Python `set[Callable]`, SDK TỰ SINH JSON schema
                                  từ type hint + docstring (giống @function_tool bên Agents SDK) —
                                  vì vậy chiều CHUYỂN NGƯỢC (Azure -> spec trung lập) dễ hơn chiều
                                  đang làm (spec -> Azure), có thể bỏ qua params_json_schema có sẵn
                                  và chỉ truyền thẳng spec.tools[i].func vào `FunctionTool({...})`.
  AgentSpec.guardrails         -> Azure AI Agent Service không có input-guardrail runtime built-in
                                  tương đương `@input_guardrail` — cách gần nhất là Azure AI Content
                                  Safety (dịch vụ riêng, chặn theo policy nội dung, KHÔNG PHẢI logic
                                  tuỳ biến như "câu hỏi có đúng phạm vi thời tiết không") — muốn giữ
                                  đúng hành vi hiện tại, vẫn cần tự viết lớp guardrail riêng như
                                  claude_agent_sdk_exporter.py, gọi trước khi tạo run.
  AgentSpec.hooks              -> Không có hook lifecycle native — phải polling `run.status` qua
                                  `AgentsClient.runs.get()` hoặc dùng streaming event handler
                                  (`AgentEventHandler.on_thread_run_step_delta` v.v.) — mô hình
                                  polling/streaming khác hẳn callback trực tiếp của AgentHooks.

Điền code thật: `pip install azure-ai-projects azure-ai-agents azure-identity`, cần thêm
Azure credential/endpoint config (không chỉ API key đơn giản như OpenAI/DeepSeek) — chi phí hạ
tầng cao hơn 3 exporter kia, cân nhắc kỹ trước khi điền nếu chỉ để demo.
"""


def build_azure_agent(spec):
    raise NotImplementedError(
        "Chưa cài Azure AI SDK trong sandbox này — xem sơ đồ ánh xạ ở docstring module này. Guardrail "
        "và hooks không có tương đương native trong Azure AI Agent Service, cần tự viết lại — không "
        "phải chỉ đổi tên field như openai_agents_exporter."
    )
