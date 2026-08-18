"""STUB — sandbox này CHƯA cài `langgraph`. Sơ đồ ánh xạ — khác hẳn openai-agents/langchain vì
LangGraph là mô hình GRAPH/STATE-MACHINE, không phải "1 agent + danh sách tool" phẳng:

  AgentSpec  -> 1 StateGraph với tối thiểu 3 node:
                  "guardrail"  : chạy AgentSpec.guardrails (kind=input) trước tiên — nếu trip,
                                 edge có điều kiện đi thẳng tới node "refuse" (trả
                                 OUT_OF_SCOPE_MESSAGE tĩnh), bỏ qua hoàn toàn node "agent".
                  "agent"      : node gọi LLM + AgentSpec.tools (bind_tools), tương đương vòng lặp
                                 think-act-observe của Runner.run_sync bên openai-agents.
                  "tools"      : ToolNode(spec.tools đã convert — xem cách convert tool ở
                                 langchain_exporter.py, LangGraph dùng chung kiểu Tool với
                                 LangChain) — nối vòng lặp lại "agent" qua conditional edge
                                 (tools_condition) tới khi model không còn gọi tool nữa.
  AgentSpec.hooks -> KHÔNG map trực tiếp — LangGraph dùng `.stream()`/`.astream_events()` để lấy
                     sự kiện theo từng bước graph, kiến trúc "quan sát" khác hẳn callback-hooks —
                     cần viết lại logic monitoring.py để đọc event stream thay vì implement hooks.
  Harness (harness.py: max_turns, retry)
                  -> LangGraph có `recursion_limit` tương đương max_turns; retry cần tự viết node
                     hoặc dùng `RunnableRetry` bọc quanh node "agent".

Điền code thật: `pip install langgraph`, dựng StateGraph theo sơ đồ trên, thêm test hermetic (mock
model) trước khi coi là xong. Đây là exporter phức tạp nhất trong 4 stub vì đổi hẳn PARADIGM (graph
thay vì vòng lặp phẳng), không chỉ đổi tên field.
"""


def build_langgraph_agent(spec, llm=None):
    raise NotImplementedError(
        "Chưa cài langgraph trong sandbox này — xem sơ đồ ánh xạ ở docstring module này. LangGraph "
        "đổi cả paradigm (graph/state-machine) nên không thể chuyển đổi máy móc field-theo-field "
        "như openai_agents_exporter — cần thiết kế lại luồng theo node/edge trước khi viết code."
    )
