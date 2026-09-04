## 2025-05-18 - Batching Progress State Persistence in Transfer Loop

**Learning:** Calling `_persist_progress_state()` inside the `_flush_completed` iteration loop resulted in redundant O(N) local disk I/O and Cloudflare R2 network PUT requests for every completed item in a flush batch. Batching `_persist_progress_state()` outside the loop reduces this overhead to a single O(1) invocation per flush cycle while maintaining exact progress consistency.
**Action:** Always inspect queue processing and batch completion loops for redundant I/O or network calls that can be safely batched after loop termination.
