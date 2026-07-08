## 2025-05-15 - Redundant RSS reporting overhead
**Learning:** Frequent calls to `psutil.Process()` to report memory usage in logs can add measurable overhead. In this codebase, every logged message was fetching RSS twice (for bytes and MB), and each utility call was reinstantiating the process object.
**Action:** Cache the `psutil.Process()` instance globally and capture the RSS value once per logging event to reuse it for multiple derived metrics.
