"""Monitoring — PORT TRỰC TIẾP từ demo_agents/weather_agent/monitoring.py (đã chạy ổn định, có
test) — chỉ đổi tên class hook (`DevOpsAgentHooks`) và DB path riêng cho agent này, KHÔNG đổi logic.
Bắt hành vi agent qua lifecycle hooks THẬT của Agents SDK (`AgentHooks`), ghi vào SQLite local kèm
`run_id`/`session_id` — xem docstring gốc ở weather_agent/monitoring.py cho giải thích đầy đủ.

devops_agent trước đây KHÔNG có layer monitoring này (ghi chú CHỦ Ý trong chatdemo.py cũ: "chưa xây
monitoring.py/dashboard.py cho agent này — thêm khi được yêu cầu") — nay thêm để đủ 2 agent đều có
`/monitor`, và để `_run_streamed`/`chatdemo.py` có nơi ghi sự kiện tool_call/tool_result đầy đủ
args/output (đúng tinh thần "loop transparency" — xem wiki/log.md)."""

import json
import sqlite3
import time
from pathlib import Path

from agents import AgentHooks

_DB_PATH = Path(__file__).parent / "monitoring.sqlite3"
_RETENTION_DAYS = 30

_LATENCY_PAIRS = {
    "request": ("agent_start", "agent_end"),
    "llm_call": ("llm_start", "llm_end"),
}

_TERMINAL_EVENTS = ("agent_end", "harness_guardrail_tripped", "harness_max_turns_exceeded")
_ERROR_EVENTS = ("harness_guardrail_tripped", "harness_max_turns_exceeded")


def _connect():
    con = sqlite3.connect(str(_DB_PATH))
    con.execute(
        "CREATE TABLE IF NOT EXISTS events ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "ts REAL NOT NULL, "
        "agent_name TEXT NOT NULL, "
        "event TEXT NOT NULL, "
        "detail TEXT NOT NULL, "
        "session_id TEXT, "
        "run_id TEXT)"
    )
    return con


def log_event(agent_name, event, detail=None, session_id=None, run_id=None):
    con = _connect()
    try:
        con.execute(
            "INSERT INTO events (ts, agent_name, event, detail, session_id, run_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (time.time(), agent_name, event, json.dumps(detail or {}, ensure_ascii=False), session_id, run_id),
        )
        con.commit()
    finally:
        con.close()


def recent_events(limit=50):
    con = _connect()
    try:
        rows = con.execute(
            "SELECT ts, agent_name, event, detail, session_id, run_id FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {"ts": ts, "agent_name": name, "event": event, "detail": json.loads(detail),
             "session_id": session_id, "run_id": run_id}
            for ts, name, event, detail, session_id, run_id in rows
        ]
    finally:
        con.close()


def count_events_by_type():
    con = _connect()
    try:
        rows = con.execute(
            "SELECT event, COUNT(*) FROM events GROUP BY event ORDER BY COUNT(*) DESC"
        ).fetchall()
        return dict(rows)
    finally:
        con.close()


def tool_usage_counts():
    con = _connect()
    try:
        rows = con.execute("SELECT detail FROM events WHERE event = 'tool_end'").fetchall()
    finally:
        con.close()
    counts = {}
    for (detail,) in rows:
        name = json.loads(detail).get("tool", "unknown")
        counts[name] = counts.get(name, 0) + 1
    return counts


def events_by_session():
    con = _connect()
    try:
        rows = con.execute("SELECT COALESCE(session_id, ''), event FROM events").fetchall()
    finally:
        con.close()
    by_session = {}
    for sid, event in rows:
        entry = by_session.setdefault(sid, {"session_id": sid, "events": 0, "errors": 0})
        entry["events"] += 1
        if event in _ERROR_EVENTS:
            entry["errors"] += 1
    return sorted(by_session.values(), key=lambda e: -e["events"])


