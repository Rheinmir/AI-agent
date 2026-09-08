---
type: draft
title: Build agent đầu tiên — Weather MVP (model + tools + instructions)
status: proposed
tags: [orca-workflow, propose, agent, mvp]
timestamp: 2026-07-27
task: T-260727-01
---

# 270726-first-agent-weather
**Type:** draft
**Status:** proposed
**Tags:** orca-workflow, propose, agent, mvp
**Proposed:** 2026-07-27
**Task:** T-260727-01

## Yêu cầu (diễn giải lại thành 1 câu)
Từ tài liệu đã ingest ("Hướng dẫn xây dựng Agent thực tế"), xây dựng agent đầu tiên của dự án — thể hiện rõ
ràng đúng 3 yếu tố nền tảng quan trọng nhất (Model, Tools, Instructions) — bằng OpenAI Agents SDK (Python),
theo sát ví dụ minh họa trong tài liệu nguồn.

## Context
Tài liệu nguồn [[huong-dan-xay-dung-agent-thuc-te]] định nghĩa [[agent]] gồm ba thành phần nền tảng:
[[model-selection|model]] (năng lực suy luận), [[tools]] (hàm/API để hành động), [[instructions]] (hướng dẫn
+ guardrail xác định hành xử). Ví dụ code đầu tiên trong tài liệu (`weather_agent`) chính là minh họa gọn nhất
của cả ba yếu tố cùng lúc, dùng [[openai-agents-sdk]] của [[openai]]. Repo hiện tại (`AI-agent`) mới chỉ có
`llmwiki/` (wiki) và `harness/` — **chưa có code ứng dụng nào** — nên đây là agent MVP đầu tiên của dự án,
thiết lập luôn cấu trúc thư mục code cho các agent sau này.

Khảo sát môi trường (fact, đã tra không hỏi):
- Python có sẵn: `3.9.6`.
- Chưa cài `openai` / `openai-agents` (pip show → not found).
- Không có `OPENAI_API_KEY` trong sandbox hiện tại.
- Không có git remote (repo local-only).
- Chưa có `requirements.txt`/`pyproject.toml` nào trong repo.

## Global constraints
Chép nguyên văn từ `harness/harness/policy.yaml`:
- R1 (no-write-raw): "Agent không bao giờ ghi vào raw/ — raw/ là inbox của con người."
- R15 (no-ai-attribution): "Commit message KHÔNG được ghi công cho AI (Co-Authored-By: Claude…, Generated
  with Claude Code, 🤖). Author/committer chỉ là danh tính người."
- R2 (origin-required) / R9 (okf-frontmatter): áp dụng cho mọi file wiki liên quan tạo/sửa trong quá trình
  này (draft này, các trang concept nếu cần bổ sung).

Ràng buộc thực tế của sandbox (đã xác nhận bằng lệnh, không phải giả định):
- Không có `OPENAI_API_KEY` → **không thể gọi LLM thật trong phiên hiện tại**. Mọi task liên quan "chạy
  live" chỉ verify được cấu trúc/logic offline; chạy thật với LLM là trách nhiệm của user, dùng key riêng của
  họ, ngoài phạm vi phiên này.
- Không được commit bất kỳ secret/API key nào vào repo (chuẩn bảo mật chung, không phải rule cụ thể của
  policy.yaml nhưng là ràng buộc bao trùm mọi task chạm tới cấu hình).

## Non-goals
- Không triển khai [[manager-pattern]] hay [[handoff-pattern]] (đa agent) — bản đầu tiên chỉ là **một agent
  duy nhất**, đúng khuyến nghị "tối đa hóa năng lực một agent trước" trong [[orchestration]].
- Không triển khai [[guardrails]] (input/output filtering, moderation) — để lại cho một propose riêng sau.
- Không tích hợp API thời tiết thật (ví dụ OpenWeatherMap) — tool `get_weather` trả dữ liệu mock cố định,
  giữ đúng tinh thần ví dụ minh họa của tài liệu nguồn, không thêm dependency ngoài không cần thiết.
- Không deploy, không CI/CD, không containerize.
- Không tự ý gọi API OpenAI thật trong phiên này (không có key) — không giả lập kết quả LLM là đã chạy
  thật.

## Approaches
**A. OpenAI Agents SDK (Python)** — bám sát 100% ví dụ minh họa trong tài liệu nguồn
(`Agent(name=, instructions=, tools=[...])`, `Runner.run(...)`, `@function_tool`). Ba thành phần nền tảng ánh
xạ 1-1 vào tham số của `Agent(...)`, ít code nhất, dễ đối chiếu ngược lại tài liệu để kiểm tra đúng-sai.
Tradeoff: cần cài thêm package `openai-agents`, và bắt buộc `OPENAI_API_KEY` để chạy vòng lặp thật (chỉ ảnh
hưởng lúc *chạy*, không ảnh hưởng lúc *viết/test offline*).

