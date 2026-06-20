## 2025-05-14 - Initial Performance Audit
**Learning:** The application has several small performance bottlenecks: redundant network I/O (R2 HEAD requests), excessive state persistence (R2 writes on every message), and inefficient system calls (re-creating psutil.Process).
**Action:** Prioritize batching R2 state updates as it has the highest impact on cost and latency when processing large batches of messages.
