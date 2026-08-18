"""Librarian agent — "gate cuối cùng của thủ thư" cho wiki riêng từng agent (weather_agent/wiki/,
devops_agent/wiki/). Đây là AGENT THẬT (Model+Tools+Instructions+reasoning qua Agents SDK), không
phải script tất định — khác hẳn `data_collector.py::lookup_city_note`/`lookup_cheatsheet` (khớp
CHÍNH XÁC theo tên/alias). Librarian đóng 2 vai:

1. **search_library** — đọc thư viện (tham số hoá qua `library: "weather"|"devops"`, map sang
   `wiki_root` tương ứng — CÙNG pattern `llmwiki/wiki_lib.py` đã dùng, không global state, 1
   process phục vụ CẢ HAI thư viện) rồi REASONING để trả lời câu hỏi diễn đạt khác cách viết file —
   nhưng PHẢI bám sát nội dung đọc được qua tool `list_topics`/`read_topic`, KHÔNG được bịa dữ kiện
   ngoài thư viện (cùng kỷ luật NO_DATA xuyên dự án, chỉ khác ở chỗ hiểu được diễn đạt tự nhiên hơn
   khớp CHÍNH XÁC).
2. **ingest_raw** — nhận raw text (chưa qua xử lý), ghi `<slug>-raw.md` (giữ nguyên văn, provenance)
   rồi tự viết bản `<slug>.md` (distill/lint) — cả 2 qua `llmwiki.wiki_lib.compose_page`/`save_page`
   đã có (validate + rollback nếu vi phạm harness gate, không viết luật ghi riêng).
   **Scope v1: CHỈ nhận input TEXT** — chưa có pipeline đọc ảnh/OCR trong dự án (model hiện dùng
   qua model_provider.py chưa xác nhận multimodal) — đây là giới hạn CHỦ Ý, không tự nhận có khả
   năng đọc ảnh (cùng kỷ luật "audit thật" đã áp cho Agent-Reach trước đây).

Được gọi qua `server.py` (Unix domain socket, giao thức tham khảo `herdrdev/herdr` — xem
wiki/log.md entry liên quan), KHÔNG gọi trực tiếp trong process của weather_agent/devops_agent
(2 thực thể tách rời theo đúng yêu cầu)."""
import datetime
from pathlib import Path

from agents import Agent, Runner, function_tool

from llmwiki import wiki_lib
from demo_agents.librarian_agent.model_provider import get_model

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LIBRARIES = {
    "weather": _REPO_ROOT / "demo_agents" / "weather_agent" / "wiki",
    "devops": _REPO_ROOT / "demo_agents" / "devops_agent" / "wiki",
}


def library_root(library: str) -> Path:
    root = LIBRARIES.get(library)
    if root is None:
        raise ValueError(f"library lạ '{library}' — chỉ hỗ trợ {sorted(LIBRARIES)}")
    return root


def _list_topics_impl(root: Path) -> str:
    lines = []
    for path, rel in wiki_lib.iter_md_files(root):
        meta, _ = wiki_lib.parse_frontmatter(path.read_text(encoding="utf-8"))
        title = meta.get("title") or rel.stem
        aliases = ", ".join(str(a) for a in (meta.get("aliases") or []))
        lines.append(f"- {rel} | title={title} | aliases=[{aliases}]")
    return "\n".join(lines) if lines else "(thư viện rỗng — chưa có topic nào đã lint)"


def _read_topic_impl(root: Path, rel: str) -> str:
    target = wiki_lib.resolve_safe_path(root, rel)
    if target is None or not target.is_file():
        return f"NO_DATA: không tìm thấy trang '{rel}' trong thư viện."
    _, body = wiki_lib.parse_frontmatter(target.read_text(encoding="utf-8"))
    return body.strip()


SEARCH_INSTRUCTIONS = (
    "Bạn là librarian — thủ thư quản lý 1 thư viện kiến thức đã lint cho 1 agent khác (weather "
    "hoặc devops). Nhiệm vụ DUY NHẤT: trả lời câu hỏi tra cứu DỰA HOÀN TOÀN vào nội dung đọc được "
    "qua tool list_topics/read_topic — KHÔNG được bịa thêm dữ kiện không có trong thư viện, kể cả "
    "khi bạn 'biết' câu trả lời từ kiến thức chung. Luôn gọi list_topics trước để biết thư viện có "
    "gì, rồi read_topic cho (các) trang có vẻ liên quan trước khi trả lời.\n\n"
    "QUAN TRỌNG — phân biệt 2 việc KHÁC NHAU, đừng lẫn: (1) CHỦ ĐỀ câu hỏi có được thư viện đề cập "
    "hay không, và (2) nội dung có sẵn ĐÚNG NGUYÊN HÌNH THỨC người hỏi yêu cầu hay chưa (vd người "
    "hỏi muốn 'liệt kê N fact', 'tóm tắt', 'so sánh X với Y' — thư viện hiếm khi có sẵn đúng hình "
    "thức đó, mà chỉ có nội dung thô liên quan). Nếu (1) ĐÚNG — trang đọc được có nội dung THẬT nói "
    "về đúng chủ đề hỏi, dù không viết sẵn theo hình thức yêu cầu — bạn ĐƯỢC PHÉP tự tổng hợp/đếm/"
    "định dạng lại nội dung đó cho đúng hình thức người hỏi muốn, miễn KHÔNG thêm sự thật/số liệu "
    "nào ngoài những gì đã đọc được từ read_topic (chỉ sắp xếp lại cách trình bày, không sáng tác "
    "nội dung mới). CHỈ trả 'NO_DATA' khi (1) SAI — không trang nào trong thư viện thật sự nói về "
    "chủ đề đó — không phải vì thiếu đúng hình thức trình bày.\n\n"
    "Nếu không trang nào thật sự khớp CHỦ ĐỀ câu hỏi (không phải chỉ thiếu hình thức), trả lời đúng "
    "nguyên văn 'NO_DATA' (không thêm giải thích khác) — người gọi tự biết đây là tín hiệu 'không có "
    "trong thư viện', không phải lỗi."
)

