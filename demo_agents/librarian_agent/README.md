# Librarian agent

Agent thật (Model+Tools+Instructions+reasoning, Agents SDK) đứng giữa human/raw data và
`weather_agent`/`devops_agent`. 2 vai:

- **search** — trả lời câu hỏi tra cứu bằng cách đọc thư viện wiki của agent được hỏi
  (`weather_agent/wiki/` hoặc `devops_agent/wiki/`) và reasoning trên nội dung đọc được — KHÔNG
  bịa dữ kiện ngoài thư viện.
- **ingest** — nhận raw text lộn xộn, ghi `<slug>-raw.md` (nguyên văn) + tự viết `<slug>.md`
  (bản đã lint/distill) vào `wiki/sources/<slug>/`, qua đúng harness gate
  (`llmwiki-validate.py`).

Chạy như 1 **process riêng**, expose Unix domain socket (`librarian.sock`) — giao thức
newline-delimited JSON tham khảo `herdrdev/herdr` (xem `server.py` docstring). `weather_agent`/
`devops_agent` gọi qua `client.py` (tool `ask_librarian`), KHÔNG import agent.py trực tiếp.

## Chạy

```bash
cp demo_agents/librarian_agent/.env.example demo_agents/librarian_agent/.env
# điền OPENAI_API_KEY hoặc DEEPSEEK_API_KEY
python3 -m demo_agents.librarian_agent.server
```

Cần chạy TRƯỚC khi `weather_agent`/`devops_agent` gọi tool `ask_librarian` — nếu socket chưa có,
tool trả `NO_DATA` kèm lý do rõ ràng, không crash agent gọi.
