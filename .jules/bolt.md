## 2025-05-15 - Batching Progress Persistence
**Learning:** The `_flush_completed` loop was performing O(N) I/O and network operations by calling `_persist_progress_state()` for every message in a flush cycle. For a batch of 50 messages, this caused a 50x slowdown (0.51s vs 0.01s).
**Action:** Always batch state persistence outside of processing loops to minimize expensive I/O and network overhead, especially when handling out-of-order completions.

## 2025-05-15 - Process Object Overhead
**Learning:** Calling `psutil.Process()` repeatedly in logging hot-paths (like `current_rss_bytes`) adds unnecessary overhead due to repeated library imports and system object instantiation.
**Action:** Cache heavy system-querying objects (like process handles) globally and use lazy initialization to minimize utility overhead in high-frequency call sites.
