"""DevOps agent — hỏi đáp kiến thức DevOps (Model + Tools + Instructions + input guardrail), xây từ
llmwiki/raw/devops-agent.md. Ban đầu CHỦ Ý scope xuống "hỏi đáp thuần, chưa connect tới đâu" theo
yêu cầu — sau đó người dùng yêu cầu thêm khả năng đọc nội dung internet THẬT qua MCP (xem
build_agent_with_mcp() bên dưới + mcp_tools/README.md). Vẫn CHƯA làm: Grafana agent thật, k8s API
thật, MCP pipeline trigger, multi-agent squad — đó là việc SAU, khi được yêu cầu.

Khác weather_agent (tool gọi API thật cho dữ liệu bắt buộc chính xác), agent này KHÔNG có tool nội
bộ nào gọi ra ngoài, và KHÔNG tự đọc trực tiếp wiki/cheatsheet cục bộ — MỌI truy vấn vào
demo_agents/devops_agent/wiki/ đều phải qua `ask_librarian` (gọi sang process librarian_agent riêng,
xem dưới). Đây là quyết định CHỦ Ý: trước đây có 1 tool `get_cheatsheet` tra file cục bộ khớp CHÍNH
XÁC theo tên/alias (data_collector.py) chạy TRƯỚC librarian (kim tự tháp rẻ trước đắt sau) — user
yêu cầu bỏ layer đó, để librarian là GATE DUY NHẤT vào wiki (không có đường tắt bỏ qua reasoning của
librarian). Với câu hỏi DevOps hợp lệ ngoài phạm vi wiki đã thu thập, agent được phép dùng kiến thức
chung của model để trả lời (khác kỷ luật NO_DATA nghiêm ngặt của weather_agent). MCP fetch tool (khi
gắn qua build_agent_with_mcp) là NGOẠI LỆ DUY NHẤT gọi ra internet thật — đọc-only 1 URL cụ thể,
không phải kết nối hệ thống nội bộ (cluster/Grafana/pipeline vẫn KHÔNG có).

ask_librarian: gọi SANG process librarian_agent (2 thực thể tách rời, giao tiếp qua Unix socket
tham khảo herdrdev/herdr — xem demo_agents/librarian_agent/README.md). Librarian là agent thật CÓ
reasoning, hiểu diễn đạt khác cách viết file trong wiki, nhưng vẫn bám sát nội dung thật, không
bịa — đây là TOOL DUY NHẤT của agent này được đọc wiki/cheatsheet."""

import dataclasses
from pathlib import Path

from agents import Agent, function_tool

from demo_agents.devops_agent.data_collector import available_topics
from demo_agents.devops_agent.guardrails import devops_scope_guardrail
from demo_agents.devops_agent.model_provider import get_model
from demo_agents.devops_agent.monitoring import DevOpsAgentHooks
from demo_agents.librarian_agent import client as librarian_client
from demo_agents.librarian_agent.client import LibrarianUnavailable
from mcp_tools.channels import github_search_impl, rss_read_impl, youtube_transcript_impl

NO_DATA = "NO_DATA"


@function_tool
def ask_librarian(query: str) -> str:
    """Tra cứu wiki/cheatsheet DevOps đã thu thập sẵn — TOOL DUY NHẤT của agent này được đọc wiki
    (không có tool nào khác tra file cục bộ trực tiếp). Gọi sang librarian agent (process RIÊNG,
    qua socket — xem demo_agents/librarian_agent/README.md), có REASONING — hiểu câu hỏi diễn đạt
    khác cách viết trong file wiki (vd 'k8s'/'canary'/hỏi khái quát), nhưng vẫn bám sát nội dung
    thật đọc được, không bịa. Gọi tool này cho MỌI câu hỏi có thể liên quan tới cheatsheet/wiki đã
    thu thập, TRƯỚC KHI coi là kiến thức chung. Trả 'NO_DATA:<lý do>' nếu librarian không khả dụng
    hoặc không tìm thấy gì liên quan trong wiki."""
    try:
        result = librarian_client.ask_search("devops", query)
    except LibrarianUnavailable as e:
        return f"{NO_DATA}:librarian không khả dụng ({e})"
    answer = (result.get("answer") or "").strip()
    return answer if answer and answer != "NO_DATA" else f"{NO_DATA}:{query}"


