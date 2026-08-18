"""Wiki browser — route /wiki để CON NGƯỜI coi lại nội dung `llmwiki/wiki/*.md` (wiki KỸ THUẬT DỰ
ÁN — build history, concept kiến trúc chung, harness/tooling docs). File này giờ CHỈ LÀ ENTRYPOINT
mỏng — logic render dùng CHUNG với route `/wiki` của từng agent nằm ở `wiki_lib.py` (1 nguồn sự
thật, xem docstring module đó).

**Khác với wiki CỦA TỪNG AGENT** (`demo_agents/{weather,devops}_agent/wiki/`, mounted trực tiếp vào
`chatdemo.py` của agent đó dưới dạng layer Memory riêng — xem `wiki/log.md` entry
"wiki-per-agent-memory"): wiki NÀY là tài liệu kỹ thuật về CHÍNH DỰ ÁN (cách agent được xây, quyết
định kiến trúc, báo cáo phiên làm việc) — không phải kiến thức agent tự nạp lúc trả lời câu hỏi.
Đứng ĐỘC LẬP (không mount vào 1 agent cụ thể) vì đây là hạ tầng DÙNG CHUNG toàn dự án.

Chạy: python3 llmwiki/wiki_browser.py (mặc định port 8769, đổi qua biến môi trường PORT)
YÊU CẦU: pip install markdown pyyaml (xem llmwiki/requirements.txt)."""

import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from llmwiki import wiki_lib  # noqa: E402

WIKI_ROOT = Path(__file__).parent / "wiki"
PORT = int(os.environ.get("PORT", "8769"))
BRAND = "llmwiki/wiki"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _reply_html(self, body, status=200):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/wiki")
            self.end_headers()
            return
        if path in ("/wiki", "/wiki/"):
            return self._reply_html(wiki_lib.render_index_page(WIKI_ROOT, BRAND))
        if path.startswith("/wiki/"):
            rel = path[len("/wiki/"):]
            target = wiki_lib.resolve_safe_path(WIKI_ROOT, rel)
            if target is None:
                return self._reply_html("<h1>403</h1><p>Ngoài phạm vi wiki/.</p>", 403)
            status, body = wiki_lib.render_wiki_page(WIKI_ROOT, rel, BRAND)
            return self._reply_html(body, status)
        self._reply_html("<h1>404</h1>", 404)


def main():
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Wiki browser (project docs) — http://127.0.0.1:{PORT}/wiki ({WIKI_ROOT})")
    server.serve_forever()


if __name__ == "__main__":
    main()
