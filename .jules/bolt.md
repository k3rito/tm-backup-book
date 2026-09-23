## 2025-05-18 - Batch progress state persistence in transfer flush loop
**Learning:** Calling `_persist_progress_state()` inside the `while` loop of `TransferService._flush_completed` caused redundant async disk I/O and Cloudflare R2 PUT network requests for every committed message in a flush batch, creating an O(N) network and disk bottleneck during concurrent transfer flushes.
**Action:** Always batch persistence/state updates outside sequential processing loops when multiple items can be processed or committed in a single iteration batch.
