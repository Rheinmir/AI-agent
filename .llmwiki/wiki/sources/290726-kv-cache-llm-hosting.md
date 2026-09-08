---
type: source
title: Kiến trúc Agent — 7 layer & Model Hosting (KV cache, VRAM, chọn model)
tags: [agent, model-hosting, kv-cache, vram, infra, latency]
timestamp: 2026-07-29
resource: raw/290726-kv-cache-llm-hosting.html
---

# Kiến trúc Agent — 7 layer & Model Hosting

Ghi chú kỹ thuật nội bộ (29/07/2026), dựa trên phân tích hạ tầng + kiến trúc agent — không phải dữ liệu
research cộng đồng. Luận điểm chính: chạy được model (Model Hosting) chỉ là 1/7 việc cần làm để có một
agent usable; 6 layer còn lại phải cân bằng trong cùng một ngân sách **latency end-to-end**, nếu không thì
"usable trên giấy" vẫn thành "chậm khi chạy thật".

## 7 layer

Model Hosting · Tools · Memory · Context/Instruction · Data Collector · Harness · Evaluation

## Luồng dữ liệu (không phải danh sách rời rạc)

Dữ liệu chảy qua **5 layer** theo một vòng: Data Collector → Memory → Context → Model Hosting → Tools.
**Harness** bao quanh toàn bộ vòng này bằng khung nét đứt và lặp lại nó tới khi đủ bước ("think → act →
observe → repeat") — nói cách khác, Harness không phải bước thứ 6 trong hàng, mà là layer điều phối đứng
NGOÀI, ôm lấy 5 layer kia. **Evaluation** đứng tách hẳn ra ngoài luồng, nối bằng dây nét đứt — nó chỉ quan
sát/chấm điểm chứ không nằm trong đường request-response, không chặn latency user thật.

→ Xem chi tiết từng layer (bọc thế nào, tại sao quan trọng, ví dụ nếu bỏ, chi phí hạ tầng) ở
[[agent-7-layers]]. Layer Model Hosting (công thức KV cache, ngân sách VRAM, checklist 6 mục, so sánh
13 vendor) tách riêng ở [[model-hosting]] vì nội dung sâu hơn hẳn 6 layer còn lại.

## Ngân sách latency — thứ thật sự quyết định "usable"

```
Latency_tổng ≈ Context_assembly(~ms) + Memory_retrieval(20-100ms)
              + [Model_TTFT + N_token×decode_time] × N_vòng_lặp(Harness)
              + Tool_call_time × N_lần_gọi_tool
```

So với ngưỡng "chấp nhận được" (vd <3s cho chat tương tác, <10-15s cho tác vụ agentic nhiều bước).
Model_TTFT/decode_time chỉ là MỘT số hạng — Harness nhân số vòng lặp và Tools cộng latency gọi ngoài
thường lớn hơn phần model nhiều lần. Đây là lý do tối ưu riêng Model Hosting không đủ để có agent nhanh.

## Origin
- **Source:** `raw/290726-kv-cache-llm-hosting.html`
