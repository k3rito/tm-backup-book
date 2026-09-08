## 2025-05-18 - Progress State Batching Optimization
**Learning:** In async pipelines with incremental progress tracking, persisting state inside the item-processing loop executes $O(N)$ network requests to R2 and local disk writes per flush batch. Batching state persistence outside the loop reduces I/O complexity from $O(N)$ to $O(1)$ per flush.
**Action:** Always verify if state persistence calls inside batch-flushing loops can be moved after the loop processes all contiguous completed items.
