## 2025-05-15 - Progress Persistence Bottleneck
**Learning:** Calling `_persist_progress_state()` (which involves R2 network calls and local I/O) inside a loop during message flushing creates an O(N) bottleneck. For a 50-message batch with 10ms latency per call, this adds 0.5s of overhead per flush cycle.
**Action:** Always batch state persistence outside of processing loops. Batching reduced flush time from 0.51s to 0.01s (~50x speedup).

## 2025-05-15 - Utility Overhead in Hot Paths
**Learning:** `current_rss_bytes()` was creating a new `psutil.Process()` instance and performing repeated imports on every call. In high-frequency logging paths, this overhead accumulates.
**Action:** Cache the process object and avoid redundant imports. Captured RSS value once when logging multiple metrics to further reduce overhead. Cached utility calls achieved a ~2x speedup.
