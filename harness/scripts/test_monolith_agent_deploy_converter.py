"""Test cho monolith_agent_deploy_converter.py — dùng CHÍNH demo_agents/weather_agent thật làm
--src (đã có agent_spec.py đúng quy ước từ trước) thay vì fixture giả, để test luôn phản ánh đúng
input thật của tool. Không test việc CHẠY standalone_server.py sinh ra (cần network/API key thật) —
phần đó đã verify tay 1 lần khi build tool (xem wiki/log.md), test ở đây chỉ verify CẤU TRÚC bundle
sinh ra đúng, và các đường fail-loud đúng như thiết kế.
"""

import py_compile
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import monolith_agent_deploy_converter as converter  # noqa: E402

_REPO_ROOT = Path(__file__).parent.parent.parent
_WEATHER_AGENT_SRC = _REPO_ROOT / "demo_agents" / "weather_agent"
_DEVOPS_AGENT_SRC = _REPO_ROOT / "demo_agents" / "devops_agent"


def test_converts_real_weather_agent_end_to_end(tmp_path):
    out = tmp_path / "bundle"
    result = converter.convert(_WEATHER_AGENT_SRC, out, target="python", repo_root=_REPO_ROOT)
    assert result["agent_name"] == "Weather agent"
    assert result["package"] == "demo_agents.weather_agent"
    assert result["spec_func"] == "build_weather_agent_spec"
    assert set(result["tools"]) == {"get_weather", "get_city_note", "recall_last_city"}


def test_mcp_tools_bundled_when_spec_declares_it(tmp_path):
    """weather_agent/devops_agent đều khai báo mcp_tool_names=['fetch_server','exa_server'] —
    converter phải bundle mcp_tools/ (code) nhưng LOẠI servers-venv/ (machine-specific, quá nặng)."""
    out = tmp_path / "bundle"
    result = converter.convert(_WEATHER_AGENT_SRC, out, target="python", repo_root=_REPO_ROOT)
    assert result["mcp_tool_names"] == ["fetch_server", "exa_server"]
    assert (out / "mcp_tools" / "fetch_server.py").is_file()
    assert (out / "mcp_tools" / "exa_server.py").is_file()
    assert (out / "mcp_tools" / "README.md").is_file()
    assert not (out / "mcp_tools" / "servers-venv").exists()


def test_standalone_server_references_mcp_tool_names(tmp_path):
    out = tmp_path / "bundle"
    converter.convert(_DEVOPS_AGENT_SRC, out, target="python", repo_root=_REPO_ROOT)
    text = (out / "standalone_server.py").read_text()
    assert "MCP_TOOL_NAMES = ['fetch_server', 'exa_server']" in text
    assert "_MCPBridge" in text


def test_readme_mentions_mcp_setup_when_agent_uses_it(tmp_path):
    out = tmp_path / "bundle"
    converter.convert(_DEVOPS_AGENT_SRC, out, target="python", repo_root=_REPO_ROOT)
    readme = (out / "README.md").read_text()
    assert "servers-venv" in readme
    assert "mcp-server-fetch" in readme


def test_accent_color_read_from_spec_is_per_agent_not_hardcoded(tmp_path):
    """accent_color phải tới TỪ AgentSpec của từng agent (quy ước: màu công nghệ xương sống của
    domain agent theo) — không phải 1 hằng số hardcode chung cho mọi bundle."""
    out_weather = tmp_path / "weather"
    out_devops = tmp_path / "devops"
    result_weather = converter.convert(_WEATHER_AGENT_SRC, out_weather, target="python", repo_root=_REPO_ROOT)
    result_devops = converter.convert(_DEVOPS_AGENT_SRC, out_devops, target="python", repo_root=_REPO_ROOT)
    assert result_weather["accent_color"] == "#10a37f"
    assert result_devops["accent_color"] == "#326CE5"
    assert result_weather["accent_color"] != result_devops["accent_color"]
    assert "#326CE5" in (out_devops / "standalone_server.py").read_text()
    assert "#10a37f" in (out_weather / "standalone_server.py").read_text()


def test_accent_color_falls_back_to_neutral_when_spec_omits_it(tmp_path):
    src = tmp_path / "no_color_agent"
    src.mkdir()
    (src / "__init__.py").write_text("")
    (src / "agent_spec.py").write_text(
        "from dataclasses import dataclass, field\n"
        "@dataclass\n"
        "class AgentSpec:\n"
        "    name: str\n"
        "    instructions: str\n"
        "    tools: list = field(default_factory=list)\n"
        "    guardrails: list = field(default_factory=list)\n"
        "    hooks: object = None\n"
        "def build_no_color_agent_spec():\n"
        "    return AgentSpec(name='No Color Agent', instructions='x')\n"
    )
    result = converter.convert(src, tmp_path / "out", target="python", repo_root=tmp_path)
    assert result["accent_color"] == "#0a84ff"