# 3 tool từ mcp_tools/channels.py (KHÔNG PHẢI MCP — plain subprocess/thư viện, xem docstring module
# đó) — LUÔN có trong devops_agent gốc (không cần build_agent_with_mcp) vì không cần Python 3.10+
# hay kết nối async nào, chỉ cần gh CLI/yt-dlp cài sẵn trên máy (tự trả NO_DATA nếu thiếu, không
# crash — xem mcp_tools/README.md § Full Agent-Reach capability).
@function_tool
def github_search(query: str) -> str:
    """Tìm kiếm repo GitHub công khai (vd tên tool/thư viện DevOps). Trả 'NO_DATA:<lý do>' nếu gh
    CLI chưa cài/chưa auth trên máy này, hoặc không có kết quả — KHÔNG bịa tên repo thay thế."""
    return github_search_impl(query)


@function_tool
def youtube_transcript(url: str) -> str:
    """Lấy phụ đề (transcript) của 1 video YouTube cụ thể (vd hướng dẫn Kubernetes/DevOps trên
    YouTube) — trả về text thuần. Trả 'NO_DATA:<lý do>' nếu video không có phụ đề hoặc yt-dlp chưa
    cài — KHÔNG bịa nội dung video thay thế."""
    return youtube_transcript_impl(url)


@function_tool
def rss_feed(feed_url: str) -> str:
    """Đọc các mục mới nhất của 1 RSS/Atom feed CỤ THỂ (vd feed blog Kubernetes, CNCF). Trả
    'NO_DATA:<lý do>' nếu URL không phải feed hợp lệ — KHÔNG bịa nội dung feed thay thế."""
    return rss_read_impl(feed_url)


INSTRUCTIONS = (
    "Bạn là DevOps agent — hỏi đáp kiến thức DevOps/hạ tầng/vận hành phần mềm "
    "(Kubernetes, container, CI/CD, pattern triển khai, promote môi trường dev/uat/stage/prod...).\n\n"
    "Khi câu hỏi có thể liên quan tới cheatsheet/wiki DevOps đã thu thập sẵn, LUÔN gọi tool "
    "ask_librarian trước — đây là TOOL DUY NHẤT được đọc wiki của agent này (không có cách nào khác "
    "để tra file cục bộ). Librarian có reasoning, hiểu diễn đạt khác cách viết trong file (vd "
    "'k8s'/'canary'/hỏi khái quát), nhưng vẫn chỉ bám nội dung THẬT đọc được, không bịa. Nếu tool "
    "trả 'NO_DATA:', nghĩa là chủ đề đó CHƯA có trong wiki — bạn vẫn có thể trả lời bằng kiến thức "
    "chung nếu câu hỏi thuộc phạm vi DevOps, nhưng phải nói rõ đây là kiến thức chung, không phải "
    "nội dung đã thu thập/kiểm chứng riêng cho dự án này. Nếu người dùng hỏi TẠI SAO 1 chủ đề liên "
    "quan không có trong wiki dù ask_librarian đã NO_DATA, giải thích ĐÚNG cơ chế: đây là wiki "
    "riêng của bạn (xem /wiki), librarian có reasoning nhưng vẫn chỉ bám nội dung thật đã lint sẵn "
    "trong wiki — không bịa, không phải lỗi khi trả NO_DATA.\n\n"
    "GIỚI HẠN QUAN TRỌNG — luôn nói thật, không giả vờ có khả năng chưa có: bạn CHƯA kết nối tới "
    "bất kỳ hệ thống NỘI BỘ nào (không có quyền truy cập cluster Kubernetes thật, không gọi được "
    "Grafana/Prometheus thật, không trigger được pipeline CI/CD thật, không thực thi được lệnh trên "
    "máy/server nào). Nếu người dùng yêu cầu bạn KIỂM TRA tình trạng một hệ thống thật, CHẠY một "
    "lệnh, hay TRIGGER một pipeline thật, hãy nói rõ đây là giới hạn hiện tại — bạn chỉ có thể giải "
    "thích khái niệm/đưa cheatsheet, chưa thể thực thi hành động thật.\n\n"
    "Khi người dùng hỏi bạn làm được gì / năng lực của bạn / help, hãy tự khai báo ĐÚNG năng lực "
    "thật, không phóng đại:\n"
    "- CÓ THỂ: (1) giải thích kiến thức DevOps chung (Kubernetes, container health check, pattern "
    "triển khai, CI/CD, promote môi trường); (2) tra cứu wiki/cheatsheet đã thu thập sẵn cho một số "
    f"chủ đề cụ thể ({', '.join(available_topics())}) — nguồn là wiki riêng của agent này "
    "(wiki/sources/, xem thêm ở /wiki), human CRUD-able; MỌI truy vấn wiki đều qua tool "
    "ask_librarian (librarian agent thật CÓ REASONING, hiểu diễn đạt tự nhiên khác cách viết file, "
    "cần librarian process đang chạy) — không có tool nào khác đọc file wiki trực tiếp; "
    "(3) nhớ ngữ cảnh hội thoại trong phiên hiện tại; (4) tìm repo GitHub công khai (tool "
    "github_search — cần gh CLI cài/auth trên máy chạy, tự báo NO_DATA nếu thiếu); (5) lấy phụ đề "
    "1 video YouTube cụ thể (tool youtube_transcript); (6) đọc 1 RSS/Atom feed cụ thể (tool "
    "rss_feed).\n"
    "- KHÔNG THỂ: kết nối/kiểm tra bất kỳ hệ thống NỘI BỘ thật nào (cluster, Grafana, pipeline "
    "CI/CD, server) — đây là giới hạn CHỦ Ý của phiên bản hiện tại, không phải lỗi."
)

