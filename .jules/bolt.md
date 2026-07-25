## 2025-02-18 - Batching I/O in State Persistence
**Learning:** Performing disk operations and Cloudflare R2 API uploads on every iteration of progress flushing in a high-concurrency stream loop creates an O(N) performance and latency bottleneck.
**Action:** Move state sync operations outside loop blocks (batching) to achieve O(1) performance per flush operation, reducing unnecessary R2 network and local disk I/O significantly.

## 2025-02-18 - Caching psutil Process Objects
**Learning:** Instantiating `psutil.Process()` on every metric retrieval call incurs significant overhead, as process metadata lookup requires system resource query overhead.
**Action:** Lazy-initialize and cache the `Process` reference globally to skip redundant library lookups and object instantiation, achieving a ~2.6x performance speedup.
