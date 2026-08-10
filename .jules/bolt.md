# Bolt's Journal ⚡

## 2025-02-15 - Progress Serialization Batching
**Learning:** In sequential queue-processing systems like `TransferService`, persisting state on every single transaction/message committed inside a loop introduces a significant $O(N)$ performance bottleneck, dominated by network round-trips to Cloudflare R2 and local disk writes.
**Action:** Always batch persistence operations outside processing or flushing loops to achieve $O(1)$ complexity per batch, ensuring state is synchronized only when the entire batch is successfully updated or forced.
