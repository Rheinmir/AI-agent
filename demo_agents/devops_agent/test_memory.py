import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from demo_agents.devops_agent import memory


def _run(coro):
    return asyncio.run(coro)


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
        memory.save_consolidated_summary("s1", "User hay hỏi Kubernetes.", 6)
        rows = memory.recent_summaries("s1")
        assert len(rows) == 1
        assert rows[0]["summary"] == "User hay hỏi Kubernetes."


@patch("demo_agents.devops_agent.memory.Runner.run", new_callable=AsyncMock)
def test_consolidate_skips_when_not_due(mock_run, tmp_path):
    with patch.object(memory, "_DB_PATH", tmp_path / "mem.sqlite3"):
        session = MagicMock()
        session.get_items = AsyncMock(return_value=_fake_items(3))
        _run(memory.consolidate_if_due(session, "s1"))
        mock_run.assert_not_called()
        assert memory.recent_summaries("s1") == []


@patch("demo_agents.devops_agent.memory.Runner.run", new_callable=AsyncMock)
def test_consolidate_fires_at_n_turns_and_saves_summary(mock_run, tmp_path):
    with patch.object(memory, "_DB_PATH", tmp_path / "mem.sqlite3"):
        mock_run.return_value = MagicMock(final_output="User hay hỏi Kubernetes và CI/CD.")
        session = MagicMock()
        session.get_items = AsyncMock(return_value=_fake_items(6))
        _run(memory.consolidate_if_due(session, "s1"))
        mock_run.assert_called_once()
        rows = memory.recent_summaries("s1")
        assert rows[0]["summary"] == "User hay hỏi Kubernetes và CI/CD."


def test_consolidate_noop_without_session_id(tmp_path):
    with patch.object(memory, "_DB_PATH", tmp_path / "mem.sqlite3"):
        session = MagicMock()
        session.get_items = AsyncMock(return_value=_fake_items(6))
        _run(memory.consolidate_if_due(session, ""))
        session.get_items.assert_not_called()


@patch("demo_agents.devops_agent.memory.Runner.run", new_callable=AsyncMock)
def test_consolidate_swallows_model_error(mock_run, tmp_path):
    with patch.object(memory, "_DB_PATH", tmp_path / "mem.sqlite3"):
        mock_run.side_effect = ConnectionError("network down")
        session = MagicMock()
        session.get_items = AsyncMock(return_value=_fake_items(6))
        _run(memory.consolidate_if_due(session, "s1"))
        assert memory.recent_summaries("s1") == []