def test_bundle_has_expected_files_for_python_target(tmp_path):
    out = tmp_path / "bundle"
    converter.convert(_WEATHER_AGENT_SRC, out, target="python", repo_root=_REPO_ROOT)
    assert (out / "standalone_server.py").is_file()
    assert (out / "requirements.txt").is_file()
    assert (out / "README.md").is_file()
    assert (out / "demo_agents" / "__init__.py").is_file()
    assert (out / "demo_agents" / "weather_agent" / "agent.py").is_file()
    assert (out / "demo_agents" / "weather_agent" / "web" / "chat.html").is_file()
    assert not (out / "Dockerfile").exists()


def test_bundle_adds_dockerfile_only_for_docker_or_both_target(tmp_path):
    out_py = tmp_path / "py-only"
    converter.convert(_WEATHER_AGENT_SRC, out_py, target="python", repo_root=_REPO_ROOT)
    assert not (out_py / "Dockerfile").exists()

    out_both = tmp_path / "both"
    converter.convert(_WEATHER_AGENT_SRC, out_both, target="both", repo_root=_REPO_ROOT)
    assert (out_both / "Dockerfile").is_file()
    assert (out_both / ".dockerignore").is_file()
    assert "EXPOSE 8080" in (out_both / "Dockerfile").read_text()


def test_bundle_excludes_secrets_and_runtime_state(tmp_path):
    """Không được copy .env (secret thật) hay .sqlite3/-wal/-shm (rác runtime của repo gốc) vào
    bundle xuất ra — bundle sẽ được đưa đi triển khai nơi khác, rò rỉ .env là lỗi bảo mật thật."""
    out = tmp_path / "bundle"
    converter.convert(_WEATHER_AGENT_SRC, out, target="python", repo_root=_REPO_ROOT)
    all_files = [str(p) for p in out.rglob("*") if p.is_file()]
    assert not any(f.endswith("/.env") or f.endswith("\\.env") for f in all_files)
    assert not any("sqlite3" in f for f in all_files)
    assert not any(Path(f).name.startswith("test_") for f in all_files)


def test_bundle_excludes_env_but_keeps_env_example(tmp_path):
    out = tmp_path / "bundle"
    converter.convert(_WEATHER_AGENT_SRC, out, target="python", repo_root=_REPO_ROOT)
    assert (out / "demo_agents" / "weather_agent" / ".env.example").is_file()


def test_standalone_server_is_syntactically_valid_python(tmp_path):
    out = tmp_path / "bundle"
    converter.convert(_WEATHER_AGENT_SRC, out, target="both", repo_root=_REPO_ROOT)
    py_compile.compile(str(out / "standalone_server.py"), doraise=True)


def test_generated_server_contains_correct_import_paths(tmp_path):
    out = tmp_path / "bundle"
    converter.convert(_WEATHER_AGENT_SRC, out, target="python", repo_root=_REPO_ROOT)
    text = (out / "standalone_server.py").read_text()
    assert "from demo_agents.weather_agent import agent_spec" in text
    assert "from demo_agents.weather_agent.exporters.openai_agents_exporter import build_openai_agent" in text
    assert "_agent_spec_module.build_weather_agent_spec()" in text


def test_missing_agent_spec_file_fails_loud(tmp_path):
    src = tmp_path / "not_an_agent"
    src.mkdir()
    (src / "__init__.py").write_text("")
    with pytest.raises(SystemExit, match="agent_spec.py"):
        converter.convert(src, tmp_path / "out", target="python", repo_root=tmp_path)


def test_zero_spec_functions_fails_loud(tmp_path):
    src = tmp_path / "bad_agent"
    src.mkdir()
    (src / "__init__.py").write_text("")
    (src / "agent_spec.py").write_text("def not_the_right_name():\n    pass\n")
    with pytest.raises(SystemExit, match="build_.*_agent_spec"):
        converter.convert(src, tmp_path / "out", target="python", repo_root=tmp_path)


def test_multiple_spec_functions_fails_loud_not_guessing(tmp_path):
    src = tmp_path / "ambiguous_agent"
    src.mkdir()
    (src / "__init__.py").write_text("")
    (src / "agent_spec.py").write_text(
        "def build_a_agent_spec():\n    pass\n\ndef build_b_agent_spec():\n    pass\n"
    )
    with pytest.raises(SystemExit, match="phải có ĐÚNG 1"):
        converter.convert(src, tmp_path / "out", target="python", repo_root=tmp_path)


def test_src_outside_repo_root_requires_explicit_package(tmp_path):
    outside = tmp_path / "outside_repo" / "agent"
    outside.mkdir(parents=True)
    other_root = tmp_path / "other_root"
    other_root.mkdir()
    with pytest.raises(SystemExit, match="--package"):
        converter._derive_package(outside, other_root)


def test_cli_requires_explicit_target(tmp_path):
    """--target không có default — chạy thiếu cờ này phải lỗi rõ, không tự chọn hộ 1 target."""
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).parent / "monolith_agent_deploy_converter.py"),
            "--src", str(_WEATHER_AGENT_SRC),
            "--out", str(tmp_path / "out"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "--target" in result.stderr
