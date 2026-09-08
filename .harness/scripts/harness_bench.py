#!/usr/bin/env python3
"""harness_bench.py — benchmark NỘI BỘ đo chất lượng của HARNESS (demo_agents/weather_agent/
harness.py), KHÔNG đo model. Cùng phương pháp luận với Harness-Bench (arXiv:2605.27922, xem
wiki/log.md entry "harness-bench-research" — user hỏi có benchmark nào cho harness không, tìm ra
đúng paper này rồi xin giữ pattern của nó thành 1 file):

    TaskScore = Security × Completion × Process
    Process   = mean(Robustness, ToolUse, Consistency)

Mỗi thành phần chuẩn hoá về [0,1] trước khi nhân, kết quả cuối scale 0-100.

KHÁC Harness-Bench (bản gốc so sánh 6 harness × 8 model backend × 106 task = 5088 trajectory, ra
con số "23.8 điểm" là khoảng cách giữa harness tốt nhất/tệ nhất TRÊN HỆ THỐNG CỦA HỌ): project này
chỉ có ĐÚNG 1 harness cho weather_agent, không có harness thay thế nào để so sánh chéo — số 23.8
của paper gốc KHÔNG áp dụng/mượn được cho project này. Benchmark này đo TUYỆT ĐỐI 5 chiều của CHÍNH
harness.py hiện tại (không có baseline "harness khác" để so sánh tương đối) — dùng để theo dõi
harness có TỆ ĐI hay TỐT LÊN qua các lần sửa, không phải để so bì với con số của paper khác.

5 chiều điểm (giữ đúng định nghĩa gốc của Harness-Bench, diễn giải lại cho ĐÚNG những gì harness.py
THẬT SỰ làm — không bịa tiêu chí không áp dụng được cho project này):

- Security   : guardrail 3 mức (guardrails.py::classify_scope) có chặn ĐÚNG câu ngoài phạm vi VÀ
               KHÔNG chặn nhầm câu trong phạm vi — cổng NHỊ PHÂN, sai 1 trong 2 chiều = 0 (giữ đúng
               ngữ nghĩa "binary gate, zeroed if violated" của Harness-Bench). Gọi model THẬT (2 lời
               gọi rẻ).
- Completion : agent có trả lời ĐÚNG cho câu hỏi hợp lệ hay không — kiểm bằng keyword assert tất
               định (không dùng LLM judge, khác wikieval.py vốn đã có judge riêng để CHẤM VĂN
               PHONG câu trả lời — ở đây chỉ đo harness có để lọt câu trả lời SAI HẲN chủ đề hay
               không). Tái dùng CÙNG lời gọi model với Security (không gọi thêm), giữ benchmark rẻ.
- Robustness : retry ĐÚNG khi lỗi tạm thời (ConnectionError) rồi thành công + dừng ĐÚNG (không
               nuốt lỗi, không lặp vô hạn) khi vượt max_turns — mock Runner.run, KHÔNG gọi mạng
               thật (hành vi lỗi mạng không tất định để trigger sống một cách đáng tin cậy).
- ToolUse    : retrieval gate có ẩn ĐÚNG tool tra dữ liệu đã thu thập (get_city_note/ask_librarian)
               khỏi agent khi KHÔNG cần tra cứu hay không — mock should_retrieve, kiểm tools thật
               được đưa vào Runner.run_streamed.
- Consistency: fast-path tất định (greeting, không qua model) có trả NGUYÊN VĂN giống hệt nhau qua
               nhiều lần gọi liên tiếp hay không — chạy N=3 lần, so sánh byte-for-byte.

Chạy: python3 harness/scripts/harness_bench.py [--json]

Cần DEEPSEEK_API_KEY hoặc OPENAI_API_KEY cho 2 case Security/Completion (gọi model thật, 2 lời gọi
ngắn/rẻ) — Robustness/ToolUse/Consistency hoàn toàn mock, không cần key, không tốn API. KHÔNG chạy
trong CI (cùng kỷ luật "không tự động chạy agent LIVE trong CI" đã áp cho wikieval.py — xem comment
trong harness/scripts/wikieval.py — chạy tay khi cần theo dõi harness qua thời gian)."""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Chạy trực tiếp `python3 harness/scripts/harness_bench.py` (không phải `-m`, cùng quy ước
# monolith_agent_deploy_converter.py) — cần tự thêm REPO ROOT vào sys.path để import được
# demo_agents.* (pytest tự làm việc này qua rootdir insertion, script trần thì không).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents.exceptions import MaxTurnsExceeded

from demo_agents.weather_agent import agent as agent_module
from demo_agents.weather_agent.guardrails import OUT_OF_SCOPE_MESSAGE, ScopeCheck
from demo_agents.weather_agent.harness import (
    _RETRIEVAL_TOOL_NAMES,
    run_with_harness,
    run_with_harness_streamed,
)
from demo_agents.weather_agent.model_provider import has_any_key

_IN_SCOPE = ScopeCheck(verdict="in_scope", reason="harness_bench")


async def _collect(agen):
    return [item async for item in agen]


async def _security_and_completion():
    """2 lời gọi model THẬT dùng chung cho cả Security lẫn Completion — giữ benchmark rẻ."""
    oos_result = await run_with_harness(
        agent_module.weather_agent, "1 + 1 bằng mấy?", session=None, session_id="harness-bench-oos"
    )
    blocked_correctly = oos_result.final_output == OUT_OF_SCOPE_MESSAGE

    inscope_result = await run_with_harness(
        agent_module.weather_agent, "Thời tiết ở Hà Nội thế nào?", session=None, session_id="harness-bench-inscope"
    )
    not_falsely_blocked = inscope_result.final_output != OUT_OF_SCOPE_MESSAGE

    security_pass = blocked_correctly and not_falsely_blocked
    security = (
        1.0 if security_pass else 0.0,
        f"chặn đúng câu ngoài phạm vi={blocked_correctly}, không chặn nhầm câu trong phạm vi={not_falsely_blocked}",
    )

    text = inscope_result.final_output.lower()
    completion_pass = "hà nội" in text or "ha noi" in text
    completion = (
        1.0 if completion_pass else 0.0,
        f"câu trả lời có nhắc đúng thành phố được hỏi (Hà Nội)={completion_pass}",
    )
    return security, completion


def _robustness():
    # agent=MagicMock() (không phải agent thật) — agent.name không phải string thật, phải mock
    # log_event luôn (khác _security_and_completion/_consistency dùng agent THẬT, cứ để ghi log
    # thật, cùng quy ước autouse fixture "_no_real_monitoring_writes" trong test_harness.py).
    checks = []
    with patch("demo_agents.weather_agent.harness.asyncio.sleep", new_callable=AsyncMock), patch(
        "demo_agents.weather_agent.harness.log_event"
    ), patch("demo_agents.weather_agent.harness.classify_scope", new_callable=AsyncMock, return_value=_IN_SCOPE), patch(
        "demo_agents.weather_agent.harness.Runner.run", new_callable=AsyncMock
    ) as mock_run:
        mock_run.side_effect = [ConnectionError("timeout"), "ok"]
        result = asyncio.run(run_with_harness(agent=MagicMock(), question="q", session=MagicMock()))
        checks.append(("retry-rồi-thành-công", result == "ok" and mock_run.call_count == 2))

    with patch("demo_agents.weather_agent.harness.asyncio.sleep", new_callable=AsyncMock), patch(
        "demo_agents.weather_agent.harness.log_event"
    ), patch("demo_agents.weather_agent.harness.classify_scope", new_callable=AsyncMock, return_value=_IN_SCOPE), patch(
        "demo_agents.weather_agent.harness.Runner.run", new_callable=AsyncMock
    ) as mock_run:
        mock_run.side_effect = MaxTurnsExceeded("too many")
        raised = False
        try:
            asyncio.run(run_with_harness(agent=MagicMock(), question="q", session=MagicMock()))
        except MaxTurnsExceeded:
            raised = True
        checks.append(("max_turns-không-bị-nuốt", raised and mock_run.call_count == 1))

    passed = sum(1 for _, ok in checks if ok)
    detail = ", ".join(f"{name}={ok}" for name, ok in checks)
    return passed / len(checks), detail


def _tooluse():
    class _FakeStreamResult:
        final_output = "ok"

        async def stream_events(self):
            return
            yield  # pragma: no cover - generator rỗng, không có event nào để phát

    with patch("demo_agents.weather_agent.harness.classify_scope", new_callable=AsyncMock, return_value=_IN_SCOPE), patch(
        "demo_agents.weather_agent.harness.should_retrieve",
        new_callable=AsyncMock,
        return_value=(False, "harness_bench: không cần tra cứu"),
    ), patch("demo_agents.weather_agent.harness.Runner.run_streamed") as mock_run_streamed:
        mock_run_streamed.return_value = _FakeStreamResult()
        asyncio.run(_collect(run_with_harness_streamed(agent_module.weather_agent, "q", session=MagicMock())))
        called_agent = mock_run_streamed.call_args[0][0]
        tool_names = {getattr(t, "name", None) for t in called_agent.tools}
        hidden_correctly = tool_names.isdisjoint(_RETRIEVAL_TOOL_NAMES)

    return (
        1.0 if hidden_correctly else 0.0,
        f"tool tra cứu bị ẩn đúng khi retrieve=False: {hidden_correctly} (tools còn lại: {sorted(tool_names)})",
    )


def _consistency():
    outputs = [
        asyncio.run(_collect(run_with_harness_streamed(agent_module.weather_agent, "Cảm ơn nhé!", session=MagicMock())))
        for _ in range(3)
    ]
    all_same = all(o == outputs[0] for o in outputs)
    return 1.0 if all_same else 0.0, f"greeting fast-path giống hệt nhau qua {len(outputs)} lần gọi: {all_same}"


def compute_task_score(security, completion, robustness, tooluse, consistency):
    process = (robustness + tooluse + consistency) / 3
    return security * completion * process * 100


def main():
    parser = argparse.ArgumentParser(description="Benchmark nội bộ đo chất lượng harness weather_agent.")
    parser.add_argument("--json", action="store_true", help="In kết quả dạng JSON thay vì bảng text.")
    args = parser.parse_args()

    if not has_any_key():
        print(
            "Lỗi: thiếu DEEPSEEK_API_KEY/OPENAI_API_KEY — dimension Security/Completion cần gọi "
            "model thật. Xem demo_agents/weather_agent/.env.example.",
            file=sys.stderr,
        )
        return 1

    (security_score, security_detail), (completion_score, completion_detail) = asyncio.run(
        _security_and_completion()
    )
    robustness_score, robustness_detail = _robustness()
    tooluse_score, tooluse_detail = _tooluse()
    consistency_score, consistency_detail = _consistency()

    task_score = compute_task_score(
        security_score, completion_score, robustness_score, tooluse_score, consistency_score
    )

    dimensions = {
        "security": {"score": security_score, "detail": security_detail},
        "completion": {"score": completion_score, "detail": completion_detail},
        "robustness": {"score": robustness_score, "detail": robustness_detail},
        "tool_use": {"score": tooluse_score, "detail": tooluse_detail},
        "consistency": {"score": consistency_score, "detail": consistency_detail},
    }
    report = {"agent": "weather_agent", "dimensions": dimensions, "task_score": round(task_score, 1)}

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("harness_bench — demo_agents/weather_agent/harness.py\n")
        for name, d in dimensions.items():
            print(f"  {name:12s} {d['score']:.2f}  — {d['detail']}")
        print("\nTaskScore = Security × Completion × mean(Robustness, ToolUse, Consistency) × 100")
        print(f"          = {report['task_score']}/100")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
