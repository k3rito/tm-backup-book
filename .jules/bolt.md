# Bolt ⚡ Performance Journal

## 2025-05-15 - Batching State Persistence and Optimizing Telemetry

**Learning:** Per-message state persistence (local disk + R2 upload) in an async pipeline is extremely expensive due to I/O and network latency. Batching these operations to occur once per completed set of sequential messages provides a ~98% reduction in overhead for a batch of 50. Additionally, re-instantiating `psutil.Process()` on every memory check in a hot logging path adds significant avoidable latency.

**Action:** Always look for opportunities to batch state-sync operations in transfer pipelines. Cache system-level process objects for telemetry instead of re-creating them on every call.
