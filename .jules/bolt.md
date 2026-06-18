## 2026-06-18 - Optimized I/O and System Monitoring
**Learning:** Instantiating `psutil.Process()` and performing redundant network checks (like R2 `HEAD` requests) are significant bottlenecks in high-throughput data pipelines. Caching system handles and batching state persistence can reduce overhead by an order of magnitude.
**Action:** Always cache long-lived system handles (like Process handles) and batch I/O operations (like state syncs) to the end of a processing cycle instead of per-message.
