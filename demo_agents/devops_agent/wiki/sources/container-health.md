---
type: source
title: Container health check
aliases: ["docker health", "healthcheck", "health check"]
tags: [cheatsheet, containers]
timestamp: 2026-08-05
---

# Container health check

- Liveness probe: 'container này còn sống không' — probe fail nhiều lần liên tiếp thì container
  bị kill và restart. Dùng cho lỗi treo (deadlock) không tự phục hồi được.
- Readiness probe: 'container đã sẵn sàng nhận traffic chưa' — probe fail thì pod bị gỡ khỏi
  Service endpoints (không traffic mới vào) nhưng KHÔNG bị restart. Dùng cho lúc khởi động chậm
  (đang load cache, đang kết nối DB).
- Startup probe: cho container khởi động rất chậm — trì hoãn liveness/readiness probe tới khi
  startup probe pass lần đầu, tránh bị kill oan lúc mới boot.
- Docker HEALTHCHECK (Dockerfile): tương tự nhưng đơn giản hơn, chỉ có 1 trạng thái
  healthy/unhealthy/starting, không tách liveness/readiness.

## Origin
- Di dời từ `data_collector.py::_CHEATSHEETS` (dict hardcode) sang wiki — xem `wiki/log.md` entry
  "wiki-per-agent-memory".
