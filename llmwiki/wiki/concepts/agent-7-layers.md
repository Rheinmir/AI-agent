---
type: concept
title: 7 layer của một agent usable
tags: [agent, architecture, latency, harness, memory, tools]
timestamp: 2026-07-29
---

# 7 layer của một agent usable

Khung mở rộng của [[agent]] (vốn chỉ nêu 3 thành phần nền tảng: model, tools, instructions) — góc nhìn hạ
tầng/vận hành, chia một agent chạy thật thành **7 layer** phải cân bằng cùng lúc trong một ngân sách
**latency end-to-end** duy nhất. Thiếu bất kỳ layer nào, agent vẫn "chạy" nhưng theo một cách hỏng cụ thể,
không phải hỏng chung chung.

## Cấu trúc luồng — không phải 7 mục rời rạc

5 layer chảy theo vòng: **Data Collector → Memory → Context → Model Hosting → Tools**. **Harness** bao
quanh vòng này (không phải bước thứ 6 trong hàng) và lặp lại nó tới khi đủ bước. **Evaluation** đứng tách
hẳn ra ngoài, chỉ quan sát, không chặn latency user thật.

## Model Hosting

Layer lõi — chạy được model. Layer DUY NHẤT trong 7 layer cần GPU; 6 layer còn lại chạy CPU nhưng vẫn
cộng dồn vào latency tổng. Nội dung sâu (KV cache, ngân sách VRAM, checklist công thức, so sánh 13
vendor) → xem [[model-hosting]].

**Nếu thiếu:** không còn gì để chạy — 6 layer còn lại vô nghĩa vì không có gì để chạy cả (case đặc biệt,
coi là chặn toàn hệ thống, khác 6 layer kia chỉ làm hỏng CỤC BỘ).

## Tools

**Định nghĩa:** thực thi các "hành động" agent có thể gọi — search web, chạy code, gọi API nội bộ,
đọc/ghi file/database.

- **Bọc như thế nào:** Model chỉ SINH RA text mô tả "muốn gọi tool X với tham số Y". Tools layer là code
  THẬT nằm ngoài model, nhận yêu cầu đó, thực thi thật, trả kết quả về cho vòng lặp tiếp theo (do Harness
  điều phối).
- **Tại sao quan trọng:** ranh giới giữa "chatbot nói chuyện" và "agent làm việc thật". Model mạnh cỡ nào
  cũng chỉ dừng ở gợi ý nếu không có tay chân để thực thi.
- **Nếu bỏ layer này:** nhờ agent "gửi email nhắc nhóm dự án X deadline mai" → nó chỉ trả lời "Đây là nội
  dung email bạn có thể copy..." rồi DỪNG LẠI — không gửi được, dù nó "biết" phải làm gì.
- **Chi phí hạ tầng:** mỗi tool = 1 service/endpoint riêng (có thể cần sandbox chạy code cách ly, proxy
  gọi API ngoài). Latency tool call cộng TRỰC TIẾP vào tổng thời gian phản hồi — tool gọi API bên thứ 3
  chậm là nguyên nhân phổ biến nhất khiến agent "nhanh trên giấy, chậm khi chạy thật".

## Memory

**Định nghĩa:** lưu trạng thái hội thoại ngắn hạn (trong session) và dài hạn (giữa các session) — lịch sử
chat, fact đã học, preference user.

- **Bọc như thế nào:** đọc/ghi mỗi lượt — đứng giữa Data Collector (nạp dữ liệu ngoài) và Context layer
  (lắp vào prompt).
- **Tại sao quan trọng:** không có memory, agent "mất trí nhớ" hoàn toàn mỗi lần gọi mới — không nhớ ngữ
  cảnh hội thoại trước, không cá nhân hoá được.
- **Nếu bỏ layer này:** tin nhắn 1: "Tôi tên Minh, làm kế toán." Tin nhắn 3: "Vậy phòng tôi xử lý được yêu
  cầu này không?" → Agent hỏi lại: "Bạn làm phòng ban nào ạ?" — quên sạch 2 câu vừa nói.
- **Chi phí hạ tầng:** 1 session store (Redis, <5ms), 1 lần gọi vector DB retrieval (20-100ms tuỳ index
  size) — cộng trực tiếp vào latency mỗi turn.

## Context/Instruction

**Định nghĩa:** lắp ráp prompt thật gửi vào model mỗi lượt — system instruction, kết quả Memory, tool
schema, lịch sử rút gọn, đúng thứ tự, đúng token budget.

- **Bọc như thế nào:** lớp "biên dịch" ngay trước khi gọi model — nhận input từ Memory + Tools + Harness,
  xuất ra 1 prompt/messages array cuối cùng.
- **Tại sao quan trọng:** prompt lắp sai thứ tự/thiếu context = model trả lời sai dù model mạnh cỡ nào —
  không phải lỗi model, mà lỗi assembly.
- **Nếu bỏ layer này (hoặc lắp sai):** agent có đủ tool, đủ trí nhớ, đủ dữ liệu — nhưng lắp tài liệu 50
  trang TRƯỚC câu hỏi thật của bạn, khiến model "quên" mất câu hỏi ở dưới cùng và trả lời lạc đề, dù mọi
  input đều đúng và đầy đủ.