**B. Tự viết vòng lặp function-calling thủ công** (gọi thẳng OpenAI Chat Completions API, tự parse tool
calls). Không phụ thuộc SDK, kiểm soát toàn bộ luồng, nhưng phải tự viết lại phần mà Agents SDK đã có sẵn
(vòng lặp run, schema tool, xử lý handoff sau này) — nhiều code hơn, dễ lệch khỏi mẫu trong tài liệu nguồn,
khó dùng làm tài liệu tham chiếu cho các concept đã ingest.

**C. Dùng framework ngoài (ví dụ LangChain/LangGraph)** — phổ biến trong cộng đồng, nhưng không phải
framework mà tài liệu nguồn minh họa, kéo theo dependency nặng và một tập khái niệm khác (không map thẳng
vào [[agent]]/[[tools]]/[[instructions]] đã ingest) — lệch mục tiêu "xây agent đầu tiên bám sát tài liệu vừa
đọc".

**Chọn A** — vì mục tiêu rõ ràng là hiện thực hóa đúng những gì tài liệu vừa ingest dạy, với lượng code tối
thiểu và khả năng đối chiếu trực tiếp từng dòng với [[agent]]/[[model-selection]]/[[tools]]/[[instructions]].

## Plan
- [ ] **Task 1** — Scaffold thư mục `agents/weather_agent/` + `requirements.txt` (`openai-agents`) +
      `.env.example` (biến `OPENAI_API_KEY=`, để trống, không commit giá trị thật).
