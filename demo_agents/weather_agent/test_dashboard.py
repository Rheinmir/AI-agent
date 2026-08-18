import json
import time
from unittest.mock import patch

from demo_agents.weather_agent import dashboard, monitoring


def test_monitor_page_empty_state_renders_without_error(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"), \
         patch.object(dashboard, "_EVAL_BASELINE_PATH", tmp_path / "missing.json"):
        html_out = dashboard.render_monitor_page()
        assert "Monitor" in html_out
        assert "Chưa có lượt gọi tool nào" in html_out
        assert "Chưa có sự kiện nào" in html_out


def test_monitor_page_reflects_real_events(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"), \
         patch.object(dashboard, "_EVAL_BASELINE_PATH", tmp_path / "missing.json"):
        monitoring.log_event("Weather agent", "agent_start")
        monitoring.log_event("Weather agent", "tool_start", {"tool": "get_weather"})
        monitoring.log_event("Weather agent", "tool_end", {"tool": "get_weather", "result_preview": "ok"})
        monitoring.log_event("Weather agent", "harness_guardrail_tripped")
        html_out = dashboard.render_monitor_page()
        assert "get_weather" in html_out
        assert ">1<" in html_out  # guardrail-trip count card shows 1


def test_monitor_page_escapes_untrusted_detail_text(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"), \
         patch.object(dashboard, "_EVAL_BASELINE_PATH", tmp_path / "missing.json"):
        monitoring.log_event("Weather agent", "tool_end", {"tool": "<script>x</script>"})
        html_out = dashboard.render_monitor_page()
        assert "<script>x</script>" not in html_out
        assert "&lt;script&gt;" in html_out


def test_evaluate_page_missing_baseline_shows_placeholder(tmp_path):
    with patch.object(dashboard, "_EVAL_BASELINE_PATH", tmp_path / "missing.json"):
        html_out = dashboard.render_evaluate_page()
        assert "eval-baseline.json" in html_out
        assert "0/0" in html_out


def test_evaluate_page_renders_pass_and_fail_pills(tmp_path):
    baseline = {
        "generated_at": "2026-08-04",
        "summary": {"goldens": 2, "decided": 2, "passed": 1},
        "goldens": {
            "golden-a": {"pass": True, "decided_by": "tier1-asserts", "asserts": ["icontains:ok"]},
            "golden-b": {"pass": False, "decided_by": "tier1-asserts", "asserts": ["equals:nope"]},
        },
    }
    path = tmp_path / "eval-baseline.json"
    path.write_text(json.dumps(baseline), encoding="utf-8")
    with patch.object(dashboard, "_EVAL_BASELINE_PATH", path):
        html_out = dashboard.render_evaluate_page()
        assert "golden-a" in html_out
        assert "golden-b" in html_out
        assert html_out.count('class="pill pass"') == 1
        assert html_out.count('class="pill fail"') == 1
        assert "1/2" in html_out


def test_monitor_page_shows_latency_and_error_rate_cards(tmp_path):
    # ts phải GẦN với thời gian thật (render_monitor_page tự prune sự kiện >30 ngày mỗi lần tải) —
    # dùng epoch nhỏ (100.0) sẽ bị prune trước khi kịp render, không phải lỗi code.
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"), \
         patch.object(dashboard, "_EVAL_BASELINE_PATH", tmp_path / "missing.json"):
        now = time.time()
        con = monitoring._connect()
        con.execute(
            "INSERT INTO events (ts, agent_name, event, detail, session_id, run_id) VALUES (?, 'A', 'agent_start', '{}', 's1', 'r1')",
            (now - 2,),
        )
        con.execute(
            "INSERT INTO events (ts, agent_name, event, detail, session_id, run_id) VALUES (?, 'A', 'agent_end', '{}', 's1', 'r1')",
            (now,),
        )
        con.commit()
        con.close()
        html_out = dashboard.render_monitor_page()
        assert "Latency TB / lượt" in html_out
        assert "2.0s" in html_out
        assert "Lỗi trong 20 lượt gần nhất" in html_out


def test_monitor_page_flags_high_error_rate_with_warn_card(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"), \
         patch.object(dashboard, "_EVAL_BASELINE_PATH", tmp_path / "missing.json"):
        for _ in range(3):
            monitoring.log_event("A", "harness_guardrail_tripped")
        html_out = dashboard.render_monitor_page()
        assert 'class="card warn"' in html_out


def test_monitor_page_shows_session_breakdown(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"), \
         patch.object(dashboard, "_EVAL_BASELINE_PATH", tmp_path / "missing.json"):
        monitoring.log_event("A", "agent_start", session_id="my-session-1", run_id="r1")
        html_out = dashboard.render_monitor_page()
        assert "my-session-1" in html_out


def test_monitor_page_prunes_old_events(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"), \
         patch.object(dashboard, "_EVAL_BASELINE_PATH", tmp_path / "missing.json"):
        con = monitoring._connect()
        old_ts = time.time() - 40 * 86400
        con.execute(
            "INSERT INTO events (ts, agent_name, event, detail) VALUES (?, 'A', 'agent_start', '{}')",
            (old_ts,),
        )
        con.commit()
        con.close()
        dashboard.render_monitor_page()
        assert monitoring.recent_events() == []


def test_evaluate_page_shows_staleness_banner_when_code_newer_than_baseline(tmp_path):
    baseline = {
        "generated_at": "2000-01-01",
        "summary": {"goldens": 1, "decided": 1, "passed": 1},
        "goldens": {"g": {"pass": True, "decided_by": "tier1-asserts", "asserts": []}},
    }
    path = tmp_path / "eval-baseline.json"
    path.write_text(json.dumps(baseline), encoding="utf-8")
    with patch.object(dashboard, "_EVAL_BASELINE_PATH", path):
        html_out = dashboard.render_evaluate_page()
        assert "có thể KHÔNG còn phản ánh đúng hành vi hiện tại" in html_out


def test_evaluate_page_no_staleness_banner_when_baseline_missing(tmp_path):
    with patch.object(dashboard, "_EVAL_BASELINE_PATH", tmp_path / "missing.json"):
        html_out = dashboard.render_evaluate_page()
        assert "phản ánh đúng hành vi hiện tại" not in html_out
