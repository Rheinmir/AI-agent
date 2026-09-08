"""Thư viện render wiki DÙNG CHUNG — 1 nguồn sự thật cho MỌI route `/wiki` trong dự án: browser
độc lập của project (`llmwiki/wiki_browser.py`, đọc `llmwiki/wiki/`) VÀ route `/wiki` gắn vào từng
agent (`demo_agents/{weather,devops}_agent/chatdemo.py`, mỗi agent đọc `wiki/` CỦA RIÊNG NÓ — xem
lý do tách vật lý trong `wiki/log.md` entry "wiki-per-agent-memory"). KHÔNG có state/global path
cứng — mọi hàm nhận `wiki_root` tường minh, để 3 nơi gọi module này với 3 thư mục KHÁC NHAU mà
không đụng nhau.

Đọc TRỰC TIẾP từ đĩa mỗi lần gọi (không cache) — đúng triết lý "human CRUD-able mà agent nạp được
cùng": sửa file `.md` bằng tay/git, lần gọi kế tiếp phản ánh ngay, không có bản sao lệch pha."""

import html
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import markdown
import yaml

_VALIDATOR_PATH = Path(__file__).resolve().parent.parent / "harness" / "poc-vendor-neutral" / "bin" / "llmwiki-validate.py"
_VI_TRANSLIT = str.maketrans({"đ": "d", "Đ": "D"})
_ORIGIN_SECTION_RE = re.compile(r"^##\s+Origin\b", re.MULTILINE)

TYPE_LABELS = {
    "concept": "Concepts",
    "source": "Sources",
    "entity": "Entities",
    "draft": "Drafts",
    "eval": "Evals",
}
TYPE_ORDER = ["concept", "source", "entity", "eval", "draft"]

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]")


def iter_md_files(wiki_root):
    """Bỏ qua `index.md`/`log.md` VÀ mọi file `<slug>-raw.md` — bản raw (nguồn thô chưa qua lint,
    xem wiki/concepts/click-depth-pyramid.md) không xuất hiện trong index/sidebar/wikilink/tra cứu
    tự động (data_collector.py, librarian search) mặc định — CHỈ tới được qua link "Xem bản gốc"
    tường minh trên trang linted tương ứng (render_wiki_page), đúng rule "đỉnh pyramid = ít click
    nhất". Muốn đọc raw trực tiếp vẫn được (render_wiki_page/resolve_safe_path không lọc theo hàm
    này) — chỉ ẩn khỏi các danh sách TỰ ĐỘNG duyệt qua toàn bộ wiki_root."""
    for p in sorted(Path(wiki_root).rglob("*.md")):
        rel = p.relative_to(wiki_root)
        if rel.name in ("index.md", "log.md"):
            continue
        if rel.stem.endswith("-raw"):
            continue
        yield p, rel


