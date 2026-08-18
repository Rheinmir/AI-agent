"""STUB — sandbox này CHƯA cài Claude Agent SDK (`claude-agent-sdk`). Sơ đồ ánh xạ:

  AgentSpec.tools[i]   -> hàm decorate bằng `@tool(name, description, input_schema)` của Claude
                          Agent SDK (kiểu MCP — Model Context Protocol) rồi đăng ký qua
                          `create_sdk_mcp_server(name=..., tools=[...])`, gắn vào
                          `ClaudeAgentOptions(mcp_servers=[...])`. `input_schema` nhận trực tiếp
                          JSON schema (gần giống params_json_schema — bước convert NHẸ hơn hẳn so
                          với langchain_exporter, không cần pydantic).
  AgentSpec.instructions -> `ClaudeAgentOptions(system_prompt=...)`.
  AgentSpec.guardrails (kind=input)
                        -> Claude Agent SDK có hook `PreToolUse`/`can_use_tool` cho phép chặn Ở
                          CẤP TOOL, nhưng KHÔNG có khái niệm input-guardrail chặn TRƯỚC KHI vào
                          agent loop như `@input_guardrail` của Agents SDK — muốn giữ đúng hành vi
                          "chặn sớm, model chính không chạy", cách gần nhất là tự viết 1 lớp kiểm
                          tra TRƯỚC khi gọi `query()`/`ClaudeSDKClient`, y hệt cách harness.py hiện
                          đang gọi guardrail rồi mới gọi Runner.run_sync.
  AgentSpec.hooks       -> Claude Agent SDK có hook system riêng (`PreToolUse`, `PostToolUse`,
                          `Stop`...) — tên khác nhưng Ý TƯỞNG giống `AgentHooks.on_tool_start`/
                          `on_tool_end`, map được khá trực tiếp.

Điền code thật: `pip install claude-agent-sdk`, viết converter tool JSON-schema (đã gần tương
thích, ít việc hơn langchain_exporter), thêm test hermetic trước khi coi là xong.
"""


def build_claude_agent(spec):
    raise NotImplementedError(
        "Chưa cài claude-agent-sdk trong sandbox này — xem sơ đồ ánh xạ ở docstring module này. "
        "Đây là exporter GẦN THẬT NHẤT trong 4 stub (input_schema JSON gần giống params_json_schema "
        "sẵn có) — ưu tiên điền trước nếu cần chạy thử trên Claude Agent SDK."
    )
