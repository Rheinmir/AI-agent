"""Long-term memory — nhớ XUYÊN các cuộc trò chuyện khác nhau, khác hẳn `SQLiteSession` (agents SDK)
vốn chỉ nhớ TRONG 1 phiên/session_id (xem chatdemo.py). Bản demo local 1 người dùng (không có đăng
nhập/nhiều user) nên lưu GLOBAL, không phân biệt theo session — thành phố agent tra cứu thời tiết
THÀNH CÔNG gần nhất, để gợi ý lại khi một cuộc trò chuyện MỚI không nêu rõ thành phố. Xem
wiki/concepts/agent-7-layers.md § Memory.

Consolidation (`consolidate_if_due`): SQLiteSession tích luỹ RAW message VÔ HẠN trong 1 session —
càng dài, agent/guardrail càng phải đọc nhiều context không cần thiết. Cứ mỗi
`_CONSOLIDATE_EVERY_N_TURNS` lượt hỏi, 1 model RẺ tóm tắt các lượt gần đây thành 1-2 câu fact bền,
ghi vào bảng `consolidated_summaries` riêng (KHÔNG đụng bảng `agent_sessions`/`agent_messages` do
SQLiteSession tự quản) — chạy FIRE-AND-FORGET sau khi response đã gửi xong (xem
chatdemo.py::_MCPBridge.fire_and_forget), không chặn request kế tiếp. Lỗi consolidation (model
lỗi, JSON méo...) bị NUỐT có chủ đích — đây là tác vụ PHỤ, không được làm mất phản hồi chat thật."""

import sqlite3
import time
from pathlib import Path

from agents import Agent, Runner

from demo_agents.weather_agent.model_provider import get_model

_DB_PATH = Path(__file__).parent / "long_term_memory.sqlite3"
_KEY_LAST_CITY = "last_city"
_CONSOLIDATE_EVERY_N_TURNS = 6

_SUMMARIZER_INSTRUCTIONS = (
    "Bạn tóm tắt 1 đoạn hội thoại giữa user và weather agent thành 1-2 CÂU NGẮN, chỉ giữ thông tin "
    "ĐÁNG NHỚ LÂU DÀI (thành phố người dùng hay hỏi, pattern câu hỏi lặp lại, sở thích) — bỏ qua "
    "số liệu thời tiết cụ thể (nhiệt độ, tình trạng trời — đã có trong lịch sử session, không cần "
    "tóm tắt lại). CHỈ trả về 1-2 câu tóm tắt bằng tiếng Việt, không thêm giải thích/tiêu đề."
)
_summarizer_agent = Agent(
    name="Weather session summarizer", model=get_model(), instructions=_SUMMARIZER_INSTRUCTIONS,
)


def _connect():
    con = sqlite3.connect(str(_DB_PATH))
    con.execute("CREATE TABLE IF NOT EXISTS facts (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    con.execute(
        "CREATE TABLE IF NOT EXISTS consolidated_summaries ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, "
        "summary TEXT NOT NULL, created_at REAL NOT NULL, turn_count INTEGER NOT NULL)"
    )
    return con


def _extract_plain_transcript(items):
    """Rút gọn output thô SQLiteSession.get_items() thành text 'User: .../Assistant: ...' cho model
    tóm tắt đọc — bản ĐƠN GIẢN HƠN chatdemo.py::_extract_transcript (không cần giữ cấu trúc
    {role,text} cho UI, chỉ cần text thuần nối dòng)."""
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
    """Gọi sau MỖI lượt chat thành công — tự bỏ qua nếu chưa tới mốc N lượt hoặc session_id rỗng.
    KHÔNG raise — mọi lỗi bị nuốt có chủ đích (xem docstring module)."""
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
    except Exception:  # noqa: BLE001 — tác vụ phụ, không được làm crash/lộ lỗi ra ngoài
        pass


def remember_last_city(city_name: str) -> None:
    """Lưu (ghi đè) thành phố tra cứu thời tiết thành công gần nhất — sống sót qua mọi session_id
    và qua cả lần khởi động lại server (SQLite trên đĩa, không phải in-memory)."""
    con = _connect()
    try:
        con.execute(
            "INSERT INTO facts (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (_KEY_LAST_CITY, city_name),
        )
        con.commit()
    finally:
        con.close()


def recall_last_city():
    """Trả thành phố đã lưu gần nhất, hoặc None nếu chưa từng tra cứu thành công lần nào."""
    con = _connect()
    try:
        row = con.execute("SELECT value FROM facts WHERE key=?", (_KEY_LAST_CITY,)).fetchone()
        return row[0] if row else None
    finally:
        con.close()
