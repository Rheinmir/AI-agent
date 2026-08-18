---
type: source
title: Env promotion
aliases: ["dev uat stage prod", "promotion"]
tags: [cheatsheet, ci-cd]
timestamp: 2026-08-05
---

# Env promotion

Luồng promote môi trường dev -> uat -> stage -> production:
- dev: môi trường của dev, đổi liên tục, dữ liệu giả/mock, không cần độ ổn định cao.
- uat (User Acceptance Testing): stakeholder/QA xác nhận tính năng đúng yêu cầu nghiệp vụ trước
  khi đi tiếp — không phải nơi test kỹ thuật sâu.
- stage (staging): mô phỏng production càng sát càng tốt (cùng config, gần cùng data shape/scale)
  — nơi cuối để bắt lỗi trước khi ảnh hưởng người dùng thật.
- production: môi trường người dùng thật dùng — mọi thay đổi nên đã đi qua các bước trên, và có
  kế hoạch rollback rõ ràng trước khi deploy.

Nguyên tắc chung: build 1 lần (artifact/image duy nhất), promote CÙNG 1 artifact đó qua từng môi
trường — không build lại riêng cho từng môi trường (tránh lệch do build khác nhau).

## Origin
- Di dời từ `data_collector.py::_CHEATSHEETS` (dict hardcode) sang wiki — xem `wiki/log.md` entry
  "wiki-per-agent-memory".
