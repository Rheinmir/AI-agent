"""STUB — sandbox này CHƯA cài `langchain` (không có trong requirements.txt, xem README trước khi
điền code thật, đừng thêm dependency chỉ để làm stub "trông chạy được"). Sơ đồ ánh xạ:

  AgentSpec.tools[i]              -> langchain_core.tools.StructuredTool.from_function(
                                        func=tool_spec.func,
                                        name=tool_spec.name,
                                        description=tool_spec.description,
                                        args_schema=<pydantic model dựng từ params_json_schema>,
                                      )
                                      (StructuredTool cần args_schema kiểu pydantic, không nhận
                                      JSON schema thô — cần 1 bước convert JSON-schema -> pydantic
                                      model, vd qua `pydantic.create_model` hoặc thư viện
                                      `datamodel-code-generator`; ĐÂY LÀ CHỖ "chuyển đổi giữa các
                                      cấu trúc" thật sự khó, không phải copy field 1-1.)
  AgentSpec.instructions           -> ChatPromptTemplate hệ thống (SystemMessage)
  AgentSpec.guardrails (kind=input) -> không có khái niệm input_guardrail native trong
                                      AgentExecutor cũ; LangChain hiện đại khuyến khích chuyển sang
                                      LangGraph để có node kiểm tra trước khi vào vòng chính — xem
                                      langgraph_exporter.py thay vì cố nhét vào đây.
  AgentSpec.hooks                  -> LangChain Callbacks (BaseCallbackHandler.on_tool_start/
                                      on_tool_end/on_llm_start/on_llm_end — tên method GẦN GIỐNG
                                      AgentHooks của Agents SDK nhưng chữ ký tham số khác).

Điền code thật: `pip install langchain langchain-core`, viết converter JSON-schema->pydantic, rồi
thay `raise NotImplementedError` bằng implementation, thêm test hermetic (mock LLM) trước khi coi
là xong.
"""


def build_langchain_agent(spec, llm=None):
    raise NotImplementedError(
        "Chưa cài langchain trong sandbox này — xem sơ đồ ánh xạ ở docstring module này để điền "
        "code thật khi cần. Không giả vờ chạy được khi chưa test qua langchain thật."
    )