def parse_frontmatter(text):
    """Trả (meta dict, body sau frontmatter). meta rỗng nếu không có/không parse được — KHÔNG
    raise, để 1 file lỗi frontmatter không sập cả trang danh sách."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, text[m.end():]


def build_index(wiki_root):
    """Quét TOÀN BỘ wiki_root 1 lần mỗi lời gọi — trả (pages, slug_to_rel). aliases (nếu frontmatter
    có field `aliases:`) cũng được đăng ký vào slug_to_rel, để [[hanoi]] và [[ha-noi]] cùng trỏ
    đúng 1 trang nếu trang đó khai `aliases: [hanoi, ha-noi]`."""
    pages = []
    slug_to_rel = {}
    for p, rel in iter_md_files(wiki_root):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        meta, _ = parse_frontmatter(text)
        title = meta.get("title") or rel.stem
        pages.append({"rel": str(rel), "meta": meta, "title": title})
        slug_to_rel[rel.stem] = str(rel)
        for alias in meta.get("aliases") or []:
            slug_to_rel[str(alias).strip()] = str(rel)
    return pages, slug_to_rel


def resolve_wikilinks(html_text, slug_to_rel, prefix="/wiki"):
    """Thay [[slug]]/[[slug|label]] thành <a> nếu slug có trong slug_to_rel, else <span
    class="wl-missing"> — KHÔNG giả vờ trang đó tồn tại khi chưa có."""

    def _sub(m):
        slug, label = m.group(1).strip(), m.group(2)
        display = html.escape((label or slug).strip())
        rel = slug_to_rel.get(slug)
        if rel is None:
            return f'<span class="wl-missing" title="Chưa có trang &quot;{html.escape(slug)}&quot;">{display}</span>'
        return f'<a class="wl" href="{prefix}/{rel}">{display}</a>'

    return _WIKILINK_RE.sub(_sub, html_text)


def render_markdown(body, slug_to_rel, prefix="/wiki"):
    rendered = markdown.markdown(body, extensions=["extra", "sane_lists", "toc"], output_format="html5")
    return resolve_wikilinks(rendered, slug_to_rel, prefix)


def sidebar_html(pages, active_rel, prefix="/wiki"):
    grouped = {}
    for pg in pages:
        t = pg["meta"].get("type") or "other"
        grouped.setdefault(t, []).append(pg)
    parts = ['<input id="q" type="text" placeholder="Lọc theo tên…" autocomplete="off">']
    order = TYPE_ORDER + sorted(k for k in grouped if k not in TYPE_ORDER)
    for t in order:
        items = grouped.get(t)
        if not items:
            continue
        label = TYPE_LABELS.get(t, t.capitalize())
        parts.append(f'<div class="grp"><div class="grp-h">{html.escape(label)} <span class="cnt">{len(items)}</span></div><ul>')
        for pg in sorted(items, key=lambda x: x["title"].lower()):
            cls = "active" if pg["rel"] == active_rel else ""
            parts.append(
                f'<li><a class="{cls}" href="{prefix}/{pg["rel"]}" data-title="{html.escape(pg["title"].lower())}">'
                f'{html.escape(pg["title"])}</a></li>'
            )
        parts.append("</ul></div>")
    return "\n".join(parts)


PAGE_SHELL = """<!doctype html><html lang="vi"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — {brand}</title>
<meta name="description" content="Trình duyệt nội dung wiki — human CRUD-able, agent nạp cùng nguồn.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%23{accent_hex}'/%3E%3C/svg%3E">
<style>
:root{{--ink:#0f0f12;--ink2:#4a4a55;--border:rgba(30,90,170,.16);--accent:#{accent_hex}}}
*{{box-sizing:border-box}} html,body{{margin:0;height:100%}}
body{{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','Helvetica Neue',Roboto,'Segoe UI',sans-serif;
  color:var(--ink);display:flex;height:100vh;overflow:hidden;
  background:radial-gradient(900px 500px at 12% -10%,rgba(10,132,255,.10),transparent 60%),
    radial-gradient(700px 420px at 95% 15%,rgba(88,86,214,.08),transparent 55%),
    linear-gradient(180deg,#f7fbff 0%,#eaf2fd 100%)}}
nav{{width:260px;flex-shrink:0;overflow-y:auto;padding:16px 12px;
  background:rgba(255,255,255,.55);backdrop-filter:blur(16px);border-right:1px solid var(--border)}}
nav h1{{font-size:14px;margin:0 6px 12px;letter-spacing:-.01em;color:#1d1d1f}}
nav h1 a{{color:inherit;text-decoration:none}}
#q{{width:100%;padding:7px 10px;border-radius:9px;border:1px solid var(--border);font-size:12.5px;
  background:rgba(255,255,255,.85);color:var(--ink);margin-bottom:10px}}
#q:focus{{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(10,132,255,.15)}}
.grp-h{{font-size:11px;font-weight:700;color:var(--ink2);text-transform:uppercase;letter-spacing:.04em;
  margin:12px 6px 4px;display:flex;justify-content:space-between}}
.cnt{{opacity:.55;font-weight:500}}
nav ul{{list-style:none;margin:0;padding:0}}
nav li a{{display:block;padding:6px 8px;border-radius:8px;font-size:13px;color:var(--ink2);
  text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
nav li a:hover{{background:rgba(10,132,255,.08);color:var(--accent)}}
nav li a.active{{background:rgba(10,132,255,.12);color:var(--accent);font-weight:600}}
main{{flex:1;overflow-y:auto;padding:36px 48px}}
.doc{{max-width:760px;margin:0 auto;background:rgba(255,255,255,.88);backdrop-filter:blur(4px);
  border:1px solid var(--border);border-radius:16px;padding:32px 40px;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.85),0 4px 20px rgba(20,40,90,.08)}}
.meta{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}}
.badge{{font-size:11px;font-weight:700;padding:3px 9px;border-radius:999px;background:rgba(10,132,255,.1);color:var(--accent)}}
.tag{{font-size:11px;padding:3px 9px;border-radius:999px;background:rgba(0,0,0,.05);color:var(--ink2)}}
.doc h1{{font-size:24px;margin:0 0 6px;letter-spacing:-.01em}}
.doc h2{{font-size:17px;margin:28px 0 10px;padding-top:14px;border-top:1px solid var(--border)}}
.doc h3{{font-size:14.5px;margin:20px 0 8px}}
.doc p,.doc li{{font-size:14px;line-height:1.7;color:#1d1d1f}}
.doc code{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;
  background:rgba(0,0,0,.05);border-radius:4px;padding:1px 5px}}
.doc pre{{background:rgba(0,0,0,.04);border-radius:10px;padding:14px 16px;overflow-x:auto}}
.doc pre code{{background:none;padding:0}}
.doc table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:13px}}
.doc th,.doc td{{border:1px solid var(--border);padding:6px 10px;text-align:left}}
.doc th{{background:rgba(10,132,255,.06)}}
.doc a.wl{{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(10,132,255,.3)}}
.doc a.wl:hover{{border-bottom-color:var(--accent)}}
.wl-missing{{color:#b3261e;border-bottom:1px dashed #b3261e;cursor:help}}
.welcome{{font-size:14px;line-height:1.8;color:var(--ink2)}}
.raw-link{{font-size:12px;color:var(--ink2);margin:2px 0 18px}}
.raw-link a{{color:var(--ink2);text-decoration:underline}}
.raw-link a:hover{{color:var(--accent)}}
::-webkit-scrollbar{{width:10px}} ::-webkit-scrollbar-thumb{{background:rgba(10,132,255,.25);border-radius:8px;background-clip:content-box;border:2px solid transparent}}
</style></head><body>
<nav><h1><a href="{prefix}">{brand_icon} {brand}</a></h1>{sidebar}</nav>
<main><div class="doc">{content}</div></main>
<script>
const q = document.getElementById('q');
q.addEventListener('input', () => {{
  const v = q.value.trim().toLowerCase();
  document.querySelectorAll('nav li').forEach(li => {{
    const a = li.querySelector('a');
    li.style.display = !v || a.dataset.title.includes(v) ? '' : 'none';
  }});
}});
</script></body></html>"""


def welcome_html(pages, brand):
    return (
        f'<div class="welcome"><h1 style="font-size:22px;color:#1d1d1f">{html.escape(brand)}</h1>'
        f"<p>{len(pages)} trang — chọn 1 chủ đề ở sidebar bên trái để xem.</p>"
        "<p>Đây là view ĐỌC-only, đọc trực tiếp từ file <code>.md</code> trên đĩa mỗi lần tải "
        "trang — sửa file bằng bất kỳ editor/git nào (con người) hoặc agent ghi trực tiếp, "
        "reload trang này sẽ luôn phản ánh đúng bản mới nhất, không có bản sao/cache riêng.</p></div>"
    )


def render_index_page(wiki_root, brand, prefix="/wiki", accent_hex="0a84ff", brand_icon="📚",
                       shell=None, crud=False, **shell_vars):
    """`shell` (mặc định PAGE_SHELL — macOS-glass, dùng cho llmwiki/wiki_browser.py đứng độc lập)
    cho phép caller khác truyền 1 template khác + biến riêng qua `shell_vars` (vd
    CHAT_THEMED_SHELL — khớp design token/nav của app chat đang mount route này, xem
    demo_agents/{weather,devops}_agent/chatdemo.py) — KHÔNG đổi behavior mặc định của caller cũ.
    `crud=True` chèn nút "+ Trang mới" (chỉ có ý nghĩa cùng CHAT_THEMED_SHELL, wiki dự án không
    bật cờ này nên vẫn giữ đúng "chỉ 1 VIEW đọc" như thiết kế ban đầu)."""
    pages, _ = build_index(wiki_root)
    content = welcome_html(pages, brand)
    if crud:
        content += f'<div class="crud-actions"><a class="btn" href="{prefix}/new">+ Trang mới</a></div>'
    tpl = shell or PAGE_SHELL
    fmt = dict(
        title=brand, brand=brand, accent_hex=accent_hex, prefix=prefix, brand_icon=brand_icon,
        sidebar=sidebar_html(pages, None, prefix), content=content,
    )
    fmt.update(shell_vars)
    return tpl.format(**fmt)


def _raw_sibling_html(target, rel, prefix):
    """Xem wiki/concepts/click-depth-pyramid.md — trang linted chỉ CHỈ RA raw bằng 1 link nhỏ (thêm
    1 click mới thấy), trang raw chỉ CHỈ NGƯỢC LẠI về bản linted — không nhân đôi nội dung, không
    hiện cả 2 cùng lúc."""
    rel = str(rel)
    if target.stem.endswith("-raw"):
        linted_rel = rel[: -len("-raw.md")] + ".md"
        linted_target = target.with_name(target.stem[: -len("-raw")] + ".md")
        if linted_target.is_file():
            return (
                f'<div class="raw-link">Đây là bản GỐC (raw) chưa qua lint — '
                f'<a href="{prefix}/{linted_rel}">xem bản đã biên tập</a>.</div>'
            )
        return ""
    raw_rel = rel[: -len(".md")] + "-raw.md"
    raw_target = target.with_name(target.stem + "-raw.md")
    if raw_target.is_file():
        return f'<div class="raw-link"><a href="{prefix}/{raw_rel}">Xem bản gốc (raw)</a></div>'
    return ""


def render_wiki_page(wiki_root, rel, brand, prefix="/wiki", accent_hex="0a84ff", brand_icon="📚",
                      shell=None, crud=False, **shell_vars):
    """Trả (status, html_body). rel PHẢI đã được validate nằm trong wiki_root bởi caller (xem
    resolve_safe_path) — hàm này không tự kiểm path traversal, chỉ render. `shell`/`shell_vars`/
    `crud`: xem render_index_page."""
    target = Path(wiki_root) / rel
    if not target.is_file() or target.suffix != ".md":
        return 404, f"<h1>404</h1><p>Không có trang <code>{html.escape(rel)}</code>.</p>"
    pages, slug_to_rel = build_index(wiki_root)
    text = target.read_text(encoding="utf-8")
    meta, body_text = parse_frontmatter(text)
    title = meta.get("title") or target.stem
    body_html = render_markdown(body_text, slug_to_rel, prefix)
    meta_html = f'<div class="meta"><span class="badge">{html.escape(str(meta.get("type", "?")))}</span>'
    for tag in meta.get("tags") or []:
        meta_html += f'<span class="tag">{html.escape(str(tag))}</span>'
    if meta.get("timestamp"):
        meta_html += f'<span class="tag">{html.escape(str(meta["timestamp"]))}</span>'
    meta_html += "</div>"
    content = f"<h1>{html.escape(title)}</h1>{meta_html}"
    if crud:
        content += (
            f'<div class="crud-actions"><a class="btn-ghost" href="{prefix}/edit/{rel}">✎ Sửa</a>'
            f'<form method="post" action="{prefix}/delete/{rel}" '
            f'onsubmit="return confirm(\'Xoá trang này? Không thể hoàn tác.\');">'
            f'<button type="submit" class="btn-danger">🗑 Xoá</button></form></div>'
        )
    content += _raw_sibling_html(target, rel, prefix)
    content += body_html
    tpl = shell or PAGE_SHELL
    fmt = dict(
        title=title, brand=brand, accent_hex=accent_hex, prefix=prefix, brand_icon=brand_icon,
        sidebar=sidebar_html(pages, rel, prefix), content=content,
    )
    fmt.update(shell_vars)
    body = tpl.format(**fmt)
    return 200, body


CHAT_THEMED_SHELL = """<!doctype html><html lang="vi"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — {brand}</title>
<meta name="description" content="Wiki memory của agent — human CRUD-able, agent nạp cùng nguồn.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%23{accent_hex}'/%3E%3C/svg%3E">
<style>
:root{{--bg:{bg};--panel:{panel};--text:{text};--dim:{dim};--border:{border};--accent:{accent}}}
*{{box-sizing:border-box}} html,body{{margin:0;height:100%}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  background:var(--bg);color:var(--text);display:flex;flex-direction:column;height:100vh;overflow:hidden}}
header{{padding:20px 32px 0;flex-shrink:0}}
h1{{font-size:19px;margin:0 0 4px}}
.sub{{color:var(--dim);font-size:12.5px;margin:0 0 16px}}
nav{{display:flex;gap:14px}}
nav a{{font-size:12.5px;color:var(--dim);text-decoration:none;padding:6px 12px;border-radius:8px;border:1px solid var(--border)}}
nav a.active{{color:var(--accent);border-color:var(--accent);font-weight:600}}
.layout{{flex:1;display:flex;overflow:hidden;padding:16px 32px 32px;gap:20px;min-height:0}}
aside{{width:220px;flex-shrink:0;overflow-y:auto;background:var(--panel);border-radius:12px;padding:14px 10px}}
#q{{width:100%;padding:7px 10px;border-radius:8px;border:1px solid var(--border);font-size:12.5px;
  background:var(--bg);color:var(--text);margin-bottom:10px}}
#q:focus{{outline:none;border-color:var(--accent)}}
.grp-h{{font-size:10.5px;font-weight:700;color:var(--dim);text-transform:uppercase;letter-spacing:.04em;
  margin:12px 6px 4px;display:flex;justify-content:space-between}}
.cnt{{opacity:.6;font-weight:500}}
aside ul{{list-style:none;margin:0;padding:0}}
aside li a{{display:block;padding:6px 8px;border-radius:8px;font-size:12.5px;color:var(--text);
  text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
aside li a:hover{{background:var(--border)}}
aside li a.active{{background:rgba(0,0,0,.06);color:var(--accent);font-weight:600}}
main{{flex:1;overflow-y:auto}}
.doc{{max-width:760px;background:var(--panel);border-radius:12px;padding:28px 34px}}
.meta{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}}
.badge{{font-size:10.5px;font-weight:700;padding:3px 9px;border-radius:999px;background:rgba(0,0,0,.06);color:var(--accent)}}
.tag{{font-size:10.5px;padding:3px 9px;border-radius:999px;background:var(--bg);color:var(--dim);border:1px solid var(--border)}}
.doc h1{{font-size:22px;margin:0 0 6px}}
.doc h2{{font-size:15px;margin:24px 0 8px;padding-top:12px;border-top:1px solid var(--border)}}
.doc h3{{font-size:13.5px;margin:18px 0 6px}}
.doc p,.doc li{{font-size:13.5px;line-height:1.7}}
.doc code{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;
  background:var(--bg);border-radius:4px;padding:1px 5px}}
.doc pre{{background:var(--bg);border-radius:10px;padding:14px 16px;overflow-x:auto;border:1px solid var(--border)}}
.doc pre code{{background:none;padding:0}}
.doc table{{border-collapse:collapse;width:100%;margin:12px 0;font-size:12.5px}}
.doc th,.doc td{{border:1px solid var(--border);padding:6px 10px;text-align:left}}
.doc th{{background:var(--bg)}}
.doc a.wl{{color:var(--accent);text-decoration:none;border-bottom:1px solid var(--accent)}}
.wl-missing{{color:#b3261e;border-bottom:1px dashed #b3261e;cursor:help}}
.welcome{{font-size:13.5px;line-height:1.8;color:var(--dim)}}
.raw-link{{font-size:12px;color:var(--dim);margin:2px 0 18px}}
.raw-link a{{color:var(--dim);text-decoration:underline}}
.raw-link a:hover{{color:var(--accent)}}
::-webkit-scrollbar{{width:9px}} ::-webkit-scrollbar-thumb{{background:var(--border);border-radius:8px;
  background-clip:content-box;border:2px solid transparent}}
/* Reset native <button> chrome TRƯỚC KHI khai .btn* — Chrome/Safari/Firefox mỗi hãng vẽ thêm
   padding/border/shadow "chìm" riêng cho <button> mà css padding/border khai sau đó KHÔNG thay thế
   hết (chỉ cộng thêm lên trên), nên <button class="btn-danger"> luôn to/lệch hơn <a class="btn">
   dù cùng 1 khối khai báo — phải appearance:none trước, coi <button> như 1 box CSS thuần. */
button{{appearance:none;-webkit-appearance:none;-moz-appearance:none;margin:0;box-sizing:border-box}}
button::-moz-focus-inner{{border:0;padding:0}}
.crud-actions{{display:flex;align-items:center;gap:8px;margin:2px 0 18px}}
.crud-actions form{{display:inline;margin:0}}
.btn,.btn-ghost,.btn-danger{{font:inherit;font-size:12.5px;line-height:1.3;font-weight:600;
  padding:7px 14px;margin:0;box-sizing:border-box;vertical-align:middle;
  border-radius:8px;border:1px solid var(--border);cursor:pointer;text-decoration:none;
  display:inline-flex;align-items:center;gap:4px;background:var(--bg);color:var(--text)}}
.btn{{background:var(--accent);border-color:var(--accent);color:#fff}}
.btn:hover{{opacity:.88}}
.btn-ghost:hover{{border-color:var(--accent);color:var(--accent)}}
.btn-danger{{color:#b3261e;border-color:#e5c2be}}
.btn-danger:hover{{background:#fdecea}}
.btn:focus-visible,.btn-ghost:focus-visible,.btn-danger:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
.err{{background:#fdecea;color:#b3261e;border-radius:8px;padding:10px 14px;font-size:12.5px;margin-bottom:16px}}
form{{display:flex;flex-direction:column;gap:14px;margin-top:10px}}
form label{{display:flex;flex-direction:column;gap:6px;font-size:12.5px;color:var(--dim);font-weight:600}}
form input[type=text],form select,form textarea{{font:inherit;font-size:13.5px;color:var(--text);
  background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:8px 10px;
  box-sizing:border-box;width:100%}}
form select{{appearance:none;-webkit-appearance:none;-moz-appearance:none;cursor:pointer;
  background-image:linear-gradient(45deg,transparent 50%,var(--dim) 50%),
    linear-gradient(135deg,var(--dim) 50%,transparent 50%);
  background-position:calc(100% - 18px) 16px,calc(100% - 13px) 16px;
  background-size:5px 5px,5px 5px;background-repeat:no-repeat;padding-right:32px}}
form textarea{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;resize:vertical}}
form input:focus,form select:focus,form textarea:focus{{outline:none;border-color:var(--accent)}}
form input:focus-visible,form select:focus-visible,form textarea:focus-visible{{
  outline:2px solid var(--accent);outline-offset:1px}}
.actions{{display:flex;gap:10px;margin-top:2px}}
</style></head><body>
<header><h1>{brand_icon} {brand}</h1><p class="sub">Memory wiki của agent này — human CRUD-able, agent nạp cùng nguồn.</p>{topbar}</header>
<div class="layout"><aside>{sidebar}</aside><main><div class="doc">{content}</div></main></div>
<script>
const q = document.getElementById('q');
q.addEventListener('input', () => {{
  const v = q.value.trim().toLowerCase();
  document.querySelectorAll('aside li').forEach(li => {{
    const a = li.querySelector('a');
    li.style.display = !v || a.dataset.title.includes(v) ? '' : 'none';
  }});
}});
</script></body></html>"""


def resolve_safe_path(wiki_root, rel):
    """Chặn path traversal — trả Path tuyệt đối nếu rel nằm TRONG wiki_root, else None. Test sống
    (không chỉ đọc code): xem wiki/log.md entry wiki-browser-route, đã verify qua http.client thô
    (không qua normalize của client) trả đúng 403 khi có '../'."""
    wiki_root = Path(wiki_root).resolve()
    target = (wiki_root / rel).resolve()
    try:
        target.relative_to(wiki_root)
    except ValueError:
        return None
    return target


# ---- CRUD (write path) — chỉ dùng cho wiki riêng từng agent (mount qua chatdemo.py), KHÔNG mount
# cho llmwiki/wiki_browser.py cấp dự án (giữ nguyên "chỉ 1 VIEW đọc" như thiết kế ban đầu của nó).


def split_csv(raw):
    """'a, b ,  ,c' -> ['a', 'b', 'c'] — dùng cho input tags/aliases dạng text tự do trong form."""
    return [s.strip() for s in (raw or "").split(",") if s.strip()]


def slugify(title):
    """Tiêu đề (kể cả tiếng Việt có dấu) -> slug kebab-case ascii dùng làm tên file. 'đ'/'Đ' không
    tự decompose qua NFKD (không phải dấu kết hợp) nên map tay trước khi normalize."""
    s = (title or "").translate(_VI_TRANSLIT)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "trang-moi"


def load_page_values(wiki_root, rel):
    """Đọc 1 trang thành dict field cho form sửa (type/title/tags/aliases/body) — trả None nếu file
    không tồn tại. `body` giữ NGUYÊN văn bản sau frontmatter (kể cả section ## Origin cũ) để form
    sửa không mất nội dung người dùng đã viết."""
    target = Path(wiki_root) / rel
    if not target.is_file():
        return None
    meta, body = parse_frontmatter(target.read_text(encoding="utf-8"))
    return {
        "type": meta.get("type") or "source",
        "title": meta.get("title") or Path(rel).stem,
        "tags": ", ".join(str(t) for t in (meta.get("tags") or [])),
        "aliases": ", ".join(str(a) for a in (meta.get("aliases") or [])),
        "body": body.strip(),
    }


def compose_page(meta, body, default_origin="Tạo/sửa qua /wiki UI."):
    """Ghép frontmatter (dict) + body thành nội dung file .md hoàn chỉnh — tự thêm section
    ## Origin nếu body CHƯA có (R2 require_section bắt buộc), giữ nguyên nếu người dùng đã tự viết
    Origin riêng khi sửa trang có sẵn."""
    body = (body or "").strip()
    if not _ORIGIN_SECTION_RE.search(body):
        body += f"\n\n## Origin\n- {default_origin}\n"
    ordered = {}
    for key in ("type", "title", "aliases", "tags", "timestamp"):
        val = meta.get(key)
        if val not in (None, "", []):
            ordered[key] = val
    fm = yaml.safe_dump(ordered, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{fm}\n---\n\n{body}\n"


def save_page(wiki_root, rel, content):
    """Ghi `content` vào wiki_root/rel rồi chạy NGAY llmwiki-validate.py path <file> — CÙNG lõi gác
    cổng mà Claude Code hook dùng (harness/poc-vendor-neutral), không phải 1 luật viết tay riêng dễ
    lệch. Vi phạm (thiếu frontmatter/## Origin/sai subfolder...) -> ROLLBACK ngay (khôi phục nội
    dung cũ nếu là sửa, xoá file nếu là tạo mới) — không để lại file không hợp lệ trên đĩa. Trả
    (ok: bool, error: str|None)."""
    target = resolve_safe_path(wiki_root, rel)
    if target is None:
        return False, "Đường dẫn không hợp lệ."
    existed = target.is_file()
    original = target.read_text(encoding="utf-8") if existed else None
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(_VALIDATOR_PATH), "path", str(target)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        if existed:
            target.write_text(original, encoding="utf-8")
        else:
            target.unlink(missing_ok=True)
        return False, proc.stderr.strip() or f"Harness gate chặn (exit {proc.returncode})."
    return True, None


def delete_page(wiki_root, rel):
    """Xoá 1 trang — trả True nếu xoá thành công, False nếu path không hợp lệ/không tồn tại."""
    target = resolve_safe_path(wiki_root, rel)
    if target is None or not target.is_file():
        return False
    target.unlink()
    return True


def _form_content(mode, prefix, rel, values, error):
    values = values or {}
    type_opts = "".join(
        f'<option value="{t}"{" selected" if t == (values.get("type") or "source") else ""}>'
        f"{html.escape(TYPE_LABELS.get(t, t))}</option>"
        for t in TYPE_ORDER
    )
    err_html = f'<div class="err">{html.escape(error)}</div>' if error else ""
    if mode == "edit":
        action, heading, cancel_href = f"{prefix}/edit/{rel}", "Sửa trang", f"{prefix}/{rel}"
    else:
        action, heading, cancel_href = f"{prefix}/new", "Trang mới", prefix
    return (
        f"<h1>{heading}</h1>{err_html}"
        f'<form method="post" action="{action}">'
        f'<label>Loại<select name="type">{type_opts}</select></label>'
        f'<label>Tiêu đề<input type="text" name="title" value="{html.escape(values.get("title", ""))}" required></label>'
        f'<label>Tags (phân cách bởi dấu phẩy)<input type="text" name="tags" value="{html.escape(values.get("tags", ""))}"></label>'
        f'<label>Aliases (phân cách bởi dấu phẩy, tuỳ chọn — dùng để agent khớp câu hỏi tự nhiên)'
        f'<input type="text" name="aliases" value="{html.escape(values.get("aliases", ""))}"></label>'
        f'<label>Nội dung (Markdown)<textarea name="body" rows="16" required>{html.escape(values.get("body", ""))}</textarea></label>'
        f'<div class="actions"><button type="submit" class="btn">Lưu</button>'
        f'<a class="btn-ghost" href="{cancel_href}">Huỷ</a></div>'
        f"</form>"
    )


def render_form_page(mode, wiki_root, brand, prefix="/wiki", accent_hex="0a84ff", brand_icon="📚",
                      shell=None, rel=None, error=None, values=None, **shell_vars):
    """mode: 'new' hoặc 'edit'. `shell`/`shell_vars`: xem render_index_page — CRUD form chỉ có ý
    nghĩa khi dùng với CHAT_THEMED_SHELL (có CSS cho form/button), không mount cho wiki dự án."""
    pages, _ = build_index(wiki_root)
    tpl = shell or PAGE_SHELL
    fmt = dict(
        title="Sửa trang" if mode == "edit" else "Trang mới", brand=brand, accent_hex=accent_hex,
        prefix=prefix, brand_icon=brand_icon,
        sidebar=sidebar_html(pages, rel, prefix),
        content=_form_content(mode, prefix, rel, values, error),
    )
    fmt.update(shell_vars)
    return tpl.format(**fmt)