- **Chi phí hạ tầng:** thường KHÔNG cần service riêng — chạy như code trong Harness (vài ms CPU). Không
  tốn container riêng, nhưng tốn token budget (ảnh hưởng chi phí + latency gián tiếp qua độ dài prompt).

## Data Collector

**Định nghĩa:** thu thập, làm sạch, index dữ liệu bên ngoài (tài liệu nội bộ, web, API, database công ty)
để nạp vào kho tri thức cho agent tra cứu (RAG).

- **Bọc như thế nào:** chạy độc lập, theo lịch (cron/batch) hoặc streaming — KHÔNG nằm trong đường
  request-response trực tiếp; kết quả đổ vào vector DB mà Memory layer đọc.
- **Tại sao quan trọng:** agent không tự "biết" dữ liệu riêng của tổ chức — thiếu layer này, nó chỉ dựa
  kiến thức train sẵn, dễ trả lời sai/lỗi thời với domain-specific info.
- **Nếu bỏ layer này:** hỏi "chính sách nghỉ phép công ty mình là gì?" → Agent trả lời chung chung kiểu
  Google, hoặc BỊA ra một chính sách nghe hợp lý nhưng SAI hoàn toàn, vì chưa từng "đọc" tài liệu nội bộ
  của bạn.
- **Chi phí hạ tầng:** 1 service ETL/ingestion (worker, CPU-only), 1 vector database (Qdrant/Milvus/
  pgvector). KHÔNG nằm trong request-time trực tiếp, trừ khi làm real-time crawling.

## Harness

**Định nghĩa:** vòng lặp chính (think → act → observe → repeat) — quyết định khi nào gọi model, khi nào
gọi tool, khi nào dừng, xử lý lỗi/retry.

- **Bọc như thế nào:** layer NGOÀI CÙNG về mặt điều khiển — ôm toàn bộ Model/Tools/Memory/Context bên
  trong, chạy như 1 process điều phối, tự nó không sinh câu trả lời.
- **Tại sao quan trọng:** độc lập với model mạnh cỡ nào — harness kém thì agent vẫn "ngu" theo nghĩa
  không biết dừng đúng lúc hay chọn đúng bước.
- **Nếu bỏ layer này (hoặc yếu):** agent cần 3 bước để trả lời (tra dữ liệu → tính toán → viết báo cáo)
  nhưng không có ai điều phối vòng lặp, nên nó dừng lại sau bước 1 và trả lời luôn dữ liệu thô, hoặc lặp
  vô hạn không biết khi nào nên dừng.
- **Chi phí hạ tầng:** 1 service điều phối (CPU-only, có thể serverless/lightweight) — nhưng mỗi bước lặp
  cộng thêm 1 lần gọi model → latency NHÂN theo số vòng lặp trung bình, không phải cộng 1 lần.
- **Monitoring:** giám sát hành vi agent (mỗi tool call, LLM call, kết thúc lượt) không cần đổi
  framework — dùng lifecycle hooks có sẵn của SDK đang chạy. Xem [[agent-portability]] cho cách
  giữ agent chuyển đổi được giữa nhiều framework (openai-agents/LangChain/LangGraph/...) mà không
  phải viết lại từ đầu mỗi lần đổi.

## Evaluation

**Định nghĩa:** đo chất lượng đầu ra (đúng/sai, hữu ích, an toàn), theo dõi regression, chấm điểm tự động
hoặc người gác.

- **Bọc như thế nào:** chạy SONG SONG/SAU (out-of-band) — không nằm trong đường request-response trực
  tiếp; quan sát toàn hệ thống từ ngoài (vòng ngoài cùng, nét đứt trong sơ đồ luồng).
- **Tại sao quan trọng:** không có eval, không biết agent có đang xuống cấp (đổi version model, đổi
  prompt, tool lỗi) cho đến khi user complain.
- **Nếu bỏ layer này:** tuần trước agent trả lời đúng 95%. Tuần này ai đó đổi version model hoặc sửa
  prompt, độ chính xác rớt còn 60% — nhưng không ai biết, vì không có gì đo lường liên tục. Đến khi khách
  hàng complain hàng loạt mới phát hiện ra.
- **Chi phí hạ tầng:** 1 pipeline eval riêng (batch job hoặc LLM-as-judge — tốn thêm GPU/API call NHƯNG
  offline, không cộng vào latency request thật).

## Tóm tắt 1 dòng/layer nếu thiếu

| Layer | Nếu thiếu |
|---|---|
| Model Hosting | không còn gì để chạy (chặn toàn hệ thống) |
| Tools | chỉ nói suông, không thực thi được hành động nào |
| Memory | quên sạch ngữ cảnh sau mỗi lượt |
| Context | lắp prompt sai thứ tự nên dễ lạc đề dù input đủ |
| Data Collector | không biết gì về dữ liệu riêng của bạn, dễ bịa thông tin |
| Harness | không biết khi nào nên dừng — lặp vô hạn hoặc bỏ cuộc giữa chừng |
| Evaluation | xuống cấp âm thầm mà không ai phát hiện ra |

Đủ cả 7: agent phản hồi đúng, nhớ ngữ cảnh, thực thi được hành động, và tự giám sát chất lượng.

## Origin
- **Source:** [[290726-kv-cache-llm-hosting]]
