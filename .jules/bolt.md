# Bolt's Performance Journal

## 2025-02-18 - Batching I/O in State Persistence Loop
**Learning:** In progress tracking mechanisms that commit sequential messages (like `_flush_completed`), invoking network and local I/O calls (such as file writes or R2 object uploads) inside the iteration loop introduces a massive O(N) network latency/I/O bottleneck. Since state updates are cumulative, only the final state at the end of the flush is required.
**Action:** Always batch state/progress persistence logic outside the processing or iteration loops to reduce complexity from O(N) to O(1) network/disk operations.

## 2025-02-18 - Caching psutil.Process Instance for RSS Queries
**Learning:** Checking memory usage (`psutil.Process().memory_info().rss`) frequently in logging statements or loops creates significant overhead due to repeated imports and process object instantiation. Caching the `Process` instance globally yields a ~2.63x performance boost for RSS lookups.
**Action:** Lazily initialize and cache system-resource checking objects (like `psutil.Process`) at module-level, and avoid inline imports/re-instantiation.
