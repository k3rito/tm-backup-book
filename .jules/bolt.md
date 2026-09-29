## 2025-05-20 - Batch Progress Persistence in Flush Loop
**Learning:** Calling `_persist_progress_state()` inside the `_flush_completed()` while loop triggered $O(N)$ sequential R2 `upload_text_object` HTTP requests and local disk file writes per batch flush.
**Action:** Always batch progress state persistence outside loop processing so that $N$ committed outcomes emit exactly 1 state sync operation ($O(1)$ complexity per flush batch).
