---
type: concept
title: Model Hosting — KV cache, ngân sách VRAM, chọn model theo hạ tầng
tags: [model-hosting, kv-cache, vram, gpu, infra, agent-7-layers]
timestamp: 2026-07-29
---

# Model Hosting — KV cache, ngân sách VRAM, chọn model theo hạ tầng

Layer lõi của [[agent-7-layers]] — layer DUY NHẤT trong 7 layer cần GPU. Trọng tâm: VRAM còn lại sau khi
load weight model = trần cho context dài và số user đồng thời (CCU). Hết margin này, server không OOM
ngay mà âm thầm cắt context hoặc từ chối request mới.

## KV cache là gì

Vòng lặp: token mới sinh → tính Key/Value → lưu vào KV cache → token N+1 tra lại cache thay vì tính lại từ
đầu → lặp lại. Ngân sách VRAM thuê (vd 1024GB) tách thành **Trọng số mô hình** (cố định theo model) và
**KV cache còn lại** (phục vụ context dài + nhiều user đồng thời).

## Công thức KV cache/token

```
KV_bytes/token = 2 × L × H_kv × d_head × bytes_elem
```
- `L` = số layer transformer (`num_hidden_layers`)
- `H_kv` = số "đầu" lưu Key/Value (`num_key_value_heads`) — model hiện đại dùng GQA nên H_kv < số
  attention-head thật
- `d_head` = kích thước vector mỗi head (`head_dim`), thường 64-128
- `bytes_elem` = byte lưu 1 số: 2 cho fp16/bf16, 1 cho fp8
- Hệ số `2` đầu công thức = tính cả Key VÀ Value (không liên quan `bytes_elem`)

**Ví dụ thật (Qwen3-235B-A22B, từ config.json):** L=94, H_kv=4, d_head=128, bytes_elem=2 →
KV_bytes/token = 2×94×4×128×2 = 192.512 byte ≈ 188KB/token. Context native 32K: 188KB×32.768 ≈
6,16GB/request. Ngân sách 554GB còn lại → tối đa ≈ **89 request đồng thời** ở full 32K context.

## Checklist triển khai — 6 mục kèm công thức

1. **Đo VRAM thật** — công thức KV cache/token ở trên; lấy L/H_kv/d_head từ config.json model cụ thể,
   nhân theo context×CCU mục tiêu, so với "KV cache còn lại" — vượt số đó nghĩa là không thật sự chạy
   được ở tải đó.
2. **Chọn framework + số GPU**: `TP_degree = ceil(Weight_GB / VRAM_mỗi_GPU)`. Vd Qwen3-235B-A22B
   (470GB) trên H100 80GB → ceil(470/80)=6, làm tròn lên 8. vLLM/SGLang/TensorRT-LLM đều cấu hình TP qua
   số này; MoE cần thêm expert-parallel.
3. **Interconnect**: NVLink 4.0 trên H100 SXM = 900GB/s bidirectional/GPU — bắt buộc nếu TP>4. Multi-node
   cần InfiniBand tốc độ cao. `Độ_trễ_đọc_weight = Weight_GB / (TP_degree × Bandwidth_GBps_mỗi_GPU)`.
   Vd Qwen3-235B-A22B, TP=8, H100 3.35TB/s/GPU: 470/(8×3350) ≈ 17.5ms/lần đọc full weight.
4. **Xác nhận license thật**: Apache 2.0/MIT sạch (Qwen mọi bản, gpt-oss, Cohere Command A+, DeepSeek
   V4-Flash/Pro, GLM-4.6/5.2) vs có ràng buộc thật (Llama 4 Maverick: 700M MAU, cấm train model khác,
   hạn chế EU; Nemotron 3 Ultra: OpenMDW-1.1; MiniMax M3: điều khoản thương mại chưa công bố rõ).
5. **Tự benchmark**: `Token/giây ≈ (TP_degree × Bandwidth_GBps) / (Active_params_B × bytes_elem)` —
   trần lý thuyết. Vd Qwen3-235B-A22B (22B active) trên 8×H100: (8×3350)/(22×2) ≈ 609 token/s. Đo thật
   dưới 30-40% số này → có vấn đề cấu hình.
