---
type: adr
title: issue-tracker
status: accepted
tags: [issue-tracker, adapter-boundary]
timestamp: 2026-09-08
id: issue-tracker
---

# issue-tracker

Hợp đồng adapter cho `raise-issue`/`orca-issue`: ledger local là NGUỒN CHÂN LÝ, tracker remote (nếu
có) chỉ là bản mirror để phối hợp/hiện Issues tab/assign người thật.

## Ledger (nguồn chân lý)
- Issue: `.llmwiki/wiki/sources/draft/DDMMYY-<slug>.md`
- Index: `.llmwiki/wiki/sources/ISSUES.md`
- Repo dùng layout dot-prefix (`.llmwiki/` thay vì `llmwiki/` — xem
  `demo_agents/devops_agent/web/design.md` / `.harness/poc-vendor-neutral/install.sh`
  `migrate_dot_layout()`), nên mọi path issue trong repo này đọc dưới `.llmwiki/...`, không phải
  `llmwiki/...` trần.

## Tracker remote — GitHub Issues (gh)
- Repo có remote `origin` → `https://github.com/Rheinmir/AI-agent` (xác nhận qua
  `git remote get-url origin`, tạo 2026-09-08).
- CLI: `gh` (đã đăng nhập account `Rheinmir`, xác nhận qua `gh auth status`).
- Mirror: `gh issue create --repo Rheinmir/AI-agent --title "<title>" --body "<body có link ngược
  về file ledger>"` — ghi URL trả về vào cột `tracker` trong `ISSUES.md`.
- Labels: 5 nhãn chuẩn `needs-triage` · `needs-info` · `ready-for-agent` · `ready-for-human` ·
  `wontfix`. Repo GitHub mới tạo chưa có sẵn các label này — cần `gh label create` trước lần mirror
  đầu nếu muốn gắn label (không bắt buộc để mirror thành công).
- Body issue remote PHẢI link ngược file ledger (đường dẫn tương đối trong repo) để tracker không
  bao giờ là nguồn chân lý độc lập.

## Origin
- Tạo bởi `raise-issue` skill lúc chưa có file hợp đồng (mặc định local-markdown + đề xuất mirror
  gh vì phát hiện remote GitHub đã có sẵn), phiên raise issue
  `080926-harness-hardcoded-path-dot-layout`.