def latency_stats():
    con = _connect()
    try:
        rows = con.execute(
            "SELECT run_id, event, ts FROM events WHERE run_id IS NOT NULL AND run_id != ''"
        ).fetchall()
    finally:
        con.close()
    by_run = {}
    for run_id, event, ts in rows:
        by_run.setdefault(run_id, []).append((event, ts))
    stats = {}
    for label, (start_ev, end_ev) in _LATENCY_PAIRS.items():
        durations = []
        for run_id, events in by_run.items():
            starts = sorted(ts for ev, ts in events if ev == start_ev)
            ends = sorted(ts for ev, ts in events if ev == end_ev)
            for s, e in zip(starts, ends):
                if e >= s:
                    durations.append(e - s)
        if durations:
            stats[label] = {
                "count": len(durations),
                "avg_s": round(sum(durations) / len(durations), 2),
                "max_s": round(max(durations), 2),
                "min_s": round(min(durations), 2),
            }
        else:
            stats[label] = {"count": 0, "avg_s": None, "max_s": None, "min_s": None}
    return stats


def error_rate_recent(window=20):
    con = _connect()
    try:
        placeholders = ",".join("?" * len(_TERMINAL_EVENTS))
        rows = con.execute(
            f"SELECT event FROM events WHERE event IN ({placeholders}) ORDER BY id DESC LIMIT ?",
            (*_TERMINAL_EVENTS, window),
        ).fetchall()
    finally:
        con.close()
    total = len(rows)
    errors = sum(1 for (event,) in rows if event in _ERROR_EVENTS)
    return {"window": window, "total": total, "errors": errors, "rate": round(errors / total, 3) if total else 0.0}


def daily_event_counts(days=14):
    cutoff = time.time() - days * 86400
    con = _connect()
    try:
        rows = con.execute("SELECT ts FROM events WHERE ts >= ?", (cutoff,)).fetchall()
    finally:
        con.close()
    counts = {}
    for (ts,) in rows:
        day = time.strftime("%Y-%m-%d", time.gmtime(ts))
        counts[day] = counts.get(day, 0) + 1
    return sorted(counts.items())


def prune_old_events(days=_RETENTION_DAYS):
    cutoff = time.time() - days * 86400
    con = _connect()
    try:
        con.execute("DELETE FROM events WHERE ts < ?", (cutoff,))
        con.commit()
    finally:
        con.close()


class DevOpsAgentHooks(AgentHooks):
    """Cùng pattern weather_agent/monitoring.py::WeatherAgentHooks — xem docstring ở đó."""

    @staticmethod
    def _ids(context):
        meta = getattr(context, "context", None)
        return getattr(meta, "session_id", None), getattr(meta, "run_id", None)

    async def on_start(self, context, agent):
        sid, rid = self._ids(context)
        log_event(agent.name, "agent_start", session_id=sid, run_id=rid)

    async def on_end(self, context, agent, output):
        sid, rid = self._ids(context)
        log_event(agent.name, "agent_end", {"output_preview": str(output)[:200]}, sid, rid)

    async def on_tool_start(self, context, agent, tool):
        sid, rid = self._ids(context)
        log_event(agent.name, "tool_start", {"tool": getattr(tool, "name", str(tool))}, sid, rid)

    async def on_tool_end(self, context, agent, tool, result):
        sid, rid = self._ids(context)
        log_event(
            agent.name, "tool_end",
            {"tool": getattr(tool, "name", str(tool)), "result_preview": str(result)[:200]}, sid, rid,
        )

    async def on_llm_start(self, context, agent, system_prompt, input_items):
        sid, rid = self._ids(context)
        log_event(agent.name, "llm_start", {"n_input_items": len(input_items)}, sid, rid)

    async def on_llm_end(self, context, agent, response):
        sid, rid = self._ids(context)
        log_event(agent.name, "llm_end", session_id=sid, run_id=rid)
