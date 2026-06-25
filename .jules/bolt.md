## 2025-05-15 - State Persistence Batching
**Learning:** Per-message state persistence to Cloudflare R2 introduces significant network overhead and latency. In a high-concurrency upload scenario, this becomes a major bottleneck.
**Action:** Batch state updates to happen once per processing cycle or message batch rather than per individual message.

## 2025-05-15 - Logging Path Optimization
**Learning:** Redundant calls to system monitoring functions like `psutil.Process().memory_info().rss` within a single log entry context add unnecessary overhead to the application's hot path.
**Action:** Capture resource metrics once per context and reuse the value for multiple log fields.