INGEST_INSTRUCTIONS = (
    "Bạn là librarian — nhận 1 đoạn RAW TEXT (có thể lộn xộn, không có cấu trúc, dữ liệu ngẫu "
    "nhiên) và 1 tiêu đề gợi ý. Nhiệm vụ: viết lại thành nội dung Markdown SẠCH, súc tích, đúng cấu "
    "trúc heading/bullet hợp lý — GIỮ NGUYÊN mọi sự thật/số liệu có trong raw text, KHÔNG thêm "
    "thông tin không có trong đó, KHÔNG bịa. Xoá phần lặp/rác/nhiễu không mang thông tin. CHỈ trả "
    "về nội dung Markdown thuần (không kèm frontmatter YAML, không kèm lời giải thích/mở đầu/kết "
    "luận thêm ngoài nội dung đã distill)."
)


def build_search_agent(library: str) -> Agent:
    """Dựng Agent MỚI mỗi lần gọi, tool đóng (closure) quanh `root` của library — tránh phải truyền
    library qua tham số tool (model không tự quyết định được library, đó là quyết định của CALLER
    trước khi vào model, xem server.py::dispatch)."""
    root = library_root(library)

    @function_tool
    def list_topics() -> str:
        """Liệt kê MỌI topic đã lint trong thư viện này (rel path + title + alias) — gọi tool này
        ĐẦU TIÊN để biết thư viện có gì, trước khi đọc chi tiết 1 topic cụ thể."""
        return _list_topics_impl(root)

    @function_tool
    def read_topic(rel: str) -> str:
        """Đọc TOÀN VĂN 1 topic cụ thể theo rel path lấy được từ list_topics (vd 'sources/hanoi.md').
        Trả 'NO_DATA: ...' nếu rel không tồn tại — KHÔNG bịa nội dung thay thế."""
        return _read_topic_impl(root, rel)

    return Agent(name="Librarian (search)", instructions=SEARCH_INSTRUCTIONS,
                 tools=[list_topics, read_topic], model=get_model())


def build_ingest_agent() -> Agent:
    return Agent(name="Librarian (distill)", instructions=INGEST_INSTRUCTIONS, model=get_model())


async def search(library: str, query: str) -> dict:
    """Trả {"status": "done", "answer": str}. `library` phải hợp lệ (ValueError nếu không — caller
    ở server.py biến thành lỗi JSON-RPC)."""
    agent = build_search_agent(library)
    result = await Runner.run(agent, query)
    return {"status": "done", "answer": result.final_output.strip()}


async def _distill(raw_text: str, title: str) -> str:
    agent = build_ingest_agent()
    prompt = f"Tiêu đề gợi ý: {title}\n\nRaw text cần distill:\n{raw_text}"
    result = await Runner.run(agent, prompt)
    return result.final_output.strip()


async def ingest_raw(library: str, title: str, raw_text: str) -> dict:
    """Ghi cặp <slug>-raw.md (nguyên văn) + <slug>.md (distill) vào wiki/sources/<slug>/ của thư
    viện — validate qua llmwiki-validate.py (wiki_lib.save_page), ROLLBACK nếu vi phạm. Trả
    {"status": "done", "rel", "raw_rel"} hoặc {"status": "error", "error"}."""
    root = library_root(library)
    slug = wiki_lib.slugify(title)
    topic_dir = f"sources/{slug}"
    raw_rel = f"{topic_dir}/{slug}-raw.md"
    linted_rel = f"{topic_dir}/{slug}.md"
    today = datetime.date.today().isoformat()

    raw_meta = {"type": "source", "title": f"{title} (raw)", "timestamp": today}
    raw_content = wiki_lib.compose_page(
        raw_meta, raw_text,
        "Raw ingest qua librarian agent (ingest_raw) — KHÔNG chỉnh sửa tay, xem bản đã lint.",
    )
    ok, err = wiki_lib.save_page(root, raw_rel, raw_content)
    if not ok:
        return {"status": "error", "error": f"ghi raw thất bại: {err}"}

    distilled = await _distill(raw_text, title)
    linted_meta = {"type": "source", "title": title, "timestamp": today}
    linted_content = wiki_lib.compose_page(
        linted_meta, distilled, f"Distill tự động (librarian agent) từ `{slug}-raw.md`.",
    )
    ok2, err2 = wiki_lib.save_page(root, linted_rel, linted_content)
    if not ok2:
        return {"status": "error", "error": f"ghi bản lint thất bại: {err2}", "raw_rel": raw_rel}
    return {"status": "done", "rel": linted_rel, "raw_rel": raw_rel}
