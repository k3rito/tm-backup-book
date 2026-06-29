## 2026-06-29 - Utility Function Optimization
**Learning:** Significant performance gains can be achieved in utility functions by caching expensive objects like `psutil.Process()` and pre-compiling regular expressions that are used frequently.
**Action:** Always pre-compile regexes at the module level and cache reusable system-level objects to reduce initialization overhead in hot code paths.
