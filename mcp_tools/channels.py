"""3 kênh Agent-Reach đã cài/xác nhận hoạt động nhưng CHƯA wire vào tool nào (xem README.md § Full
Agent-Reach capability) — GitHub, YouTube, RSS. KHÔNG PHẢI MCP (khác fetch_server.py/exa_server.py)
— đây là plain Python function shell ra CLI đã cài sẵn (gh, yt-dlp) hoặc dùng thư viện Python thuần
(feedparser), dùng chung cho weather_agent VÀ devops_agent qua @function_tool trong agent.py của mỗi
agent (không phải mcp_servers=[...]).

Cùng kỷ luật NO_DATA đã áp dụng xuyên suốt project (get_weather/get_cheatsheet) — lỗi/không có dữ
liệu trả 'NO_DATA:<lý do>', KHÔNG bịa kết quả thay thế, KHÔNG raise exception làm crash tool call.

CHẠY ĐƯỢC dưới BẤT KỲ Python version nào (không cần 3.10+ như MCP) — chỉ dùng subprocess/thư viện
chuẩn + feedparser (thêm vào requirements.txt của từng agent)."""

import json
import re
import subprocess
import tempfile
from pathlib import Path

_YT_DLP_BIN = Path(__file__).parent / "servers-venv" / "bin" / "yt-dlp"


def github_search_impl(query: str, limit: int = 5) -> str:
    """Tìm kiếm repo GitHub công khai qua `gh search repos` — CẦN `gh` CLI cài + authenticated trên
    máy chạy agent (KHÔNG bundle theo agent, khác mcp_tools/servers-venv/ — đây là hệ thống-wide,
    xem README.md). Trả 'NO_DATA:<lý do>' nếu gh chưa cài, lỗi mạng, hoặc không có kết quả."""
    try:
        result = subprocess.run(
            [
                "gh", "search", "repos", query,
                "--limit", str(limit),
                "--json", "fullName,description,url,stargazersCount",
            ],
            capture_output=True, text=True, timeout=20,
        )
    except FileNotFoundError:
        return "NO_DATA:gh CLI chưa cài trên máy này"
    except subprocess.TimeoutExpired:
        return "NO_DATA:gh search timeout"
    if result.returncode != 0:
        return f"NO_DATA:gh search lỗi — {result.stderr.strip()[:200]}"
    try:
        repos = json.loads(result.stdout)
    except json.JSONDecodeError:
        return "NO_DATA:gh trả kết quả không parse được"
    if not repos:
        return f"NO_DATA:không tìm thấy repo nào cho '{query}'"
    lines = [
        f"- {r['fullName']} (⭐{r['stargazersCount']}) — {r.get('description') or '(không mô tả)'} — {r['url']}"
        for r in repos
    ]
    return "\n".join(lines)


def youtube_transcript_impl(url: str, lang: str = "en") -> str:
    """Tải phụ đề (transcript) 1 video YouTube qua yt-dlp (mcp_tools/servers-venv/bin/yt-dlp — CẦN
    setup servers-venv/, xem README.md), ưu tiên phụ đề THẬT (manual) trước auto-generated, parse
    VTT thành text thuần, xoá file tạm ngay sau. Trả 'NO_DATA:<lý do>' nếu không có phụ đề (ngôn ngữ
    đó), yt-dlp chưa cài, hoặc lỗi mạng/video không tồn tại."""
    if not _YT_DLP_BIN.is_file():
        return "NO_DATA:yt-dlp chưa cài trong mcp_tools/servers-venv/ — xem README.md"
    with tempfile.TemporaryDirectory() as tmpd:
        try:
            subprocess.run(
                [
                    str(_YT_DLP_BIN), "--write-subs", "--write-auto-sub", "--sub-lang", lang,
                    "--skip-download", "--sub-format", "vtt", "--no-warnings",
                    "-o", f"{tmpd}/%(id)s.%(ext)s", url,
                ],
                capture_output=True, text=True, timeout=60,
            )
        except subprocess.TimeoutExpired:
            return "NO_DATA:yt-dlp timeout khi tải phụ đề"
        vtt_files = list(Path(tmpd).glob("*.vtt"))
        if not vtt_files:
            return f"NO_DATA:không tìm thấy phụ đề ({lang}) cho video này"
        raw = vtt_files[0].read_text(encoding="utf-8")
    return _parse_vtt(raw) or "NO_DATA:phụ đề rỗng sau khi parse"


def _parse_vtt(raw: str) -> str:
    """Rút gọn file VTT thành text thuần — bỏ header/timestamp/cue-number/tag inline, khử trùng lặp
    dòng liên tiếp (auto-caption VTT hay lặp dòng khi cuộn phụ đề)."""
    lines, seen = [], set()
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:")) or "-->" in line:
            continue
        if re.fullmatch(r"\d+", line):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        if line and line not in seen:
            lines.append(line)
            seen.add(line)
    return " ".join(lines)


def rss_read_impl(feed_url: str, limit: int = 5) -> str:
    """Đọc N mục mới nhất của 1 RSS/Atom feed qua feedparser (thư viện Python thuần, không cần
    servers-venv/). Trả 'NO_DATA:<lý do>' nếu URL không phải feed hợp lệ hoặc feed rỗng.

    Fetch bằng `requests` rồi đưa RAW BYTES cho feedparser.parse() — KHÔNG đưa thẳng URL cho
    feedparser tự fetch. Bug thật gặp lúc build: feedparser tự fetch dùng `urllib` (context SSL
    mặc định của hệ thống), gặp lỗi `CERTIFICATE_VERIFY_FAILED` trên máy Python 3.14 cài qua
    Homebrew (thiếu liên kết tới bundle cert của `certifi`) — trong khi `requests` (dùng bundle
    `certifi` riêng, đã verify hoạt động ổn định xuyên suốt project qua weather_agent) fetch được
    bình thường. Tránh để feedparser tự làm network I/O."""
    import feedparser
    import requests

    try:
        resp = requests.get(feed_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except requests.RequestException as e:
        return f"NO_DATA:lỗi tải feed {feed_url} — {e}"

    parsed = feedparser.parse(resp.content)
    if parsed.bozo and not parsed.entries:
        return f"NO_DATA:không đọc được RSS/Atom feed tại {feed_url}"
    entries = parsed.entries[:limit]
    if not entries:
        return f"NO_DATA:feed không có mục nào ({feed_url})"
    title = parsed.feed.get("title", feed_url)
    lines = [f"Feed: {title}"]
    for e in entries:
        lines.append(f"- {e.get('title', '(không tiêu đề)')} ({e.get('link', '')}) — {e.get('published', '')}")
    return "\n".join(lines)
