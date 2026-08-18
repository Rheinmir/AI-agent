"""Long-term memory — devops_agent CHƯA có file này trước đây (không có fact toàn cục kiểu
`recall_last_city` của weather_agent). Thêm MỚI ở đây chỉ để chứa consolidation — cùng pattern
weather_agent/memory.py::consolidate_if_due, đọc docstring ở đó cho giải thích đầy đủ động cơ/cạnh
lỗi. Cứ mỗi `_CONSOLIDATE_EVERY_N_TURNS` lượt hỏi, 1 model RẺ tóm tắt hội thoại gần đây thành 1-2
câu fact bền, ghi vào bảng `consolidated_summaries` riêng trong `long_term_memory.sqlite3`."""

import sqlite3
import time
from pathlib import Path

from agents import Agent, Runner

from demo_agents.devops_agent.model_provider import get_model

_DB_PATH = Path(__file__).parent / "long_term_memory.sqlite3"
_CONSOLIDATE_EVERY_N_TURNS = 6

_SUMMARIZER_INSTRUCTIONS = (
    "Bạn tóm tắt 1 đoạn hội thoại giữa user và DevOps Q&A agent thành 1-2 CÂU NGẮN, chỉ giữ thông "
    "tin ĐÁNG NHỚ LÂU DÀI (chủ đề DevOps người dùng hay hỏi, pattern câu hỏi lặp lại) — bỏ qua nội "
    "dung cheatsheet cụ thể (đã có trong lịch sử session, không cần tóm tắt lại). CHỈ trả về 1-2 "
    "câu tóm tắt bằng tiếng Việt, không thêm giải thích/tiêu đề."
)
_summarizer_agent = Agent(
    name="DevOps session summarizer", model=get_model(), instructions=_SUMMARIZER_INSTRUCTIONS,
)


def _connect():
    con = sqlite3.connect(str(_DB_PATH))
    con.execute(
        "CREATE TABLE IF NOT EXISTS consolidated_summaries ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, "
        "summary TEXT NOT NULL, created_at REAL NOT NULL, turn_count INTEGER NOT NULL)"
    )
    return con


def _extract_plain_transcript(items):
    lines = []
    for it in items:
        role = it.get("role")
        if role == "user" and isinstance(it.get("content"), str):
            lines.append(f"User: {it['content']}")
        elif role == "assistant" and it.get("type") == "message":
            parts = [
                c.get("text", "") for c in (it.get("content") or [])
                if isinstance(c, dict) and c.get("type") == "output_text"
            ]
            text = "".join(parts)
            if text:
                lines.append(f"Assistant: {text}")
    return "\n".join(lines)


def save_consolidated_summary(session_id, summary, turn_count):
    con = _connect()
    try:
        con.execute(
            "INSERT INTO consolidated_summaries (session_id, summary, created_at, turn_count) "
            "VALUES (?, ?, ?, ?)",
            (session_id, summary, time.time(), turn_count),
        )
        con.commit()
    finally:
        con.close()


def recent_summaries(session_id, limit=5):
    con = _connect()
    try:
        rows = con.execute(
            "SELECT summary, created_at, turn_count FROM consolidated_summaries "
            "WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [{"summary": s, "created_at": t, "turn_count": tc} for s, t, tc in rows]
    finally:
        con.close()


async def consolidate_if_due(session, session_id):
    """Gọi sau MỖI lượt chat thành công — tự bỏ qua nếu chưa tới mốc N lượt/session_id rỗng. KHÔNG
    raise — mọi lỗi bị nuốt có chủ đích (tác vụ phụ, không được làm crash/lộ lỗi ra ngoài)."""
    if not session_id:
        return
    try:
        items = await session.get_items()
        user_turns = sum(1 for it in items if it.get("role") == "user" and isinstance(it.get("content"), str))
        if user_turns == 0 or user_turns % _CONSOLIDATE_EVERY_N_TURNS != 0:
            return
        transcript = _extract_plain_transcript(items)
        if not transcript.strip():
            return
        result = await Runner.run(_summarizer_agent, transcript)
        summary = (result.final_output or "").strip()
        if summary:
            save_consolidated_summary(session_id, summary, user_turns)
    except Exception:  # noqa: BLE001
        pass
