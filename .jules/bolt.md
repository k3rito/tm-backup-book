## 2025-02-14 - Optimize Progress Persistence in Flush Loop
**Learning:** Sequential disk write I/O and Cloudflare R2 API requests inside a message-processing loop can create severe O(N) performance bottlenecks when batch-processing contiguous completed messages.
**Action:** Always batch I/O and network operations outside of processing loops to keep operations O(1) per flush call, drastically reducing network roundtrips and local write overhead.
