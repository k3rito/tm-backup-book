## 2025-05-14 - [Avoid Scope Creep in Performance PRs]
**Learning:** Combining performance optimizations with general "code cleanup" (like removing unused imports or variables) increases the risk of regressions (e.g., NameErrors) and complicates the review process.
**Action:** Strictly limit PRs to the identified performance improvement. Focus exclusively on the primary bottleneck to maintain code safety and review clarity.

## 2025-05-14 - [Caching psutil.Process() for RSS monitoring]
**Learning:** Instantiating `psutil.Process()` on every call to fetch memory metrics (RSS) is expensive due to repeated system-level lookups. Caching the instance at the module level provides a significant speedup.
**Action:** Always cache the `psutil.Process()` instance when frequent memory monitoring is required.
