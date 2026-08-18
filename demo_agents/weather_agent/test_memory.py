import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from demo_agents.weather_agent import memory


def _run(coro):
    return asyncio.run(coro)


def test_recall_before_any_remember_returns_none(tmp_path):
    with patch.object(memory, "_DB_PATH", tmp_path / "mem.sqlite3"):
        assert memory.recall_last_city() is None


def test_remember_then_recall_round_trip(tmp_path):
    with patch.object(memory, "_DB_PATH", tmp_path / "mem.sqlite3"):
        memory.remember_last_city("Hà Nội")
        assert memory.recall_last_city() == "Hà Nội"


def test_remember_overwrites_previous_value(tmp_path):
    with patch.object(memory, "_DB_PATH", tmp_path / "mem.sqlite3"):
        memory.remember_last_city("Hà Nội")
        memory.remember_last_city("Hạ Long")
        assert memory.recall_last_city() == "Hạ Long"


def test_persists_across_reconnects(tmp_path):
    # SQLite trên đĩa (không phải in-memory) — mỗi lần gọi tự mở/đóng connection riêng, giá trị
    # phải sống sót giữa các lần gọi độc lập, mô phỏng đúng việc server restart giữa các request.
    db_path = tmp_path / "mem.sqlite3"
    with patch.object(memory, "_DB_PATH", db_path):
        memory.remember_last_city("Đà Nẵng")
    with patch.object(memory, "_DB_PATH", db_path):
        assert memory.recall_last_city() == "Đà Nẵng"


# ---- consolidate_if_due — tóm tắt định kỳ (mỗi N lượt) thành fact bền, xem docstring memory.py


def _fake_items(n_user_turns):
    items = []
    for i in range(n_user_turns):
        items.append({"role": "user", "content": f"câu hỏi {i}"})
        items.append({
            "role": "assistant", "type": "message",
            "content": [{"type": "output_text", "text": f"trả lời {i}"}],
        })
    return items


def test_save_and_read_consolidated_summary(tmp_path):
    with patch.object(memory, "_DB_PATH", tmp_path / "mem.sqlite3"):
        memory.save_consolidated_summary("s1", "User hay hỏi thời tiết Hà Nội.", 6)
        rows = memory.recent_summaries("s1")
        assert len(rows) == 1
        assert rows[0]["summary"] == "User hay hỏi thời tiết Hà Nội."
        assert rows[0]["turn_count"] == 6


@patch("demo_agents.weather_agent.memory.Runner.run", new_callable=AsyncMock)
def test_consolidate_skips_when_not_due(mock_run, tmp_path):
    with patch.object(memory, "_DB_PATH", tmp_path / "mem.sqlite3"):
        session = MagicMock()
        session.get_items = AsyncMock(return_value=_fake_items(3))  # 3 < N=6, chưa tới mốc
        _run(memory.consolidate_if_due(session, "s1"))
        mock_run.assert_not_called()
        assert memory.recent_summaries("s1") == []


@patch("demo_agents.weather_agent.memory.Runner.run", new_callable=AsyncMock)
def test_consolidate_fires_at_n_turns_and_saves_summary(mock_run, tmp_path):
    with patch.object(memory, "_DB_PATH", tmp_path / "mem.sqlite3"):
        mock_run.return_value = MagicMock(final_output="User hay hỏi thời tiết các thành phố Việt Nam.")
        session = MagicMock()
        session.get_items = AsyncMock(return_value=_fake_items(6))  # đúng mốc N=6
        _run(memory.consolidate_if_due(session, "s1"))
        mock_run.assert_called_once()
        rows = memory.recent_summaries("s1")
        assert len(rows) == 1
        assert rows[0]["summary"] == "User hay hỏi thời tiết các thành phố Việt Nam."


def test_consolidate_noop_without_session_id(tmp_path):
    with patch.object(memory, "_DB_PATH", tmp_path / "mem.sqlite3"):
        session = MagicMock()
        session.get_items = AsyncMock(return_value=_fake_items(6))
        _run(memory.consolidate_if_due(session, ""))
        session.get_items.assert_not_called()


@patch("demo_agents.weather_agent.memory.Runner.run", new_callable=AsyncMock)
def test_consolidate_swallows_model_error(mock_run, tmp_path):
    """Tác vụ phụ — lỗi gọi model KHÔNG được raise ra ngoài (sẽ crash fire_and_forget nếu raise)."""
    with patch.object(memory, "_DB_PATH", tmp_path / "mem.sqlite3"):
        mock_run.side_effect = ConnectionError("network down")
        session = MagicMock()
        session.get_items = AsyncMock(return_value=_fake_items(6))
        _run(memory.consolidate_if_due(session, "s1"))  # không raise
        assert memory.recent_summaries("s1") == []
