## 2025-05-14 - [Initial Performance Assessment]
**Learning:** The application performs frequent R2 network calls for state persistence (one per message) and redundant object existence checks. The `current_rss_bytes` utility also has avoidable overhead.
**Action:** Implement batching and throttling for state persistence, remove redundant R2 calls, and optimize memory usage utility.
