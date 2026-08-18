---
type: source
title: Deployment patterns
aliases: ["blue-green", "canary", "rolling update"]
tags: [cheatsheet, deployment]
timestamp: 2026-08-05
---

# Deployment patterns

Pattern triển khai ứng dụng phổ biến:
- Rolling update: thay dần từng phần instance cũ bằng mới, không downtime nhưng có lúc cả 2
  phiên bản cùng chạy song song — cần đảm bảo tương thích ngược (backward-compatible API/schema)
  trong lúc chuyển tiếp.
- Blue-Green: dựng song song 2 môi trường độc lập (blue=đang chạy, green=bản mới), chuyển traffic
  tức thời khi green sẵn sàng — rollback cực nhanh (chuyển traffic ngược lại) nhưng tốn gấp đôi
  tài nguyên trong lúc chuyển đổi.
- Canary: đưa bản mới ra cho một tỉ lệ traffic nhỏ trước (vd 5%), theo dõi lỗi/latency rồi tăng
  dần — giảm rủi ro nhưng cần hạ tầng theo dõi tốt để phát hiện vấn đề sớm.
- Feature flag: deploy code mới nhưng ẩn tính năng sau flag, bật dần theo nhóm người dùng — tách
  rời việc DEPLOY code khỏi việc RELEASE tính năng.

## Origin
- Di dời từ `data_collector.py::_CHEATSHEETS` (dict hardcode) sang wiki — xem `wiki/log.md` entry
  "wiki-per-agent-memory".
