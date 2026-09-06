## 2025-05-18 - Batched Progress State Persistence in Transfer Flushing
**Learning:** Calling `_persist_progress_state()` inside the `_flush_completed` loop triggered O(N) network requests to Cloudflare R2 and disk writes per flush batch, creating a severe I/O bottleneck when committing multiple messages.
**Action:** Move state persistence outside of the item processing loop so state is written once (O(1)) per flush batch.
