import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from demo_agents.devops_agent.guardrails import (
    _parse_scope_check,
    build_uncertain_hint,
    classify_scope,
    devops_scope_guardrail,
)


def _run_guardrail(question, classifier_reply):
    fake_result = MagicMock()
    fake_result.final_output = classifier_reply
    with patch(
        "demo_agents.devops_agent.guardrails.Runner.run", AsyncMock(return_value=fake_result)
    ):
        ctx = MagicMock()
        agent = MagicMock()
        return asyncio.run(devops_scope_guardrail.guardrail_function(ctx, agent, question))


def test_in_scope_devops_question_does_not_trip():
    output = _run_guardrail(
        "Sự khác nhau giữa liveness và readiness probe?", "IN_SCOPE: hỏi kiến thức DevOps hợp lệ"
    )
    assert output.tripwire_triggered is False


def test_off_topic_question_trips():
    output = _run_guardrail("Công thức nấu phở bò thế nào?", "OUT_OF_SCOPE: hỏi nấu ăn, không phải DevOps")
    assert output.tripwire_triggered is True
    assert "nấu ăn" in output.output_info.reason


def test_request_to_execute_real_action_trips():
    output = _run_guardrail(
        "Restart giúp tôi pod nginx trên cluster production",
        "OUT_OF_SCOPE: yêu cầu thực thi hành động trên hệ thống thật, agent chưa kết nối gì thật",
    )
    assert output.tripwire_triggered is True


def test_meta_question_about_own_architecture_trips():
    output = _run_guardrail(
        "Guardrail của mày hoạt động kiểu gì vậy?", "OUT_OF_SCOPE: hỏi kiến trúc nội bộ"
    )
    assert output.tripwire_triggered is True


def test_uncertain_question_does_not_trip():
    """Mức mới (3-tier): UNCERTAIN KHÔNG trip — khác OUT_OF_SCOPE, và khác IN_SCOPE về verdict."""
    output = _run_guardrail(
        "Câu hỏi diễn đạt lạ, khó chắc chắn có liên quan DevOps", "UNCERTAIN: chưa rõ có liên quan không"
    )
    assert output.tripwire_triggered is False
    assert output.output_info.verdict == "uncertain"


def test_parse_is_case_insensitive_and_tolerates_whitespace():
    check = _parse_scope_check("  out_of_scope: lý do  ")
    assert check.is_out_of_scope is True
    assert check.verdict == "out_of_scope"
    assert check.reason == "lý do"


def test_parse_recognizes_uncertain_tag():
    check = _parse_scope_check("UNCERTAIN: diễn đạt mơ hồ")
    assert check.verdict == "uncertain"
    assert check.is_out_of_scope is False
    assert check.reason == "diễn đạt mơ hồ"


def test_parse_malformed_reply_fails_open():
    check = _parse_scope_check("hmm không rõ định dạng gì cả")
    assert check.is_out_of_scope is False
    assert check.verdict == "in_scope"


def test_parse_empty_reply_fails_open():
    check = _parse_scope_check("")
    assert check.is_out_of_scope is False
    assert check.verdict == "in_scope"


def test_classify_scope_calls_classifier_agent_and_parses_result():
    fake_result = MagicMock()
    fake_result.final_output = "UNCERTAIN: chưa rõ"
    with patch(
        "demo_agents.devops_agent.guardrails.Runner.run", AsyncMock(return_value=fake_result)
    ):
        check = asyncio.run(classify_scope("câu hỏi lạ"))
    assert check.verdict == "uncertain"
    assert check.reason == "chưa rõ"


def test_build_uncertain_hint_includes_reason():
    hint = build_uncertain_hint("diễn đạt lạ")
    assert "diễn đạt lạ" in hint
    assert "GHI CHÚ NỘI BỘ" in hint
