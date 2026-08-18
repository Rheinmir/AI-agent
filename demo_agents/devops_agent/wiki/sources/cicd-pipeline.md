---
type: source
title: CI/CD pipeline
aliases: ["ci/cd", "cicd", "pipeline"]
tags: [cheatsheet, ci-cd]
timestamp: 2026-08-05
---

# CI/CD pipeline

CI/CD pipeline — các bước điển hình:
- CI (Continuous Integration): lint -> unit test -> build artifact/image -> (tuỳ) scan bảo mật —
  chạy tự động mỗi khi có commit/PR, mục tiêu là phát hiện lỗi CÀNG SỚM CÀNG TỐT.
- CD (Continuous Delivery/Deployment): lấy artifact đã qua CI, deploy tới môi trường kế tiếp theo
  pipeline (dev -> uat -> stage -> prod), thường có bước approve thủ công trước prod (Continuous
  Delivery) hoặc tự động hoàn toàn (Continuous Deployment).
- Gate phổ biến giữa các bước: test coverage tối thiểu, security scan pass, health check sau
  deploy pass trước khi coi là thành công (và tự rollback nếu fail).

## Origin
- Di dời từ `data_collector.py::_CHEATSHEETS` (dict hardcode) sang wiki — xem `wiki/log.md` entry
  "wiki-per-agent-memory".
