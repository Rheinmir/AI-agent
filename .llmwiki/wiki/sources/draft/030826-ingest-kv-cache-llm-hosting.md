---
type: draft
title: 030826-ingest-kv-cache-llm-hosting
tags: [ingest, output-report]
timestamp: 2026-08-03
---

# 030826-ingest-kv-cache-llm-hosting
**Type:** draft
**Status:** proposed
**Tags:** ingest, output-report
**Proposed:** 2026-08-03

## What
Chưng cất `raw/290726-kv-cache-llm-hosting.html` (chưa từng được ingest, phát hiện qua khiếu nại của
người dùng khi hỏi nội dung file chỉ nhận lại bản tóm tắt 2-bullet nông thay vì bộ đầy đủ thật có trong
tài liệu) thành 1 trang source + 2 trang concept mới, cùng 2 wikilink bổ sung vào concept đã có.

## Output
- Trang source tổng hợp: luồng 5 layer (Data Collector→Memory→Context→Model Hosting→Tools) + Harness
  bao quanh + Evaluation tách riêng, công thức latency tổng end-to-end.
- Trang concept `agent-7-layers`: đầy đủ 4 khối nội dung (bọc thế nào / tại sao quan trọng / ví dụ nếu
  bỏ / chi phí hạ tầng) cho 6 layer Tools, Memory, Context, Data Collector, Harness, Evaluation — khắc
  phục đúng khiếu nại "chỉ có 2 chức năng" (bản cũ chỉ lấy 2 bullet mindmap teaser, bỏ sót 2/4 khối còn
  lại có sẵn trong từng section chi tiết của file gốc).
- Trang concept `model-hosting`: công thức KV cache/token, checklist 6 mục kèm công thức tính tay,
  bảng ngân sách VRAM 13 model, khuyến nghị (Qwen3-235B-A22B + DeepSeek V4-Flash + GLM-4.6), đặc điểm
  kiến trúc/rủi ro riêng từng model — tách riêng khỏi `agent-7-layers` vì nội dung sâu hơn hẳn 6 layer
  còn lại (5 khối `<details>` so với 4 khối của các layer khác).
- Cập nhật `agent.md` (link tới `agent-7-layers` — góc nhìn hạ tầng mở rộng "3 thành phần nền tảng")
  và `model-selection.md` (link tới `model-hosting` — phân biệt chọn model theo TÁC VỤ vs theo HẠ TẦNG).

## Files
| File | Action |
|------|--------|
| `wiki/sources/290726-kv-cache-llm-hosting.md` | created |
| `wiki/concepts/agent-7-layers.md` | created |
| `wiki/concepts/model-hosting.md` | created |
| `wiki/concepts/agent.md` | edited |
| `wiki/concepts/model-selection.md` | edited |
| `wiki/index.md` | updated |
| `wiki/log.md` | modified |

## Notes
- Invoked via: người dùng chỉ thẳng vào file raw kèm khiếu nại nội dung thiếu, không qua slash-command
  `/ingest` chính thức — thực hiện thủ công theo đúng quy ước OKF (frontmatter, wikilink, index/log)
  đã dùng ở lần ingest trước (`270726-ingest-agent-guide`).
- `raw/290726-kv-cache-llm-hosting.html` không bị chỉnh sửa (R1); chỉ đọc.
- File gốc rất dài (1412 dòng, nhiều CSS/SVG trang trí docs-site-macos) — nội dung text thật (card,
  checklist, bảng, ví dụ) được trích lọc, bỏ qua toàn bộ style/script không mang thông tin.

## Origin
- **Draft:** `wiki/sources/draft/030826-ingest-kv-cache-llm-hosting.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
