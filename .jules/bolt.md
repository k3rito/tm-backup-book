## 2025-05-15 - Batching State Persistence in TransferService
**Learning:** Calling `_persist_progress_state()` (which involves R2 network calls and local I/O) inside the `_flush_completed` loop was a significant bottleneck when multiple messages were committed in a single batch. Moving it outside the loop reduces operations from O(N) to O(1) per batch.
**Action:** Always identify opportunities to batch I/O operations when processing sequential tasks or messages.
