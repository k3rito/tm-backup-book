## 2026-03-31 - Batching Progress State Persistence in Transfer Loop
**Learning:** Calling async persistence methods (`_persist_progress_state`) inside batch processing loops (`_flush_completed`) causes O(N) network and disk I/O operations per flush. Batching state persistence after the loop reduces I/O calls to O(1) per flush, eliminating redundant R2 API requests and disk file writes.
**Action:** Always defer state persistence or flush operations to after batch processing loops when the state accumulated during the loop is only needed in its final form.
