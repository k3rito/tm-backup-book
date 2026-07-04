## 2025-05-14 - Caching psutil.Process() for RSS memory monitoring
**Learning:** Instantiating `psutil.Process()` (without arguments) is expensive as it involves multiple system calls to resolve the current process. Caching this instance provides a significant speedup (~2.6x) for functions that frequently monitor memory usage, such as `current_rss_bytes()` in logging contexts.
**Action:** Always cache the `psutil.Process()` instance if it's used repeatedly within the same process lifecycle.
