## 2026-07-15 - O(N) persistence bottleneck in completion loop
**Learning:** The service was performing a network call and local file write for every single completed message within the flush loop, creating a significant O(N) I/O bottleneck during high-throughput transfers.
**Action:** Always batch state persistence outside of processing loops to minimize network and disk overhead, especially when dealing with sequential progress tracking.
