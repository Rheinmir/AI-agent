"""Dashboard — 2 trang HTML dựng server-side (không SPA/JS framework, khớp quy ước "self-contained,
không phụ thuộc ngoài" của dự án): /monitor phân tích dữ liệu monitoring.sqlite3 (bao nhiêu lượt,
tool nào dùng nhiều, guardrail trip bao nhiêu lần, latency, theo session, xu hướng theo ngày, tỉ lệ
lỗi gần đây) + tóm tắt eval; /evaluate xem chi tiết từng golden trong eval-baseline.json + cảnh báo
nếu code đổi sau khi baseline được sinh. Trả lời trực tiếp yêu cầu "màn hình monitor để đưa ra được
dashboard phân tích được dữ liệu và eval được" (không phải slash-command, là 2 route HTTP) + "thêm
hết vào đi" (latency, per-session, xu hướng, cảnh báo lỗi, retention, cảnh báo eval lỗi thời).

KHÔNG có trong 2 trang này (có chủ đích, xem giải thích khi báo cáo lại cho người dùng):
- KHÔNG tự động gọi lại model để "chạy eval sống" — mỗi lần chạm `/evaluate` chỉ đọc file JSON tĩnh,
  không tốn API call thật. Muốn baseline mới phải chạy tay
  `harness/scripts/wikieval.py --write-baseline` — hành động tốn tiền/API thật không nên tự động
  hoá đằng sau 1 lần tải trang.
- KHÔNG bật tier-3 LLM-judge — `wikieval.config.yaml` cố ý để `judge.enabled:false`, đây là quyết
  định project đã có sẵn, không phải phạm vi của dashboard này.
- "Cảnh báo" ở đây chỉ là 1 badge/màu đổi TRÊN TRANG — không phải hệ thống notification thật (không
  gửi email/Slack), vì sandbox này không có kênh thông báo nào được cấu hình.
"""

import html
import json
import time
from pathlib import Path

from demo_agents.weather_agent.monitoring import (
    count_events_by_type,
    daily_event_counts,
    error_rate_recent,
    events_by_session,
    latency_stats,
    prune_old_events,
    recent_events,
    tool_usage_counts,
)

_REPO_ROOT = Path(__file__).parent.parent.parent
_EVAL_BASELINE_PATH = _REPO_ROOT / "harness" / "metrics" / "eval-baseline.json"
_BEHAVIOR_FILES = ["agent.py", "guardrails.py", "harness.py", "data_collector.py", "memory.py"]
_ERROR_RATE_WARN_THRESHOLD = 0.3

_STYLE = """
<style>
  :root{--bg:#fbfefc;--panel:#f5f5f7;--text:#0d0d0d;--dim:#6e6e80;--border:#e5e5e5;
    --accent:#10a37f;--danger:#b3261e;--danger-bg:#fdecea;--warn:#9a6700;--warn-bg:#fff6e0}
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;background:var(--bg);
    color:var(--text);padding:28px 32px 60px}
  h1{font-size:19px;margin:0 0 4px}
  .sub{color:var(--dim);font-size:12.5px;margin:0 0 24px}
  nav{display:flex;gap:14px;margin-bottom:22px}
  nav a{font-size:12.5px;color:var(--dim);text-decoration:none;padding:6px 12px;border-radius:8px;
    border:1px solid var(--border)}
  nav a.active{color:var(--accent);border-color:var(--accent);font-weight:600}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:26px}
  .card{background:var(--panel);border-radius:12px;padding:14px 16px}
  .card.warn{background:var(--warn-bg)}
  .card .n{font-size:24px;font-weight:700}
  .card.warn .n{color:var(--warn)}
  .card .l{font-size:11.5px;color:var(--dim);margin-top:2px}
  h2{font-size:14px;margin:26px 0 10px}
  table{width:100%;border-collapse:collapse;font-size:12.5px;background:var(--panel);border-radius:12px;
    overflow:hidden}
  th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--border);vertical-align:top}
  th{font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--dim);font-weight:700}
  tr:last-child td{border-bottom:none}
  .pill{display:inline-block;font-size:10.5px;font-weight:700;padding:2px 9px;border-radius:999px}
  .pill.pass{background:rgba(16,163,127,.12);color:var(--accent)}
  .pill.fail{background:var(--danger-bg);color:var(--danger)}
  code{background:var(--panel);padding:1px 5px;border-radius:5px;font-size:11.5px}
  .empty{color:var(--dim);font-size:12.5px;padding:14px 0}
  .asserts{font-size:11px;color:var(--dim)}
  .banner{border-radius:10px;padding:10px 14px;font-size:12.5px;margin-bottom:20px}
  .banner.warn{background:var(--warn-bg);color:var(--warn)}
  .chart{display:flex;align-items:flex-end;gap:4px;height:70px;background:var(--panel);
    border-radius:12px;padding:10px 12px}
  .chart .bar{flex:1;background:var(--accent);border-radius:3px 3px 0 0;min-height:2px;position:relative}
  .chart .bar .lbl{position:absolute;bottom:-16px;left:0;right:0;text-align:center;font-size:9px;
    color:var(--dim);white-space:nowrap}
  .note{font-size:11px;color:var(--dim);margin-top:6px}
</style>
"""