6. **Giám sát KV cache**: `Max_CCU = KV_cache_còn_lại_GB / (KV_bytes/token × context_length / 1e9)`.
   Đặt alert khi (concurrent_request × avg_context) tiệm cận số này — ranh giới OOM thật.

## Ngân sách VRAM 1024GB — weight vs KV cache còn lại (theo weight tăng dần)

| Model | Vendor | Total/Active | Weight | KV cache còn lại | Margin |
|---|---|---|---|---|---|
| gpt-oss-120b | OpenAI | 120B/~5.1B | 240GB | 784GB | rộng |
| Qwen3.5-122B-A10B | Alibaba | 122B/10B | 244GB | 780GB | rộng |
| Cohere Command A+ | Cohere | 218B/25B | 436GB | 588GB | rộng |
| MiniMax M2 | MiniMax | 230B/10B | 460GB | 564GB | rộng (bản cũ, đã có M2.1/2.5/2.7/M3) |
| **Qwen3-235B-A22B** | Alibaba | 235B/22B | 470GB | 554GB | rộng — **khuyến nghị mặc định** |
| DeepSeek V4-Flash | DeepSeek | 284B/13B | 568GB | 456GB | rộng — MIT, context 1M |
| GLM-4.6 | Zhipu/Z.ai | 357B/32B | 714GB | 310GB | chật — MIT, tiền thân GLM-5.2 |
| Qwen3.5-397B-A17B | Alibaba | 397B/17B | 794GB | 230GB | chật — flagship nếu nâng target |
| Llama 4 Maverick | Meta | 400B/17B | 800GB | 224GB | chật — license Meta Community, không Apache/MIT |
| MiniMax M3 | MiniMax | 428B/23B | 856GB | 168GB | chật nhất trong nhóm vừa; context 1M |
| Nemotron 3 Ultra | Nvidia | 550B/55B | 1.100GB | **-76GB** | vượt ngân sách — AA Index 48, cao nhất Mỹ, chỉ thiếu ~76GB |
| GLM-5.2 | Zhipu/Z.ai | 744B/40B | 1.488GB | **-464GB** | vượt hẳn — AA Index 51, cao nhất mọi open-weight |
| Kimi K3, Qwen3.8-Max, DeepSeek V4-Pro, Inkling | đa vendor | 1.6T-2.8T | — | -3.2TB đến -5.6TB | chỉ khả thi nếu quantize (FP8/INT8) hoặc thuê thêm VRAM nhiều lần |

Target gốc: 512GB weight (256B fp16), thuê thật 1024GB (2×). Ngoài lề: **Apertus 1.5** (Thụy Sĩ) chỉ có
bản 8B/70B, dư ~884GB cache nhưng sức mạnh thấp hơn hẳn — mở toàn phần cả training data, đáng cân nhắc
nếu ưu tiên minh bạch hơn sức mạnh thô.

## Khuyến nghị

**Qwen3-235B-A22B vẫn là lựa chọn an toàn mặc định**: đúng target ~256B, margin 554GB rộng rãi, Apache
2.0 sạch. Hai đối thủ đáng thử nghiệm song song:
- **DeepSeek V4-Flash** — context 1M dài nhất nhóm, active param thấp hơn (rẻ/nhanh hơn), MIT license.
  (Lưu ý: DeepSeek KHÔNG bị loại hoàn toàn khỏi ngân sách — chỉ bản V4-Pro (1.6T) mới quá lớn.)
- **GLM-4.6** — MIT, họ hàng gần GLM-5.2 (model dẫn đầu benchmark mọi open-weight hiện nay), nhưng CHƯA
  có điểm AA Index xác nhận cùng thang đo — danh tiếng "mạnh" chỉ suy luận từ việc là tiền thân GLM-5.2.

