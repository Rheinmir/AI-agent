"""Data Collector — thu thập + index một tập nhỏ ghi chú thực tế theo thành phố (múi giờ, đặc điểm
khí hậu chung theo mùa). Khác hẳn `get_weather` trong agent.py (dữ liệu THỜI GIAN THỰC qua API) —
đây là dữ liệu THU THẬP SẴN, ổn định theo thời gian. Nguồn sự thật là các trang `.md` dưới
`demo_agents/weather_agent/wiki/sources/` (đọc qua `llmwiki.wiki_lib`, KHÔNG cache — sửa file bằng
tay/git, lần gọi kế tiếp phản ánh ngay) — đây là 1 sub-type của layer Memory riêng của agent này,
tách vật lý khỏi wiki cấp dự án (`llmwiki/wiki/`), xem `wiki/log.md` entry "wiki-per-agent-memory"
và wiki/concepts/agent-7-layers.md § Data Collector.

Danh sách CHỦ Ý nhỏ và tường minh — không phải mọi thành phố trên thế giới. Thành phố ngoài danh
sách trả None, KHÔNG bịa ghi chú thay thế (cùng kỷ luật NO_DATA đã áp cho get_weather).
"""
import re
from pathlib import Path

from llmwiki import wiki_lib

_WIKI_ROOT = Path(__file__).parent / "wiki"
_HEADING_RE = re.compile(r"^#\s+.+\n+")
_ORIGIN_RE = re.compile(r"\n##\s+Origin\b.*", re.DOTALL)


def _normalize(city: str) -> str:
    return " ".join(city.strip().lower().split())


def _strip_body(body_text: str) -> str:
    text = _HEADING_RE.sub("", body_text, count=1)
    text = _ORIGIN_RE.sub("", text)
    return text.strip()


def _load_notes():
    notes = {}
    for path, rel in wiki_lib.iter_md_files(_WIKI_ROOT):
        meta, body = wiki_lib.parse_frontmatter(path.read_text(encoding="utf-8"))
        note = _strip_body(body)
        keys = {rel.stem, *(str(a) for a in meta.get("aliases") or [])}
        for key in keys:
            notes[_normalize(key)] = note
    return notes


def lookup_city_note(city: str):
    """Trả ghi chú thực tế đã thu thập sẵn cho thành phố (múi giờ, đặc điểm khí hậu chung), hoặc
    None nếu thành phố không có trong tập dữ liệu — KHÔNG bịa ghi chú cho thành phố ngoài danh sách."""
    return _load_notes().get(_normalize(city))
