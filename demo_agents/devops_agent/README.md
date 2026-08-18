# DevOps agent

Hỏi đáp kiến thức DevOps — Kubernetes, container health, pattern triển khai ứng dụng, promote môi
trường dev/uat/stage/prod, CI/CD pipeline — VÀ đọc nội dung trang web thật qua MCP (`mcp-server-fetch`,
xem `mcp_tools/README.md`). Xây từ `llmwiki/raw/devops-agent.md`, ban đầu CHỦ Ý scope xuống "hỏi đáp
thuần, chưa connect tới đâu", sau đó bổ sung khả năng đọc internet THẬT theo yêu cầu.

**YÊU CẦU Python 3.10+** (thư viện `mcp` client — mọi bản trên PyPI đều pin `>=3.10`, không có
ngoại lệ; đây là lý do project migrate từ Python 3.9, xem `mcp_tools/README.md`).

## Phạm vi hiện tại

| Layer | Trạng thái |
|---|---|
| Model | Có — multi-provider (DeepSeek/OpenAI), copy pattern từ `weather_agent/model_provider.py` |
| Tools | `ask_librarian` (TOOL DUY NHẤT đọc wiki/cheatsheet — gọi sang `librarian_agent` process riêng, không tra file cục bộ trực tiếp nữa) + `fetch` (MCP, `mcp-server-fetch` — đọc-only 1 URL cụ thể, xem `agent.py::build_agent_with_mcp`) |
| Instructions | Có — khai báo năng lực thật, nói rõ giới hạn CHƯA kết nối hệ thống NỘI BỘ (cluster/Grafana/pipeline) — khác internet công khai (CÓ, qua MCP) |
| Input guardrail | Có — `devops_scope_guardrail` (chặn câu hỏi ngoài DevOps/yêu cầu thực thi hành động trên hệ thống nội bộ; CHO PHÉP đọc URL công khai) |
| Data Collector | Có — cheatsheet cục bộ: `kubernetes`, `container-health`, `deployment-patterns`, `env-promotion`, `cicd-pipeline` (+ alias) |
| Chat UI | Có — `chatdemo.py` + `web/chat.html` (UI riêng, khoá bằng `web/design.md`, fork có delta từ `weather_agent`) |
| Agent portability | Có — `agent_spec.py` + `exporters/openai_agents_exporter.py`, `mcp_tool_names=["fetch_server"]` → `monolith-agent-deploy-converter` tự bundle MCP khi đóng gói standalone |
| Memory / Harness / Monitoring | **CHƯA làm** — thêm khi được yêu cầu, giống cách các layer này được thêm dần vào `weather_agent` |

## Cố ý CHƯA làm (theo `llmwiki/raw/devops-agent.md`, để dành cho sau)

- Kết nối tới Grafana agent thật để tra tình trạng máy/container thời gian thực (tham khảo
  `github.com/pranshuparmar/witr.git`).
- Gọi Kubernetes API thật (list pod/deployment thật, không chỉ cheatsheet lệnh).
- Trigger pipeline CI/CD thật.
- Kiến trúc multi-agent "đội" (tham khảo `github.com/bradygaster/squad.git`) — chỉ cần khi 1 agent
  đơn không đủ xử lý workflow phức tạp.

Guardrail chặn TRƯỚC mọi yêu cầu "thực thi hành động trên hệ thống NỘI BỘ" (vd "restart pod X giúp
tôi") bằng thông báo rõ ràng — khác hẳn yêu cầu ĐỌC 1 trang web công khai qua URL (CHO PHÉP, dùng
tool `fetch`).

## Setup (Python 3.10+ bắt buộc)

```bash
cd /Users/admin/orca/projects/AI-agent
python3.10 -m venv .venv   # hoặc 3.11/3.12/3.14 — bất kỳ 3.10+, KHÔNG chạy được 3.9
./.venv/bin/pip install -r demo_agents/devops_agent/requirements.txt

cp demo_agents/devops_agent/.env.example demo_agents/devops_agent/.env
# điền OPENAI_API_KEY hoặc DEEPSEEK_API_KEY vào .env

# (Optional nhưng khuyến nghị) cài MCP server để có tool fetch — không làm bước này agent vẫn
# chạy được, chỉ THIẾU khả năng đọc web (tự phát hiện, không crash) — xem mcp_tools/README.md
cd mcp_tools && python3.10 -m venv servers-venv && \
  ./servers-venv/bin/python3.10 -m pip install "mcp==1.29.0" mcp-server-fetch && cd ..
```

## Demo

```bash
./.venv/bin/python -m demo_agents.devops_agent.run "Sự khác nhau giữa liveness và readiness probe?"
./.venv/bin/python -m demo_agents.devops_agent.run "Canary deployment là gì?"
./.venv/bin/python -m demo_agents.devops_agent.run "Fetch https://example.com và tóm tắt"  # dùng tool fetch (MCP)
./.venv/bin/python -m demo_agents.devops_agent.run "Restart giúp tôi pod nginx trên cluster production"  # guardrail chặn
```

### Chat UI (khuyến nghị để test tương tác)

```bash
./.venv/bin/python -m demo_agents.devops_agent.chatdemo   # http://127.0.0.1:8768
```

Dùng UI riêng (`web/chat.html`, khoá bằng `web/design.md` — fork có delta từ `weather_agent`, xem
`web/design.md` § Delta). **Không dùng** `harness/scripts/monolith_agent_deploy_converter.py` cho
việc test cục bộ này — tool đó sinh trang chat TỐI GIẢN built-in (không sidebar/session-list) và
server chỉ có `/api/chat`, đúng mục đích của nó là ĐÓNG GÓI đem triển khai nơi khác (có bundle sẵn
`mcp_tools/`), không phải để có UI đẹp test tại chỗ.

## Test

```bash
./.venv/bin/python -m pytest demo_agents/devops_agent -v
```

Toàn bộ test hermetic — mock `Runner.run`/MCP server giả cho `build_agent_with_mcp`, không cần
`DEEPSEEK_API_KEY`/`OPENAI_API_KEY`/`mcp-server-fetch` cài sẵn, không gọi mạng. Verify SỐNG (spawn
`mcp-server-fetch` thật, gọi Runner.run thật) đã làm tay lúc build — xem `wiki/log.md`.
