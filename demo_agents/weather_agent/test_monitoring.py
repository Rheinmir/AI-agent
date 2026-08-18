import asyncio
import time
from unittest.mock import MagicMock, patch

from demo_agents.weather_agent import monitoring
from demo_agents.weather_agent.monitoring import (
    WeatherAgentHooks,
    daily_event_counts,
    error_rate_recent,
    events_by_session,
    latency_stats,
    log_event,
    prune_old_events,
    recent_events,
)


def test_log_event_then_recent_events_round_trip(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"):
        log_event("Weather agent", "agent_start")
        log_event("Weather agent", "tool_end", {"tool": "get_weather", "result_preview": "ok"})
        events = recent_events()
        assert len(events) == 2
        assert events[0]["event"] == "tool_end"
        assert events[0]["detail"]["tool"] == "get_weather"
        assert events[1]["event"] == "agent_start"


def test_recent_events_respects_limit(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"):
        for i in range(5):
            log_event("Weather agent", f"event-{i}")
        assert len(recent_events(limit=2)) == 2


def test_hooks_write_events_for_full_lifecycle(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"):
        hooks = WeatherAgentHooks()
        agent = MagicMock(name="Weather agent")
        agent.name = "Weather agent"
        tool = MagicMock(name="get_weather")
        tool.name = "get_weather"

        async def run_lifecycle():
            await hooks.on_start(None, agent)
            await hooks.on_llm_start(None, agent, "sys", [1, 2])
            await hooks.on_tool_start(None, agent, tool)
            await hooks.on_tool_end(None, agent, tool, "29.0C")
            await hooks.on_llm_end(None, agent, MagicMock())
            await hooks.on_end(None, agent, "final answer")

        asyncio.run(run_lifecycle())
        events = [e["event"] for e in recent_events()]
        assert events == [
            "agent_end",
            "llm_end",
            "tool_end",
            "tool_start",
            "llm_start",
            "agent_start",
        ]


def test_hooks_read_session_id_and_run_id_from_context(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"):
        hooks = WeatherAgentHooks()
        agent = MagicMock()
        agent.name = "Weather agent"
        run_ctx = MagicMock()
        run_ctx.context = MagicMock(session_id="s-1", run_id="r-1")

        asyncio.run(hooks.on_start(run_ctx, agent))
        events = recent_events()
        assert events[0]["session_id"] == "s-1"
        assert events[0]["run_id"] == "r-1"


def test_hooks_tolerate_missing_context(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"):
        hooks = WeatherAgentHooks()
        agent = MagicMock()
        agent.name = "Weather agent"
        asyncio.run(hooks.on_start(None, agent))  # không raise dù context=None
        events = recent_events()
        assert events[0]["session_id"] is None


def test_events_by_session_counts_events_and_errors(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"):
        log_event("Weather agent", "agent_start", session_id="s-1", run_id="r-1")
        log_event("Weather agent", "agent_end", session_id="s-1", run_id="r-1")
        log_event("Weather agent", "harness_guardrail_tripped", session_id="s-2", run_id="r-2")
        by_session = {e["session_id"]: e for e in events_by_session()}
        assert by_session["s-1"]["events"] == 2
        assert by_session["s-1"]["errors"] == 0
        assert by_session["s-2"]["events"] == 1
        assert by_session["s-2"]["errors"] == 1


def test_latency_stats_computes_duration_between_paired_events(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"):
        con = monitoring._connect()
        con.execute(
            "INSERT INTO events (ts, agent_name, event, detail, session_id, run_id) VALUES "
            "(100.0, 'A', 'agent_start', '{}', 's', 'r1'), "
            "(106.0, 'A', 'agent_end', '{}', 's', 'r1'), "
            "(100.0, 'A', 'llm_start', '{}', 's', 'r1'), "
            "(101.5, 'A', 'llm_end', '{}', 's', 'r1')"
        )
        con.commit()
        con.close()
        stats = latency_stats()
        assert stats["request"]["count"] == 1
        assert stats["request"]["avg_s"] == 6.0
        assert stats["llm_call"]["count"] == 1
        assert stats["llm_call"]["avg_s"] == 1.5


def test_latency_stats_ignores_events_without_run_id(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"):
        log_event("A", "agent_start")  # không truyền run_id
        log_event("A", "agent_end")
        stats = latency_stats()
        assert stats["request"]["count"] == 0


def test_error_rate_recent_computes_fraction(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"):
        log_event("A", "agent_end")
        log_event("A", "agent_end")
        log_event("A", "harness_guardrail_tripped")
        log_event("A", "harness_max_turns_exceeded")
        stats = error_rate_recent(window=10)
        assert stats["total"] == 4
        assert stats["errors"] == 2
        assert stats["rate"] == 0.5


def test_error_rate_recent_respects_window(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"):
        for _ in range(5):
            log_event("A", "agent_end")
        log_event("A", "harness_guardrail_tripped")
        stats = error_rate_recent(window=2)
        assert stats["total"] == 2
        # 2 sự kiện GẦN NHẤT: agent_end (thứ 5) + harness_guardrail_tripped (mới nhất) -> 1 lỗi
        assert stats["errors"] == 1


def test_daily_event_counts_buckets_by_day(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"):
        log_event("A", "agent_start")
        log_event("A", "agent_end")
        counts = daily_event_counts(days=1)
        today = time.strftime("%Y-%m-%d", time.gmtime())
        assert dict(counts).get(today) == 2


def test_prune_old_events_removes_events_older_than_cutoff(tmp_path):
    with patch.object(monitoring, "_DB_PATH", tmp_path / "mon.sqlite3"):
        con = monitoring._connect()
        old_ts = time.time() - 40 * 86400
        con.execute(
            "INSERT INTO events (ts, agent_name, event, detail) VALUES (?, 'A', 'agent_start', '{}')",
            (old_ts,),
        )
        con.commit()
        con.close()
        log_event("A", "agent_end")  # sự kiện mới
        assert len(recent_events(limit=10)) == 2
        prune_old_events(days=30)
        remaining = recent_events(limit=10)
        assert len(remaining) == 1
        assert remaining[0]["event"] == "agent_end"


def test_schema_migration_adds_session_and_run_id_columns_to_legacy_table(tmp_path):
    """File cũ (trước bản có session_id/run_id) chỉ có 4 cột — _connect() phải tự thêm cột mới
    thay vì crash, dữ liệu cũ vẫn đọc được."""
    db_path = tmp_path / "legacy.sqlite3"
    import sqlite3

    con = sqlite3.connect(str(db_path))
    con.execute(
        "CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, "
        "agent_name TEXT NOT NULL, event TEXT NOT NULL, detail TEXT NOT NULL)"
    )
    con.execute(
        "INSERT INTO events (ts, agent_name, event, detail) VALUES (1.0, 'A', 'agent_start', '{}')"
    )
    con.commit()
    con.close()

    with patch.object(monitoring, "_DB_PATH", db_path):
        events = recent_events()
        assert len(events) == 1
        assert events[0]["session_id"] is None
        log_event("A", "agent_end", session_id="new-session", run_id="new-run")
        events = recent_events()
        assert events[0]["session_id"] == "new-session"
