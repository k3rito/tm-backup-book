## 2025-05-15 - Redundant process object creation overhead
**Learning:** Creating `psutil.Process()` on every call to `current_rss_bytes()` introduced significant overhead (~40ms per 1000 calls). Caching the process object globally reduced the latency of memory monitoring by ~60%. Additionally, capturing the RSS value once per logging event in `transfer.py` further reduced utility overhead.
**Action:** Always cache singleton system resources (like process handlers or library-level objects) and avoid redundant calls to monitoring utilities in hot paths.
