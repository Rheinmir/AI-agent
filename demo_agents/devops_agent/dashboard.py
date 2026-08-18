"""Dashboard — PORT TRỰC TIẾP `/monitor` từ demo_agents/weather_agent/dashboard.py (đã chạy ổn
định, có test) — chỉ đổi accent màu (Kubernetes blue #326CE5, khớp design.md đã khoá của agent
này) và bỏ phần `/evaluate` (agent này CHƯA có golden eval riêng — `wikieval.py` mới chỉ phủ
weather_agent, xem wiki/log.md). Xem docstring gốc ở weather_agent/dashboard.py cho giải thích đầy
đủ những gì CHỦ Ý không làm (không tự chạy lại model, không tự động hoá baseline)."""

import html
import json
from pathlib import Path

from demo_agents.devops_agent.monitoring import (
    count_events_by_type,
    daily_event_counts,
    error_rate_recent,
    events_by_session,
    latency_stats,
    prune_old_events,
    recent_events,
    tool_usage_counts,
)

_ERROR_RATE_WARN_THRESHOLD = 0.3

_STYLE = """
<style>
  :root{--bg:#fbfefc;--panel:#f5f5f7;--text:#0d0d0d;--dim:#6e6e80;--border:#e5e5e5;
    --accent:#326CE5;--danger:#b3261e;--danger-bg:#fdecea;--warn:#9a6700;--warn-bg:#fff6e0}
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
  code{background:var(--panel);padding:1px 5px;border-radius:5px;font-size:11.5px}
  .empty{color:var(--dim);font-size:12.5px;padding:14px 0}
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
  <a href="/wiki" class="{wiki_active}">Wiki</a>
</nav>
"""


def _nav(active):
    return _NAV.format(
        monitor_active="active" if active == "monitor" else "",
        wiki_active="active" if active == "wiki" else "",
    )


def _e(text):
    return html.escape(str(text))


def _page(title, active, body):
    return (
        f"<!doctype html><html><head><meta charset='utf-8'><title>{_e(title)} — DevOps Agent</title>"
        f"{_STYLE}</head><body>{_nav(active)}{body}</body></html>"
    )


def render_monitor_page():
    prune_old_events()

    counts = count_events_by_type()
    tools = tool_usage_counts()
    events = recent_events(limit=50)
    latency = latency_stats()
    err_recent = error_rate_recent(window=20)
    sessions = events_by_session()
    daily = daily_event_counts(days=14)

    total_requests = counts.get("agent_start", 0)
    guardrail_trips = counts.get("harness_guardrail_tripped", 0)
    errors = counts.get("harness_max_turns_exceeded", 0)

    err_card_class = "card warn" if err_recent["rate"] > _ERROR_RATE_WARN_THRESHOLD else "card"
    req_latency = latency["request"]
    llm_latency = latency["llm_call"]

    cards = f"""
    <div class="cards">
      <div class="card"><div class="n">{total_requests}</div><div class="l">Tổng lượt hỏi</div></div>
      <div class="card"><div class="n">{guardrail_trips}</div><div class="l">Guardrail chặn</div></div>
      <div class="card"><div class="n">{errors}</div><div class="l">Lỗi/hết vòng lặp</div></div>
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
    ) or '<tr><td colspan="3" class="empty">Chưa có sự kiện nào — thử hỏi trên trang Chat trước</td></tr>'

    body = f"""
    <h1>Monitor</h1>
    <p class="sub">Phân tích hành vi agent thật, đọc từ <code>monitoring.sqlite3</code> (ghi qua
    lifecycle hooks thật của Agents SDK — không phải log tự chế). Giữ tối đa 30 ngày dữ liệu (tự
    dọn mỗi lần tải trang này). Cột "Chi tiết" của tool_call/tool_result gồm ĐẦY ĐỦ args/output
    (không chỉ tên tool) — xem toàn bộ 1 lượt bằng cách lọc theo session ID.</p>
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
