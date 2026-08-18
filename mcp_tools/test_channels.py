"""Test hermetic cho channels.py — mock subprocess/requests, KHÔNG gọi gh/yt-dlp/mạng thật (verify
sống đã làm tay lúc build, xem wiki/log.md). Cùng kỷ luật NO_DATA đã kiểm tra ở test_tool.py của
weather_agent/devops_agent."""

from unittest.mock import MagicMock, patch

from mcp_tools.channels import (
    _parse_vtt,
    github_search_impl,
    rss_read_impl,
    youtube_transcript_impl,
)


def _mock_run(returncode=0, stdout="", stderr=""):
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


@patch("mcp_tools.channels.subprocess.run")
def test_github_search_returns_formatted_results(mock_run):
    mock_run.return_value = _mock_run(
        stdout='[{"fullName":"kubernetes/kubernetes","description":"K8s","url":"https://x","stargazersCount":100}]'
    )
    result = github_search_impl("kubernetes")
    assert "kubernetes/kubernetes" in result
    assert "⭐100" in result


@patch("mcp_tools.channels.subprocess.run")
def test_github_search_no_results_returns_no_data(mock_run):
    mock_run.return_value = _mock_run(stdout="[]")
    assert github_search_impl("xyzxyzxyz").startswith("NO_DATA:")


@patch("mcp_tools.channels.subprocess.run")
def test_github_search_gh_not_found_returns_no_data(mock_run):
    mock_run.side_effect = FileNotFoundError()
    assert github_search_impl("kubernetes").startswith("NO_DATA:")


@patch("mcp_tools.channels.subprocess.run")
def test_github_search_error_exit_code_returns_no_data(mock_run):
    mock_run.return_value = _mock_run(returncode=1, stderr="auth error")
    result = github_search_impl("kubernetes")
    assert result.startswith("NO_DATA:")
    assert "auth error" in result


def test_parse_vtt_strips_headers_timestamps_and_dedupes():
    raw = (
        "WEBVTT\nKind: captions\nLanguage: en\n\n"
        "00:00:01.200 --> 00:00:03.360\nHello world\n\n"
        "00:00:03.360 --> 00:00:05.000\nHello world\n\n"
        "00:00:05.000 --> 00:00:07.000\n<c>Second line</c>\n"
    )
    parsed = _parse_vtt(raw)
    assert parsed == "Hello world Second line"


@patch("mcp_tools.channels._YT_DLP_BIN")
def test_youtube_transcript_missing_binary_returns_no_data(mock_bin):
    mock_bin.is_file.return_value = False
    assert youtube_transcript_impl("https://youtube.com/watch?v=x").startswith("NO_DATA:")


@patch("requests.get")
def test_rss_read_returns_formatted_entries(mock_get):
    mock_resp = MagicMock()
    mock_resp.content = (
        b"<?xml version='1.0'?><rss><channel><title>Test Feed</title>"
        b"<item><title>Entry 1</title><link>https://x/1</link><pubDate>Mon, 01 Jan 2026 00:00:00 GMT</pubDate></item>"
        b"</channel></rss>"
    )
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp
    result = rss_read_impl("https://example.com/feed.xml")
    assert "Test Feed" in result
    assert "Entry 1" in result


@patch("requests.get")
def test_rss_read_network_error_returns_no_data(mock_get):
    import requests

    mock_get.side_effect = requests.RequestException("timeout")
    assert rss_read_impl("https://example.com/feed.xml").startswith("NO_DATA:")


@patch("requests.get")
def test_rss_read_invalid_feed_returns_no_data(mock_get):
    mock_resp = MagicMock()
    mock_resp.content = b"not xml at all"
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp
    assert rss_read_impl("https://example.com/not-a-feed").startswith("NO_DATA:")
