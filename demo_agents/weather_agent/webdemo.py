"""Micro demo web server cho weather agent.

Gọi TRỰC TIẾP logic tool thật (_get_weather_impl, tra qua Open-Meteo) — không cần
DEEPSEEK_API_KEY/OPENAI_API_KEY vì không gọi LLM, chỉ demo phần Tool trong ba yếu tố nền tảng
Model/Tools/Instructions.

Chạy: python3 -m demo_agents.weather_agent.webdemo
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from demo_agents.weather_agent.agent import NO_DATA, _get_weather_impl

HTML_PATH = Path(__file__).parent / "web" / "index.html"
PORT = 8766


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = HTML_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/api/weather":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            data = {}
        city = str(data.get("city", "")).strip()
        if not city:
            payload = {"error": "city trống"}
            status = 400
        else:
            raw = _get_weather_impl(city)
            found = not raw.startswith(f"{NO_DATA}:")
            payload = {"city": city, "raw": raw, "found": found}
            status = 200
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Weather agent demo (tool thật qua Open-Meteo, không qua LLM) — http://127.0.0.1:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
