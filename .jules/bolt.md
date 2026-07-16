# Bolt's Journal - Critical Learnings

## 2025-05-15 - Initial Performance Audit
**Learning:** Found O(N) performance bottleneck in `TransferService._flush_completed` where `_persist_progress_state` (involving R2 network calls and local I/O) is called inside a loop for every processed message. Also noticed redundant `psutil.Process()` creation and double-calling `current_rss_bytes()` per log entry.
**Action:** Batch `_persist_progress_state` outside the loop. Cache the `psutil` process object. Capture RSS once per log event and reuse.
