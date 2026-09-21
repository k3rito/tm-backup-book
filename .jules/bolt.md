## 2026-03-29 - Batching Progress State Persistence in Transfer Flush
**Learning:** Calling `_persist_progress_state()` inside the `_flush_completed` loop triggered $O(N)$ async local file writes and R2 network PUT requests per completed batch. Deferring persistence until after processing all completed message outcomes in the loop reduces I/O calls to $O(1)$ per flush cycle.
**Action:** Always check loop bodies handling completed async tasks or batch outcomes for repeated network/disk persistence calls, and batch state persistence outside the loop when state updates can be aggregated safely.
