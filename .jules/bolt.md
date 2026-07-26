# Bolt's Journal

## 2024-11-19 - Psutil Global Process Instance Caching
**Learning:** In a performance-critical logging flow that repeatedly queries system memory metrics via `psutil`, instantiating `psutil.Process()` on every call causes measurable syscall and CPU overhead (~2.6x slower). Caching the process object globally lazily avoids redundant process object creation and module imports.
**Action:** Always cache process or system-state-handle instances globally when implementing high-frequency memory/telemetry checks.

## 2024-11-19 - Batching State Persistence to Cloudflare R2
**Learning:** Performing a remote API write (putting a small JSON payload to Cloudflare R2) sequentially inside a high-concurrency flush loop degrades throughput significantly. Intermediate updates are redundant when processing sequential message blocks; only the final state is relevant for state persistence.
**Action:** Batch network I/O and state sync outside of flush loops to turn O(N) remote I/O calls into O(1).
