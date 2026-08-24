# Bolt's Journal - Critical Learnings

## 2025-05-18 - Batching State Persistence in Transfer Flushing
**Learning:** Persisting progress state inside the `_flush_completed` loop triggered an R2 JSON upload and file write for every single completed message sequentially, creating an O(N) network bottleneck during batch completion.
**Action:** Always batch I/O and state persistence operations outside loops when accumulating sequential state updates.
