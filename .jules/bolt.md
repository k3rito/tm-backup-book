## 2025-05-18 - Batching Progress State Sync in Transfer Flushing
**Learning:** Calling `_persist_progress_state()` inside the `_flush_completed` loop triggered sequential R2 network uploads and local I/O for every committed message in a flush sequence (O(N) network requests).
**Action:** Always batch state persistence outside sequential commit loops so that only the final progress state is written to disk and R2 per batch (O(1) network requests).