_NAV = """
<nav>
  <a href="/" >← Chat</a>
  <a href="/monitor" class="{monitor_active}">Monitor</a>
  <a href="/evaluate" class="{evaluate_active}">Evaluate</a>
  <a href="/wiki" class="{wiki_active}">Wiki</a>
</nav>
"""


def _nav(active):
    return _NAV.format(
        monitor_active="active" if active == "monitor" else "",
        evaluate_active="active" if active == "evaluate" else "",
        wiki_active="active" if active == "wiki" else "",
    )


def _e(text):
    return html.escape(str(text))


def _page(title, active, body):
    return (
        f"<!doctype html><html><head><meta charset='utf-8'><title>{_e(title)} — Weather Agent</title>"
        f"{_STYLE}</head><body>{_nav(active)}{body}</body></html>"
    )


def _read_eval_baseline():
    if not _EVAL_BASELINE_PATH.is_file():
        return None
    try:
        return json.loads(_EVAL_BASELINE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _read_eval_summary():
    data = _read_eval_baseline()
    if not data:
        return {"goldens": 0, "decided": 0, "passed": 0}
    return data.get("summary", {"goldens": 0, "decided": 0, "passed": 0})


def _eval_staleness_banner():
    """So ngày `generated_at` (date-only, xem wikieval.py) với ngày sửa gần nhất của các file ẢNH
    HƯỞNG HÀNH VI agent — cảnh báo NGÀY, không phải giờ chính xác (generated_at chỉ lưu ngày, không
    lưu giờ). Không phát hiện được nếu sửa code CÙNG NGÀY sau khi baseline sinh — nói rõ giới hạn
    này trong ghi chú hiển thị, không giả vờ chính xác hơn thật."""
    data = _read_eval_baseline()
    if not data or not data.get("generated_at"):
        return ""
    generated_date = data["generated_at"]
    newest_mtime = 0.0
    newest_file = None
    for fname in _BEHAVIOR_FILES:
        fpath = Path(__file__).parent / fname
        if fpath.is_file() and fpath.stat().st_mtime > newest_mtime:
            newest_mtime = fpath.stat().st_mtime
            newest_file = fname
    if not newest_file:
        return ""
    newest_date = time.strftime("%Y-%m-%d", time.localtime(newest_mtime))
    if newest_date > generated_date:
        return (
            f'<div class="banner warn">⚠️ Eval baseline sinh ngày {_e(generated_date)}, nhưng '
            f'<code>{_e(newest_file)}</code> đã sửa ngày {_e(newest_date)} — kết quả PASS/FAIL dưới '
            f"đây có thể KHÔNG còn phản ánh đúng hành vi hiện tại. Chạy lại "
            f"<code>harness/scripts/wikieval.py --write-baseline</code> để cập nhật (tốn API call "
            f"thật, không tự động).</div>"
        )
    return ""


def render_monitor_page():
    prune_old_events()  # retention: xoá sự kiện >30 ngày mỗi lần tải trang, không cần cron riêng

    counts = count_events_by_type()
    tools = tool_usage_counts()
    events = recent_events(limit=50)
    latency = latency_stats()
    err_recent = error_rate_recent(window=20)
    sessions = events_by_session()
    daily = daily_event_counts(days=14)

    total_requests = counts.get("agent_start", 0) + counts.get("harness_capability_shortcut", 0)
    guardrail_trips = counts.get("harness_guardrail_tripped", 0)
    capability_shortcuts = counts.get("harness_capability_shortcut", 0)
    errors = counts.get("harness_retries_exhausted", 0) + counts.get("harness_max_turns_exceeded", 0)
    eval_summary = _read_eval_summary()

    err_card_class = "card warn" if err_recent["rate"] > _ERROR_RATE_WARN_THRESHOLD else "card"
    req_latency = latency["request"]
    llm_latency = latency["llm_call"]

    cards = f"""
    <div class="cards">
      <div class="card"><div class="n">{total_requests}</div><div class="l">Tổng lượt hỏi</div></div>
      <div class="card"><div class="n">{guardrail_trips}</div><div class="l">Guardrail chặn</div></div>
      <div class="card"><div class="n">{capability_shortcuts}</div><div class="l">"Làm được gì" (Harness ngắn mạch)</div></div>
      <div class="card"><div class="n">{errors}</div><div class="l">Lỗi/hết retry</div></div>
      <div class="card"><div class="n">{eval_summary['passed']}/{eval_summary['goldens']}</div><div class="l">Eval passing</div></div>
      <div class="{err_card_class}"><div class="n">{err_recent['errors']}/{err_recent['total']}</div><div class="l">Lỗi trong {err_recent['window']} lượt gần nhất{' ⚠️' if err_recent['rate'] > _ERROR_RATE_WARN_THRESHOLD else ''}</div></div>
      <div class="card"><div class="n">{req_latency['avg_s'] if req_latency['avg_s'] is not None else '—'}{'s' if req_latency['avg_s'] is not None else ''}</div><div class="l">Latency TB / lượt ({req_latency['count']} lượt đo được)</div></div>
      <div class="card"><div class="n">{llm_latency['avg_s'] if llm_latency['avg_s'] is not None else '—'}{'s' if llm_latency['avg_s'] is not None else ''}</div><div class="l">Latency TB / lần gọi LLM ({llm_latency['count']} lần)</div></div>
    </div>
    """

    max_daily = max((c for _, c in daily), default=1)
    chart_bars = "".join(
        f'<div class="bar" style="height:{max(4, round(c / max_daily * 54))}px" title="{_e(day)}: {c}">'
        f'<span class="lbl">{_e(day[5:])}</span></div>'
        for day, c in daily
    ) or '<div class="empty">Chưa có dữ liệu</div>'
    chart = f'<div class="chart">{chart_bars}</div><p class="note">Số sự kiện/ngày, 14 ngày gần nhất (UTC).</p>' if daily else '<p class="empty">Chưa có dữ liệu xu hướng</p>'

    tools_rows = "".join(
        f"<tr><td><code>{_e(name)}</code></td><td>{count}</td></tr>"
        for name, count in sorted(tools.items(), key=lambda kv: -kv[1])
    ) or '<tr><td colspan="2" class="empty">Chưa có lượt gọi tool nào</td></tr>'

    session_rows = "".join(
        f"<tr><td><code>{_e(s['session_id'] or '(không rõ)')}</code></td><td>{s['events']}</td>"
        f"<td>{s['errors']}</td></tr>"
        for s in sessions
    ) or '<tr><td colspan="3" class="empty">Chưa có phiên nào</td></tr>'

    events_rows = "".join(
        f"<tr><td>{_e(e['event'])}</td><td><code>{_e((e['session_id'] or '')[:12])}</code></td>"
        f"<td><code>{_e(json.dumps(e['detail'], ensure_ascii=False))[:100]}</code></td></tr>"
        for e in events
    ) or '<tr><td colspan="3" class="empty">Chưa có sự kiện nào — thử hỏi thời tiết trên trang Chat trước</td></tr>'

    body = f"""
    <h1>Monitor</h1>
    <p class="sub">Phân tích hành vi agent thật, đọc từ <code>monitoring.sqlite3</code> (ghi qua
    lifecycle hooks thật của Agents SDK — không phải log tự chế). Giữ tối đa 30 ngày dữ liệu (tự
    dọn mỗi lần tải trang này).</p>
    {_eval_staleness_banner()}
    {cards}
    <h2>Xu hướng 14 ngày</h2>
    {chart}
    <h2>Tool được dùng</h2>
    <table><thead><tr><th>Tool</th><th>Số lần gọi</th></tr></thead><tbody>{tools_rows}</tbody></table>
    <h2>Theo phiên (session)</h2>
    <table><thead><tr><th>Session ID</th><th>Số sự kiện</th><th>Lỗi/guardrail chặn</th></tr></thead>
    <tbody>{session_rows}</tbody></table>
    <h2>50 sự kiện gần nhất</h2>
    <table><thead><tr><th>Sự kiện</th><th>Session</th><th>Chi tiết</th></tr></thead><tbody>{events_rows}</tbody></table>
    """
    return _page("Monitor", "monitor", body)


def render_evaluate_page():
    data = _read_eval_baseline()
    if not data:
        goldens = {}
        summary = {"goldens": 0, "decided": 0, "passed": 0}
        generated_at = None
    else:
        goldens = data.get("goldens", {})
        summary = data.get("summary", {"goldens": 0, "decided": 0, "passed": 0})
        generated_at = data.get("generated_at")

    rows = ""
    for name, g in sorted(goldens.items()):
        pill = '<span class="pill pass">PASS</span>' if g.get("pass") else '<span class="pill fail">FAIL</span>'
        asserts = "<br>".join(_e(a) for a in g.get("asserts", []))
        rows += (
            f"<tr><td><code>{_e(name)}</code></td><td>{pill}</td>"
            f"<td>{_e(g.get('decided_by', '—'))}</td>"
            f"<td class='asserts'>{asserts}</td></tr>"
        )
    if not rows:
        rows = '<tr><td colspan="4" class="empty">Chưa có harness/metrics/eval-baseline.json — chạy harness/scripts/wikieval.py --write-baseline trước</td></tr>'

    body = f"""
    <h1>Evaluate</h1>
    <p class="sub">Baseline tất định (wikieval, tier-1 asserts) — sinh lúc {_e(generated_at or '—')}.
    Không phải LLM-judge (tier-3 đang tắt có chủ đích, xem wikieval.config.yaml), mọi kết quả tái
    lập được 100%. Trang này CHỈ đọc file JSON tĩnh — không tự gọi lại model.</p>
    {_eval_staleness_banner()}
    <div class="cards">
      <div class="card"><div class="n">{summary.get('passed', 0)}/{summary.get('goldens', 0)}</div><div class="l">Passing</div></div>
      <div class="card"><div class="n">{summary.get('decided', 0)}</div><div class="l">Đã quyết định (tier-1)</div></div>
    </div>
    <h2>Chi tiết từng golden</h2>
    <table><thead><tr><th>Golden</th><th>Kết quả</th><th>Chấm bởi</th><th>Asserts</th></tr></thead>
    <tbody>{rows}</tbody></table>
    <p class="note">Muốn baseline mới: chạy tay
    <code>python3 harness/scripts/wikieval.py --outputs &lt;file&gt; --write-baseline</code> — tốn
    API call thật cho mỗi golden agent-level, không tự động hoá đằng sau trang này.</p>
    """
    return _page("Evaluate", "evaluate", body)