**gpt-oss-120b** vẫn là phương án hạ chi phí GPU (margin rộng nhất, throughput cao nhất). Nếu muốn
flagship mạnh nhất còn vừa ngân sách, **Qwen3.5-397B-A17B** hoặc **Llama 4 Maverick** chấp nhận margin
chật ~230GB — nhưng Llama 4 dùng Meta Community License (không Apache/MIT thuần): giới hạn 700 triệu
MAU/tháng, bắt buộc ghi "Built with Llama", cấm dùng output train model khác, loại bỏ đa phương thức cho
pháp nhân EU.

## Đánh đổi tốc độ — tại sao weight KHÔNG quyết định tok/s

Decode bị giới hạn bởi băng thông đọc weight (memory-bandwidth-bound), không phải FLOPs:
```
tok/s ≈ Bandwidth_tổng / (Active_params_B × bytes_elem)
```
Tỷ lệ active/total (độ "sparse" MoE) mới quyết định tốc độ, không phải weight tổng. Ví dụ: Cohere
Command A+ (436GB weight, active 25B) chỉ ~768 tok/s — chậm hơn MiniMax M2 (460GB weight, active 10B)
đạt ~1920 tok/s, dù weight gần bằng nhau.

Lưu ý quan trọng: số tok/s trong bảng là **single-stream** (1 user). Với nhiều user, continuous batching
giúp throughput TỔNG tăng gần tuyến tính (vẫn memory-bound) cho tới khi vượt ngưỡng batch size, hệ thống
chuyển sang compute-bound → throughput tổng KHÔNG tăng thêm nữa dù thêm user — đây mới là điểm "nghẽn"
thật.

## Benchmark (Artificial Analysis Intelligence Index, v4.1)

Chỉ 4 model có điểm xác nhận CÙNG phiên bản index — GLM-5.2: 51 · Nemotron 3 Ultra: 48 · MiniMax M3: 44 ·
DeepSeek V4-Pro: 44. GLM-5.2 dẫn đầu benchmark nhưng nằm ở tier "quá lớn" cho ngân sách 1024GB — điểm số
này KHÔNG phản ánh việc có vừa ngân sách VRAM hay không. 9 model khác trong bảng so sánh (kể cả
Qwen3-235B-A22B đang khuyến nghị) KHÔNG có điểm cùng thang đo — loại khỏi benchmark có chủ đích để tránh
so sánh lệch chuẩn, không phải vì chúng yếu.

## Đặc điểm kiến trúc & rủi ro riêng (các model đáng chú ý)

- **Qwen3-235B-A22B / Qwen3.5-397B-A17B**: MoE 128 expert, chỉ 8 active/token — "nhiều chuyên gia" là ẩn
  dụ hợp lý nhưng KHÔNG literal, routing học tự động chứ không gán nhãn lĩnh vực. Rủi ro: load-balance
  giữa expert có thể lệch với prompt bất thường/hiếm gặp.
- **gpt-oss-120b**: tỷ lệ active/total cực thấp (~4.25%) — sparse nhất nhóm margin rộng. Rủi ro: mới hơn,
  ít dữ liệu production thực chiến hơn Qwen.
- **DeepSeek V4-Flash**: biến thể "nhẹ" trong họ V4 (đi cùng V4-Pro). Rủi ro: nhiều khả năng chất lượng
  trần thấp hơn V4-Pro, chưa có benchmark riêng xác nhận khoảng cách thật.
- **Nemotron 3 Ultra**: kiến trúc hybrid Mamba-Transformer (không phải Transformer thuần) — lý do
  throughput cao so với quy mô. Rủi ro: kiến trúc còn mới, cần kiểm tra vLLM/SGLang có support đầy đủ
  Mamba layer chưa trước khi cam kết.
- **Cohere Command A+**: tỷ lệ active/total ~11.5% — "đặc" nhất (ít sparse nhất) nhóm margin rộng, có
  native citation độc quyền. Đánh đổi tốc độ lấy thiết kế đặc hơn.

## Origin
- **Source:** [[290726-kv-cache-llm-hosting]]