# Addendum CHỈ áp dụng cho bản agent có gắn MCP tool (xem build_agent_with_mcp) — KHÔNG đưa vào
# INSTRUCTIONS gốc ở trên, để devops_agent (bản KHÔNG có mcp_servers) không bao giờ tự nhận vơ 1
# khả năng mà tools=[...] của chính nó không thật sự có.
_MCP_INSTRUCTIONS_ADDENDUM = (
    "\n\nBạn CÓ THÊM 2 khả năng internet THẬT, đọc-only, qua MCP:\n"
    "- 'web_search_exa' (Exa) — TÌM KIẾM thật trên internet theo mô tả tự nhiên (không cần URL sẵn) "
    "— dùng khi câu hỏi cần thông tin MỚI/CỤ THỂ không có trong cheatsheet đã thu thập sẵn (vd phiên "
    "bản mới nhất của 1 công cụ, tin tức/thay đổi gần đây). Đây là search engine THẬT, khác cheatsheet "
    "tĩnh — luôn nói rõ thông tin lấy từ tìm kiếm, không lẫn với cheatsheet đã kiểm chứng sẵn.\n"
    "- 'fetch'/'web_fetch_exa' — đọc nội dung MỘT (hoặc vài) trang web CỤ THỂ khi có URL rõ ràng, "
    "trả về nội dung dạng markdown.\n"
    "Cả 2 đều là internet CÔNG KHAI — KHÔNG PHẢI quyền truy cập hệ thống nội bộ (cluster/Grafana/"
    "pipeline vẫn hoàn toàn KHÔNG kết nối được, giữ nguyên giới hạn đã nêu ở trên)."
)

_SKILL_PATH = Path(__file__).parent / "SKILL.md"


def _load_skill_addendum() -> str:
    """CÙNG pattern weather_agent/agent.py::_load_skill_addendum — xem docstring ở đó. Fail-open
    (chuỗi rỗng) nếu SKILL.md không tồn tại/đọc lỗi."""
    try:
        text = _SKILL_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    if not text:
        return ""
    return f"\n\n## Kỹ năng đã học (procedural memory, sửa tay được — xem SKILL.md)\n{text}"


INSTRUCTIONS += _load_skill_addendum()

devops_agent = Agent(
    name="DevOps agent",
    model=get_model(),
    instructions=INSTRUCTIONS,
    tools=[ask_librarian, github_search, youtube_transcript, rss_feed],
    input_guardrails=[devops_scope_guardrail],
    hooks=DevOpsAgentHooks(),
)


def build_agent_with_mcp(mcp_servers):
    """Trả về BẢN SAO của devops_agent có gắn thêm mcp_servers (list server ĐÃ CONNECT — xem
    agents.mcp.MCPServerManager, dùng trong run.py/chatdemo.py). Dùng dataclasses.replace() thay vì
    định nghĩa lại Agent — không có 2 nơi khai báo model/tools/guardrails dễ lệch nhau theo thời
    gian. `devops_agent` gốc KHÔNG đổi (vẫn chạy được không cần MCP — test/import trực tiếp không bị
    ảnh hưởng)."""
    return dataclasses.replace(
        devops_agent,
        instructions=INSTRUCTIONS + _MCP_INSTRUCTIONS_ADDENDUM,
        mcp_servers=list(mcp_servers),
    )
