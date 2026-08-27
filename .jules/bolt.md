# Bolt's Journal - Critical Learnings

## 2025-05-18 - Batching Progress State Persistence in Transfer Pipeline
**Learning:** Persisting progress state (`_persist_progress_state`) inside the loop in `_flush_completed` executes both local disk file writes and remote R2 S3 `put_object` requests for every individual contiguous message. Batching this persistence call outside the loop reduces state sync calls from O(N) to O(1) per flush execution, eliminating redundant network/disk I/O bottlenecks without sacrificing consistency.
**Action:** Always batch I/O operations (file/network sync) when processing contiguous streams or completed task buffers.
