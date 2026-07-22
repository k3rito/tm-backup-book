# Bolt's Performance Journal

This journal logs critical, repository-specific performance learnings to avoid regressions and guide future optimization work.

## 2025-02-13 - [O(1) Progress Persistence & psutil Caching]
**Learning:** Frequent Cloudflare R2 and local disk writes during progress tracking create significant I/O latency bottlenecks. Transitioning the progress check from inside the sequential commit loop to a batched flush after the sequential commits are processed reduces these costly network and disk operations from O(N) to O(1) per flush iteration. Additionally, caching the `psutil.Process()` instance prevents heavy overhead from redundant library loading and OS level queries.
**Action:** Always batch I/O and state persistence operations when processing queues or iterations, and lazily cache system monitoring objects like `psutil.Process()` globally.
