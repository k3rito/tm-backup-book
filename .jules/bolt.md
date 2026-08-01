## 2024-10-24 - [O(1) Flush State Persistence Optimization]
**Learning:** In pipelines processing continuous streams of items, persisting state or checkpoints to external networks/services (like Cloudflare R2) inside hot processing/flushing loops creates a major O(N) overhead bottleneck due to network round-trips.
**Action:** Always batch progress and status persistence outside processing/flushing loops, ensuring we only perform a single, final O(1) state write at the end of the batch operation.
