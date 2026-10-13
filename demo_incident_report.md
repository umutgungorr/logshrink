# 🚨 LogShrink Incident & Noise Reduction Report

- **Generated At**: `2026-10-13 22:29:53`
- **Source**: `demo.log`
- **Total Lines Processed**: `20`
- **Noise Suppressed**: `7 (35.0%)`
- **Unique Incidents Detected**: `1`

## 📊 Incident Overview

| ID | Level | Occurrences | First Seen | Last Seen | Summary |
|---|---|---|---|---|---|
| #1 | **ERROR** | 1x | `22:29:53` | `22:29:53` | `ERROR: 2026-10-13 19:00:09.500 [ERROR] Failed to connect to ` |

---

## 🔍 Detailed Incident Logs

### Incident #1 — ERROR (1x)
- **First Seen**: `22:29:53`
- **Last Seen**: `22:29:53`

```log
2026-10-13 19:00:09.500 [ERROR] Failed to connect to Redis cache cluster at 10.0.0.45:6379
Traceback (most recent call last):
  File "/app/cache/redis.py", line 48, in connect
    sock.connect((self.host, self.port))
  File "/usr/local/lib/python3.12/socket.py", line 710, in connect
    raise ConnectionRefusedError(errno.ECONNREFUSED, 'Connection refused')
ConnectionRefusedError: [Errno 111] Connection refused
```
