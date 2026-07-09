## 2025-05-15 - Batching Progress Persistence
**Learning:** Calling I/O-bound persistence methods inside a hot loop (like flushing sequential message IDs) creates an O(N) performance bottleneck where N is the number of sequential messages.
**Action:** Always batch I/O operations outside of loops when possible. Use a flag (e.g., `advanced`) to track if work was done and requires persistence at the end of the batch.
