## 2026-03-10 - Batching Async State Persistence in Transfer Flushing
**Learning:** Calling `_persist_progress_state()` inside the `_flush_completed` loop introduced an $O(N)$ performance bottleneck, triggering redundant R2 network uploads and disk writes for every completed message outcome in a batch.
**Action:** Always batch progress updates so that external I/O and state persistence occur once at the end of a flush operation ($O(1)$ calls per flush).
