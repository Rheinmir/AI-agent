"""Exporters — mỗi module nhận 1 `agent_spec.AgentSpec` trung lập và dựng ra agent CHẠY ĐƯỢC trên
1 framework cụ thể. `openai_agents_exporter` chạy thật (SDK đang dùng). Các exporter khác
(langchain/langgraph/claude_agent_sdk/azure_ai) là STUB — sơ đồ ánh xạ rõ ràng, raise
NotImplementedError vì sandbox này chưa cài SDK tương ứng, không giả vờ chạy được khi chưa test
thật (fail loudly, không fail âm thầm)."""
