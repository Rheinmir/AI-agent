"""Monitoring — bắt hành vi agent qua lifecycle hooks THẬT của Agents SDK (`AgentHooks`), không
phải tự dựng cơ chế riêng. Mỗi sự kiện (bắt đầu lượt, gọi tool, nhận phản hồi model, kết thúc lượt)
được ghi vào SQLite local kèm `run_id`/`session_id` — trả lời trực tiếp câu hỏi "cần có cái gì để
monitoring hành vi của agent" + "cần hook để bắt" (không cần đổi sang LangChain/LangGraph — SDK
đang dùng đã có sẵn hook, chỉ cần gắn logger vào). Xem wiki/concepts/agent-7-layers.md § Evaluation
(giám sát ngoài luồng).

`run_id`/`session_id` đọc từ `RunMeta` (harness.py) truyền qua tham số `context=` của
`Runner.run_sync` — đây là cách CHÍNH THỐNG của Agents SDK để đưa dữ liệu tuỳ biến vào tới hooks
(`context: RunContextWrapper[TContext]`, `context.context` là object app tự định nghĩa), không
phải hack riêng. Không có `run_id` thì KHÔNG THỂ ghép cặp tool_start/tool_end hay llm_start/llm_end
của CÙNG 1 lượt để tính latency — nhiều request tuần tự (server này xử lý tuần tự, không đa luồng)
vẫn cần khoá phân biệt rõ ràng, không thể giả định "2 sự kiện liền kề luôn cùng 1 lượt".
"""

import json
import sqlite3
import time
from pathlib import Path

from agents import AgentHooks

_DB_PATH = Path(__file__).parent / "monitoring.sqlite3"
_RETENTION_DAYS = 30

# event -> (start_event, end_event) — cặp sự kiện dùng để tính latency theo run_id.
_LATENCY_PAIRS = {
    "request": ("agent_start", "agent_end"),
    "llm_call": ("llm_start", "llm_end"),
}

_TERMINAL_EVENTS = (
    "agent_end",
    "harness_capability_shortcut",
    "harness_guardrail_tripped",
    "harness_max_turns_exceeded",
    "harness_retries_exhausted",
)
_ERROR_EVENTS = ("harness_guardrail_tripped", "harness_max_turns_exceeded", "harness_retries_exhausted")


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
    # File cũ (trước khi thêm session_id/run_id) thiếu 2 cột — thêm vào nếu chưa có thay vì bắt
    # xoá file: dữ liệu cũ vẫn đọc được (2 cột mới là NULL), không mất lịch sử đã ghi.
    existing_cols = {row[1] for row in con.execute("PRAGMA table_info(events)")}
    for col in ("session_id", "run_id"):
        if col not in existing_cols:
            con.execute(f"ALTER TABLE events ADD COLUMN {col} TEXT")
    return con


def log_event(agent_name, event, detail=None, session_id=None, run_id=None):
    """Ghi 1 sự kiện — hàm trần (không async) để test/gọi tay dễ dàng, hooks bên dưới chỉ là
    lớp mỏng gọi vào đây."""
    con = _connect()
    try:
        con.execute(
            "INSERT INTO events (ts, agent_name, event, detail, session_id, run_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                time.time(),
                agent_name,
                event,
                json.dumps(detail or {}, ensure_ascii=False),
                session_id,
                run_id,
            ),
        )
        con.commit()
    finally:
        con.close()


def recent_events(limit=50):
    """Đọc lại N sự kiện gần nhất, mới nhất trước — dùng cho việc xem log/monitor thủ công."""
    con = _connect()
    try:
        rows = con.execute(
            "SELECT ts, agent_name, event, detail, session_id, run_id FROM events "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {
                "ts": ts,
                "agent_name": name,
                "event": event,
                "detail": json.loads(detail),
                "session_id": session_id,
                "run_id": run_id,
            }
            for ts, name, event, detail, session_id, run_id in rows
        ]
    finally:
        con.close()


