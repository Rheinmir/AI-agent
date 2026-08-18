"""Retrieval gate — CÙNG pattern weather_agent/retrieval_gate.py (đọc docstring ở đó cho giải
thích đầy đủ) — quyết định RẺ, temperature=0, TRƯỚC guardrail/model chính: lượt hỏi này có cần
agent tra wiki/cheatsheet đã thu thập sẵn (qua ask_librarian — TOOL DUY NHẤT đọc wiki, xem
agent.py) hay không. Fail-open (retrieve=True) nếu lỗi."""

import json

from agents import Agent, ModelSettings, Runner

from demo_agents.devops_agent.model_provider import get_model

_GATE_PROMPT = (
    "Bạn là bộ gác cổng RẺ cho 1 DevOps knowledge Q&A agent — quyết định lượt hỏi này có cần agent "
    "tra cheatsheet DevOps đã thu thập sẵn hay KHÔNG. Chỉ trả lời ĐÚNG 1 dòng JSON, không thêm chữ "
    "nào khác:\n"
    '{"retrieve": true/false, "reason": "<5 từ>"}\n\n'
    "true nếu câu hỏi hỏi về Kubernetes/container/CI/CD/pattern triển khai/promote môi trường hay "
    "bất kỳ chủ đề kỹ thuật cụ thể nào (kể cả câu tiếp nối ngắn như 'còn canary thì sao'). false "
    "nếu chỉ là lời chào/cảm ơn/xã giao, hoặc câu hỏi hoàn toàn không liên quan chủ đề kỹ thuật nào."
)

_gate_agent = Agent(
    name="DevOps retrieval gate",
    model=get_model(),
    instructions=_GATE_PROMPT,
    model_settings=ModelSettings(temperature=0),
)


async def should_retrieve(question: str) -> tuple[bool, str]:
    """Trả (retrieve?, reason). Fail-open (True, ...) nếu model lỗi/JSON méo."""
    try:
        result = await Runner.run(_gate_agent, question)
        text = (result.final_output or "").strip()
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            return True, "gate không trả JSON — fail-open"
        decision = json.loads(text[start : end + 1])
        return bool(decision.get("retrieve", True)), str(decision.get("reason", ""))
    except Exception as exc:  # noqa: BLE001
        return True, f"gate lỗi ({type(exc).__name__}) — fail-open"
