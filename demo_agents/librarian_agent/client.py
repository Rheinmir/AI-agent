"""Client helper cho weather_agent/devops_agent gọi SANG librarian — 2 thực thể tách rời (process
riêng), giao tiếp qua Unix domain socket newline-delimited JSON (xem server.py cho giải thích giao
thức tham khảo herdrdev/herdr). Đồng bộ (blocking `socket` thuần) — khớp convention @function_tool
sync đã dùng cho get_weather/get_city_note/get_cheatsheet trong dự án, không cần async."""
import json
import socket
from pathlib import Path

from demo_agents.librarian_agent.server import DEFAULT_SOCK_PATH


class LibrarianUnavailable(Exception):
    """Librarian không chạy/không kết nối được/trả lỗi — caller (tool trong agent.py) PHẢI bắt
    exception này và trả NO_DATA rõ ràng, KHÔNG để lộ traceback thô hay làm crash cả agent gọi
    (cùng kỷ luật graceful-degrade đã dùng cho MCP drop_failed_servers)."""


def _call(method, params, sock_path=DEFAULT_SOCK_PATH, timeout=30):
    sock_path = Path(sock_path)
    if not sock_path.exists():
        raise LibrarianUnavailable(
            f"librarian chưa chạy (không thấy socket {sock_path}) — cần "
            "`python3 -m demo_agents.librarian_agent.server` chạy nền trước."
        )
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect(str(sock_path))
            req = {"id": "1", "method": method, "params": params}
            sock.sendall((json.dumps(req, ensure_ascii=False) + "\n").encode("utf-8"))
            buf = b""
            while not buf.endswith(b"\n"):
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buf += chunk
        except OSError as e:
            raise LibrarianUnavailable(f"không kết nối/gọi được librarian: {e}") from e
    try:
        resp = json.loads(buf.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise LibrarianUnavailable(f"phản hồi librarian không hợp lệ: {e}") from e
    if "error" in resp:
        raise LibrarianUnavailable(resp["error"].get("message", "lỗi không rõ từ librarian"))
    return resp.get("result", {})


def ask_search(library, query, sock_path=DEFAULT_SOCK_PATH, timeout=60):
    """Trả dict {"status","answer"} — raise LibrarianUnavailable nếu librarian không khả dụng."""
    return _call("library.search", {"library": library, "query": query}, sock_path, timeout)


def ask_ingest(library, title, raw_text, sock_path=DEFAULT_SOCK_PATH, timeout=120):
    """Trả dict {"status","rel","raw_rel"} — raise LibrarianUnavailable nếu librarian không khả
    dụng (timeout dài hơn search vì ingest gọi model 2 lần: ghi raw rồi distill)."""
    return _call(
        "library.ingest", {"library": library, "title": title, "raw_text": raw_text},
        sock_path, timeout,
    )