def count_events_by_type():
    """Tổng số sự kiện theo loại, giảm dần — nền cho dashboard /monitor phân tích tổng quan."""
    con = _connect()
    try:
        rows = con.execute(
            "SELECT event, COUNT(*) FROM events GROUP BY event ORDER BY COUNT(*) DESC"
        ).fetchall()
        return dict(rows)
    finally:
        con.close()


def tool_usage_counts():
    """Đếm số lần mỗi tool thực thi xong (tool_end) — tool nào được agent dùng nhiều nhất."""
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
    """Đếm số sự kiện + số lỗi/guardrail-chặn theo session_id — trả về list dict, nhiều sự kiện
    nhất trước. Sự kiện không có session_id (vd log tay không truyền) gom vào key rỗng ''."""
    con = _connect()
    try:
        rows = con.execute(
            "SELECT COALESCE(session_id, ''), event FROM events"
        ).fetchall()
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
    """Ghép cặp start/end CÙNG run_id để tính latency thật (giây) — request tổng (agent_start ->
    agent_end) và từng lần gọi LLM (llm_start -> llm_end, 1 request có thể có NHIỀU cặp). Sự kiện
    thiếu run_id (log tay không truyền, hoặc chưa migrate) bị bỏ qua — không đoán mò ghép nhầm."""
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
            # ghép theo thứ tự thời gian trong CÙNG run_id (1 request chỉ có 1 agent_start, nhưng
            # có thể có nhiều llm_start nếu agent gọi model nhiều vòng) — zip theo cặp gần nhau
            # nhất, đủ tốt cho demo tuần tự (không có 2 run chồng lấn cùng lúc).
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
    """Tỉ lệ lỗi/guardrail-chặn/quá vòng lặp trong N request GẦN NHẤT (theo sự kiện kết thúc lượt)
    — cảnh báo sớm nếu tỉ lệ này cao bất thường, không đợi xem hết toàn bộ lịch sử."""
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
    return {
        "window": window,
        "total": total,
        "errors": errors,
        "rate": round(errors / total, 3) if total else 0.0,
    }


def daily_event_counts(days=14):
    """Số sự kiện theo NGÀY (UTC, khoá YYYY-MM-DD), N ngày gần nhất — nền cho biểu đồ xu hướng đơn
    giản trên /monitor. Không dùng thư viện chart ngoài — chỉ trả số liệu, dashboard.py tự vẽ SVG."""
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
    """Xoá sự kiện cũ hơn N ngày — retention tối thiểu để file sqlite không phình vô hạn. Gọi mỗi
    lần dashboard /monitor tải trang (rẻ, không cần cron riêng cho quy mô demo này)."""
    cutoff = time.time() - days * 86400
    con = _connect()
    try:
        con.execute("DELETE FROM events WHERE ts < ?", (cutoff,))
        con.commit()
    finally:
        con.close()


class WeatherAgentHooks(AgentHooks):
    """Gắn vào Agent(hooks=...) — mỗi callback SDK gọi sẵn (không phải code tự dựng lại vòng
    lặp) được chuyển thành 1 dòng log qua monitoring.sqlite3. Đọc session_id/run_id từ
    `context.context` (RunMeta do harness.py truyền qua Runner.run_sync(context=...)) — getattr an
    toàn vì `context`/`context.context` có thể None khi gọi Runner.run_sync không truyền context
    (vd test, hoặc dùng agent ngoài luồng chatdemo.py)."""

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
            agent.name,
            "tool_end",
            {"tool": getattr(tool, "name", str(tool)), "result_preview": str(result)[:200]},
            sid,
            rid,
        )

    async def on_llm_start(self, context, agent, system_prompt, input_items):
        sid, rid = self._ids(context)
        log_event(agent.name, "llm_start", {"n_input_items": len(input_items)}, sid, rid)

    async def on_llm_end(self, context, agent, response):
        sid, rid = self._ids(context)
        log_event(agent.name, "llm_end", session_id=sid, run_id=rid)
