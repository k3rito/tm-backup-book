## 2025-05-15 - Batching State Persistence & Lean Resource Monitoring
**Learning:** Per-message R2/S3 state persistence and local disk I/O are massive bottlenecks in high-throughput streaming services. Additionally, inline imports and object instantiation in frequently called monitoring functions (like memory checks for logging) add significant CPU overhead.
**Action:** Always batch I/O operations in main processing loops and cache system handles/pre-compile regex at the module level to minimize overhead in hot paths.
