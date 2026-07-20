## 2025-02-14 - [Shifting Progress Serialization from O(N) to O(1)]
**Learning:** In highly concurrent pipelines where `_flush_completed` resolves multiple completed events, serializing and saving state via I/O and network requests inside the loop causes an O(N) bottleneck. Moving persistence outside the loop resolves all updates in a single batch, providing O(1) performance and drastically reducing latency.
**Action:** Always batch persistence operations to occur after completion loops rather than inside them to avoid heavy unnecessary operations.