- [ ] **Task 2** — Implement agent trong `agents/weather_agent/agent.py`: định nghĩa `Model` (chọn
      `gpt-4o-mini` làm mặc định — tác vụ đơn giản, đúng nguyên tắc "tối ưu chi phí/độ trễ" ở
      [[model-selection]]), `Tools` (`get_weather(city: str)` — data tool, trả dữ liệu mock từ một dict cố
      định cho 3-4 thành phố), `Instructions` (áp dụng đủ 4 thực hành tốt của [[instructions]]: hành động rõ
      ràng, và **bao quát edge case** — thành phố không có trong dữ liệu mock thì trả lời rõ "không có dữ
      liệu" thay vì bịa số).
- [ ] **Task 3** — Viết unit test offline `agents/weather_agent/test_tool.py` cho riêng hàm `get_weather`
      (không gọi LLM, không cần `OPENAI_API_KEY`) — verify tool logic đúng độc lập với model.
- [ ] **Task 4** — Viết `agents/weather_agent/README.md` + script `run.py`: hướng dẫn cài đặt, cách tự thêm
      `OPENAI_API_KEY` riêng vào `.env` để chạy live, và nói rõ giới hạn "phiên propose/build này không có
      key nên không chạy live được — code đã sẵn sàng, chỉ cần key".

## Requirements (FR)
- **FR-001**: Hệ thống PHẢI định nghĩa một agent có đủ ba thành phần nền tảng — model, tools, instructions
  — theo đúng API của OpenAI Agents SDK.
- **FR-002**: PHẢI có ít nhất một tool (`get_weather`) mà logic của nó **kiểm thử được offline**, không cần
  `OPENAI_API_KEY`.
- **FR-003**: Instructions của agent PHẢI xử lý rõ ràng trường hợp thành phố không có trong dữ liệu (edge
  case), không được để model tự bịa số liệu.
- **FR-004**: PHẢI có tài liệu (README) đủ để một người khác tự chạy agent live bằng `OPENAI_API_KEY` của
  riêng họ, không cần hỏi lại.

## Success criteria (SC)
- **SC-001**: Một người đọc `agent.py` + README lần đầu (chưa đọc tài liệu nguồn) xác định được đâu là
  model, đâu là tools, đâu là instructions trong dưới 2 phút.
- **SC-002**: Người dùng có `OPENAI_API_KEY` riêng chạy `python run.py "Thời tiết ở Hà Nội thế nào?"` và
  nhận được câu trả lời tự nhiên có nhắc tới nhiệt độ/thành phố đã hỏi, không crash.
- **SC-003**: Khi hỏi thời tiết một thành phố không có trong dữ liệu mock, agent trả lời rõ ràng là không có
  dữ liệu (không bịa số) — kiểm chứng được cả khi chạy live lẫn qua review code instructions.
- **SC-004** *(bằng chứng máy, không thay SC người)*: `pytest agents/weather_agent/test_tool.py` xanh —
  chứng minh tool hoạt động đúng độc lập với việc có key hay không.

## Assumptions
- (default) Dùng OpenAI Agents SDK (Python) — theo đúng ví dụ trong tài liệu nguồn, xem ## Approaches.
- (default) Tool đầu tiên là `get_weather(city)` trả dữ liệu **mock cố định** (không gọi API thời tiết
  thật) — giữ scope nhỏ đúng tinh thần "MVP đầu tiên", tránh thêm dependency/API-key thứ hai không liên
  quan tới mục tiêu học từ tài liệu.
- (default) Model mặc định `gpt-4o-mini` — tác vụ đơn giản (tra cứu + trả lời một câu), không cần model
  mạnh nhất; người dùng có thể đổi qua biến môi trường nếu muốn.
- (default) Code nằm ở thư mục mới `agents/weather_agent/` — repo chưa có code app nào trước đó nên đây là
  quyết định cấu trúc thư mục lần đầu, rủi ro thấp (dễ đổi tên/di chuyển sau).
- (default) Không chạy live LLM thật trong phiên propose/build này vì sandbox không có `OPENAI_API_KEY` —
  đây là giới hạn môi trường đã xác nhận bằng lệnh (`pip show`, biến môi trường trống), không phải né việc.

## Agent Task Assignment
| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|------------|--------|
| Task 1 — Scaffold thư mục + manifest | Claude Code | Quyết định cấu trúc thư mục lần đầu của repo — thuộc nhóm "architectural decisions", không phù hợp dispatch CLI headless không có ngữ cảnh dự án | pending |
| Task 2 — Implement agent (model/tools/instructions) | Claude Code | Core logic bám sát 3 khái niệm vừa ingest, cần đối chiếu liên tục với wiki — giữ trong cùng phiên có ngữ cảnh đầy đủ | pending |
| Task 3 — Unit test offline cho tool | Claude Code | Test nhỏ, gắn liền Task 2, tách sang CLI khác chỉ thêm round-trip không cần thiết cho 1 file | pending |
| Task 4 — README + run script | Claude Code | Tài liệu phải phản ánh đúng quyết định thật ở Task 1–3 (model/tool/limitation) — không tách rời khỏi người viết code | pending |

**Sequence diagram:** [270726-first-agent-weather-seq.html](../../../html/270726-first-agent-weather-seq.html)

## Render brief
- **Task 1 (Scaffold):** legacy — repo chỉ có `llmwiki/`+`harness/`; add — tạo `agents/weather_agent/`,
  `requirements.txt`, `.env.example`. Prose: Trước khi có bất kỳ agent nào, repo cần một chỗ đứng cho code
  ứng dụng tách biệt khỏi wiki tri thức — bước này chỉ tạo khung, chưa có logic, để các task sau không phải
  vừa viết code vừa dựng thư mục.
- **Task 2 (Implement agent):** add — `Agent(model=, instructions=, tools=[get_weather])` trong
  `agent.py`. Prose: Đây là bước hiện thực hóa trực tiếp ba khái niệm đã ingest — model chọn theo nguyên
  tắc chi phí/độ trễ, tool là một hàm Python thuần trả dữ liệu mock, instructions viết theo 4 thực hành tốt
  và đặc biệt xử lý rõ nhánh "không có dữ liệu" để tránh ảo giác số liệu.
- **Task 3 (Unit test):** add — `test_tool.py` gọi trực tiếp `get_weather(...)`, assert dữ liệu mock đúng và
  assert nhánh "không có dữ liệu" trả về giá trị báo hiệu rõ ràng (không None âm thầm). Prose: Vì sandbox
  không có API key, phần duy nhất kiểm chứng được ngay bây giờ là logic tool — test này tách hẳn khỏi LLM
  nên chạy được vô điều kiện, làm bằng chứng máy cho SC-004.
- **Task 4 (README/run.py):** add — `run.py` nhận câu hỏi từ CLI, gọi `Runner.run(...)`; báo lỗi rõ ràng nếu
  thiếu `OPENAI_API_KEY` thay vì traceback khó hiểu. Prose: README phải nói thật giới hạn của phiên này —
  code sẵn sàng, chạy live cần key của chính người dùng — để không ai hiểu nhầm "đã chạy thử thành công"
  khi thực ra chỉ mới verify offline.

## Self-review
1. **Phủ yêu cầu** — yêu cầu gốc ("build agent đầu tiên", "3 yếu tố foundation quan trọng nhất") map đủ:
   Task 2 hiện thực cả ba yếu tố; Task 1/3/4 hỗ trợ chạy được và kiểm chứng được. Không có yêu cầu nào chưa
   có task.
2. **Quét placeholder** — đã rà toàn bộ draft, không còn nhãn giữ chỗ chưa điền hay câu mô tả lỗi chung
   chung kiểu "tương tự Task N".
3. **Nhất quán tên** — `get_weather`, `agent.py`, `run.py`, `agents/weather_agent/` dùng thống nhất xuyên
   suốt Plan / FR / SC / Render brief.

## Origin
- **Source:** [[huong-dan-xay-dung-agent-thuc-te]], [[agent]], [[model-selection]], [[tools]], [[instructions]]
- **Draft:** `wiki/sources/draft/270726-first-agent-weather.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
