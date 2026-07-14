## 2025-05-15 - Redundant R2 State Persistence
**Learning:** Persisting progress state to R2 inside the `_flush_completed` loop created an O(N) network bottleneck, significantly slowing down the commit phase of message processing.
**Action:** Move state persistence outside the loop to batch updates, reducing the cost from O(N) to O(1) per flush cycle.
