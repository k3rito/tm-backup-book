# Bolt's Journal - Critical Learnings Only

This journal contains critical learnings that help avoid mistakes or make better decisions regarding performance optimizations.

## 2025-02-14 - [State Serialization & Metric Tracking Optimizations]
**Learning:** Calling remote network updates (like Cloudflare R2 progress state upload) within a sequential message processing flush loop is an O(N) bottleneck that severely impacts transfer throughput. Similarly, retrieving process resource statistics (like RSS memory usage) by instantiating `psutil.Process()` on every metric tracking / logging event introduces significant local CPU overhead (measured 2.63x slower without caching).
**Action:** Always batch state persistence outside of sequential processing loops to achieve O(1) complexity per flush. For telemetry and metric tracking functions (e.g., `current_rss_bytes()`), cache the `psutil.Process()` instance globally as a lazily-initialized variable (`_PROCESS`) to avoid redundant object creation and system calls.
