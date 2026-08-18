---
type: source
title: Kubernetes
aliases: ["k8s", "kube"]
tags: [cheatsheet, kubernetes]
timestamp: 2026-08-05
---

# Kubernetes

Kubernetes — lệnh kubectl cơ bản:
- kubectl get pods -n <namespace> — liệt kê pod
- kubectl describe pod <name> — xem event/lý do lỗi (rất hữu ích khi debug CrashLoopBackOff)
- kubectl logs <pod> -c <container> --previous — log của lần container restart trước đó
- kubectl rollout status deployment/<name> — theo dõi tiến độ rollout
- kubectl rollout undo deployment/<name> — rollback về revision trước
- kubectl exec -it <pod> -- sh — vào shell trong container để debug trực tiếp

Vòng đời pod: Pending -> ContainerCreating -> Running -> (Succeeded|Failed). CrashLoopBackOff
nghĩa là container khởi động rồi crash lặp lại — luôn xem 'describe pod' + logs trước, đừng đoán
nguyên nhân.

## Origin
- Di dời từ `data_collector.py::_CHEATSHEETS` (dict hardcode) sang wiki — xem `wiki/log.md` entry
  "wiki-per-agent-memory".
