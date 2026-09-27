## 2025-05-18 - Batching Progress State Persistence in Transfer Flushing
**Learning:** Invoking async `_persist_progress_state()` (local disk write + Cloudflare R2 object upload) inside the `_flush_completed` loop created an $O(N)$ network/file I/O bottleneck when committing multiple messages in a single flush cycle.
**Action:** Always buffer in-memory state updates inside commit loops and batch progress state persistence outside the loop to execute $O(1)$ times per flush cycle.
