## 2025-02-15 - Batch State Persistence in Transfer Loop
**Learning:** In the `TransferService._flush_completed` loop, saving and syncing progress to R2 on every single item inside the `while` loop creates an O(N) network bottleneck, sending N redundant S3/R2 requests. This is because multiple sequential files can be flushed together.
**Action:** Move `_persist_progress_state` out of the loop, executing it only once at the end of the flush operation. This optimizes state synchronization to O(1) time complexity per batch.
