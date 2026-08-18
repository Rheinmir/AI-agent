"""Data Collector — tập cheatsheet DevOps thu thập sẵn, tra theo chủ đề (khác dữ liệu thời gian
thực — agent này CHƯA connect tới cluster/Grafana/pipeline nào, xem agent.py). Bắt nguồn từ
llmwiki/raw/devops-agent.md: "cần tổng hợp các thể loại cheatsheet phục vụ cho devops, k8s, sức
khoẻ container, tất cả các pattern triển khai ứng dụng dev uat stage product". Nguồn sự thật là các
trang `.md` dưới `demo_agents/devops_agent/wiki/sources/` (đọc qua `llmwiki.wiki_lib`, KHÔNG cache)
— 1 sub-type của layer Memory riêng của agent này, tách vật lý khỏi wiki cấp dự án
(`llmwiki/wiki/`), xem `wiki/log.md` entry "wiki-per-agent-memory".

Danh sách CHỦ Ý nhỏ và tường minh theo chủ đề — không phải toàn bộ kiến thức DevOps (agent vẫn có
thể trả lời câu hỏi ngoài danh sách này bằng kiến thức chung của model, xem INSTRUCTIONS trong
agent.py). Chủ đề ngoài danh sách trả None, KHÔNG bịa cheatsheet thay thế — cùng kỷ luật NO_DATA đã
áp dụng cho demo_agents/weather_agent/data_collector.py.
"""
import re
from pathlib import Path

from llmwiki import wiki_lib

_WIKI_ROOT = Path(__file__).parent / "wiki"
_HEADING_RE = re.compile(r"^#\s+.+\n+")
_ORIGIN_RE = re.compile(r"\n##\s+Origin\b.*", re.DOTALL)


def _normalize(topic: str) -> str:
    return " ".join(topic.strip().lower().split())


def _strip_body(body_text: str) -> str:
    text = _HEADING_RE.sub("", body_text, count=1)
    text = _ORIGIN_RE.sub("", text)
    return text.strip()


def _load_topics():
    """Trả (cheatsheets, main_slugs): cheatsheets map MỌI khoá đã normalize (slug chính + alias)
    tới nội dung; main_slugs là slug chính (tên file, không gồm alias) — dùng cho available_topics()."""
    cheatsheets = {}
    main_slugs = []
    for path, rel in wiki_lib.iter_md_files(_WIKI_ROOT):
        meta, body = wiki_lib.parse_frontmatter(path.read_text(encoding="utf-8"))
        note = _strip_body(body)
        main_slugs.append(rel.stem)
        keys = {rel.stem, *(str(a) for a in meta.get("aliases") or [])}
        for key in keys:
            cheatsheets[_normalize(key)] = note
    return cheatsheets, main_slugs


def available_topics():
    """Trả danh sách chủ đề CHÍNH (không gồm alias) — dùng để agent tự khai báo phạm vi cheatsheet
    thật có, không đoán/liệt kê những gì chưa thu thập."""
    _, main_slugs = _load_topics()
    return sorted(main_slugs)


def lookup_cheatsheet(topic: str):
    """Trả nội dung cheatsheet đã thu thập sẵn cho MỘT chủ đề, hoặc None nếu chủ đề không có trong
    tập dữ liệu — KHÔNG bịa nội dung cho chủ đề ngoài danh sách (xem available_topics())."""
    cheatsheets, _ = _load_topics()
    return cheatsheets.get(_normalize(topic))
