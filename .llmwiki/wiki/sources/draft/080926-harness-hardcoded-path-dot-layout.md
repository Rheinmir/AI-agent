---
type: issue
kind: tech-debt
title: "Global harness hooks/scripts hardcode \"harness/\" path, ignore dot-layout (.harness/) migration they themselves introduced"
status: open
assignee: harness-maintainer
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, harness, dot-layout, tech-debt]
timestamp: 2026-09-08
id: 080926-harness-hardcoded-path-dot-layout
tracker: https://github.com/Rheinmir/AI-agent/issues/1
source_session: AI-agent repo — phát hiện sau khi tạo remote GitHub + push, git status lặp lại
  báo một thư mục harness/ trần mới xuất hiện dù repo đã migrate sang .harness/ từ 2026-08/09.
---

# Issue: Global harness hooks/scripts hardcode "harness/" path, ignore dot-layout (.harness/) migration they themselves introduced

## Vấn đề (một câu)
`~/.claude/harness/` (hooks + scripts chạy GLOBAL cho mọi dự án) hardcode `root / "harness"` ở
~50+ điểm chạm, nên trên bất kỳ dự án nào đã migrate sang layout ẩn `.harness/` (chính do
`install.sh`'s `migrate_dot_layout()` của framework này thực hiện), các hook đó vẫn âm thầm ghi
dữ liệu / tái tạo lại một thư mục `harness/` trần mới — đúng vấn đề mà dot-layout được sinh ra để
giải quyết.

## Bối cảnh & bằng chứng
- Repo `AI-agent` (https://github.com/Rheinmir/AI-agent) đã migrate `harness/` → `.harness/` và
  `llmwiki/` → `.llmwiki/` (commit `eddb76e`, xem `.llmwiki/wiki/log.md` §2026-08-29/2026-09-08) —
  do chính `.harness/poc-vendor-neutral/install.sh`'s `migrate_dot_layout()` thực hiện, lý do nêu
  trong script: framework nằm trần ở gốc dự án khiến design/lint scanner (hallmark, impeccable...)
  quét `**/*.html` vớ phải file nội bộ framework rồi chấm nó như UI sản phẩm.
- Sau khi migrate xong và commit sạch, phiên tiếp theo (`git status`) lại thấy 1 thư mục `harness/`
  TRẦN mới xuất hiện, chỉ chứa `harness/metrics/cost-by-session.json` — untracked, lặp lại mỗi
  phiên dù đã xoá.
- Truy vết: `~/.claude/harness/hooks/code-logger.py` (`_cost_path()`, dòng ~191) và bản sao ở
  `~/.claude/harness/harness/scripts/code-logger.py` hardcode `root / "harness" / "metrics"` —
  không kiểm tra xem dự án có `.harness/` hay không trước khi ghi.
- Grep toàn bộ `~/.claude/harness/` cho thấy đây KHÔNG PHẢI lỗi một chỗ — `root / "harness"` (và
  biến thể `ROOT / "harness"`, `Path(root) / "harness"`) xuất hiện trong:
  - `hooks/`: `code-logger.py`, `session_start.py`, `build-capabilities.py`, `hooklib.py`
  - `harness/scripts/`: `token-budget.py`, `bnal_metrics.py`, `bnal_config.py`,
    `claim-receipts.py`, `mem-rank.py`, `mem-proxy.py`, `wikieval.py`, `query-log.py`,
    `provenance-log.py`, `scratch-log.py`, `flywheel.py`, `ledger-snapshot.py`,
    `grounding-check.py`, `egress-guard.py`, `prospect-critic.py`, `inject-scan.py`,
    `trace-otel.py`, `scoped-hooks.py`, `spec-gate.py`, `web-crawl.py`, `web-clone.py`,
    `capability-stamp.py`, `retrieval-eval.py`
- Đối chứng: `hooklib.py` (dòng ~55/58) VÀ `install.sh` chính nó (bash level:
  `HARNESS_DIR="harness"; [ -d "$ROOT/.harness" ] && HARNESS_DIR=".harness"`) ĐÃ có tiền lệ resolve
  đúng 2 layout — chỉ là logic này chưa được rút thành helper dùng chung rồi áp lại cho toàn bộ
  các điểm chạm Python còn lại.

## Phạm vi
- **Universal** — ảnh hưởng `~/.claude/harness/` (global, dùng chung cho MỌI dự án bật dot-layout),
  KHÔNG riêng gì repo `AI-agent`. `AI-agent` chỉ là nơi phát hiện triệu chứng.
- Các file cần sửa: toàn bộ danh sách grep ở trên trong `~/.claude/harness/hooks/*.py` và
  `~/.claude/harness/harness/scripts/*.py`.

## Không thuộc phạm vi
- KHÔNG sửa gì trong repo `AI-agent` — repo này không sở hữu code global đó, chỉ là môi trường
  quan sát triệu chứng.
- KHÔNG tự động migrate dữ liệu cũ đã lỡ ghi nhầm vào `harness/metrics/*.json*` ở các dự án khác
  (ngoài phạm vi biết được từ 1 phiên) — để phiên nhận issue tự quyết định có cần bước migrate dữ
  liệu hay không sau khi khảo sát thêm.
- KHÔNG đổi lại quyết định dot-layout (đã chốt, có lý do rõ — chống scanner quét nhầm).

## Hướng gợi ý (không bắt buộc)
- Thêm helper dùng chung, ví dụ trong `hooklib.py`:
  `def resolve_harness_dir(root: Path) -> Path: return root / ".harness" if (root / ".harness").is_dir() else root / "harness"`
  — mirror đúng logic bash `HARNESS_DIR` đã có trong `install.sh`.
- Thay toàn bộ `root / "harness"` bằng gọi helper này (import từ `hooklib` nếu các script khác đã
  import nó, hoặc factor helper vào một module dùng chung thấp hơn nếu chưa).
- Verify sống: chạy 1 phiên Claude Code trong dự án đã dot-layout (vd `AI-agent`), xác nhận Stop
  hook không còn tạo lại `harness/` trần; `cost-by-session.json`/`memory.jsonl`/`tokens.jsonl`...
  tiếp tục UPSERT đúng vào `.harness/metrics/`.
- Cân nhắc thêm bước migrate-once cho dữ liệu cũ nếu phát hiện dự án nào đã bị ghi rải rác ở cả 2
  path do bug này.

## Tiêu chí HOÀN THÀNH
- [ ] Có helper resolve layout dùng chung (`.harness` nếu tồn tại, ngược lại `harness`), không lặp
      logic rải rác từng file.
- [ ] Toàn bộ ~50+ điểm chạm `root / "harness"` liệt kê ở trên đã chuyển sang dùng helper.
- [ ] Chạy sống 1 phiên trong repo dot-layout (`AI-agent`) — Stop hook / SessionStart hook không
      tạo lại thư mục `harness/` trần; dữ liệu ghi đúng vào `.harness/metrics/`.
- [ ] Không có regression cho dự án CHƯA migrate (vẫn dùng `harness/` trần như cũ — helper phải
      fallback đúng khi không có `.harness/`).

## Assign & lý do
- `assignee: harness-maintainer` — đây là code sở hữu bởi chính framework harness
  (`~/.claude/harness/`), không thuộc quyền sửa của một dự án con như `AI-agent`. Người/phiên nhận
  cần quyền truy cập vào cây global đó.
- `dispatch: Claude` — thay thế cơ học, có pattern đối chứng sẵn (`hooklib.py`/`install.sh`), phù
  hợp giao cho agent làm với review sau.
- `entry: /fdk` — đây là sửa framework (harness tooling), không phải feature của dự án `AI-agent`.

## Origin
- Raised by: phiên Claude Code trong repo `AI-agent`, ngay sau khi tạo remote GitHub + push +
  rewrite lịch sử tác giả (commit `eddb76e`), lúc kiểm tra `git status` thấy thư mục `harness/`
  trần tái xuất hiện.
- Bằng chứng trực tiếp: `grep -rn 'root / "harness"' ~/.claude/harness/hooks/*.py
  ~/.claude/harness/harness/scripts/*.py` (chạy trong phiên này, ~50+ dòng khớp).
- Tham chiếu thiết kế dot-layout gốc: comment trong
  `.harness/poc-vendor-neutral/install.sh` (đề xuất "040926-downstream-dot-layout" — không tìm
  thấy ADR tương ứng trong wiki của repo `AI-agent`, có thể sống ở repo nguồn của framework).
