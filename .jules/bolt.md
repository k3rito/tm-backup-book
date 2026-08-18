## 2025-05-20 - Process Object Reuse in RSS Memory Benchmarking
**Learning:** Instantiating `psutil.Process()` on every RSS query causes noticeable execution overhead due to process metadata lookups and C-extension initializations. Caching a lazily initialized process reference in a module-level variable reduces RSS query time by ~2.9x (from ~0.085ms to ~0.029ms per call).
**Action:** Always reuse cached process handle instances when querying memory/CPU metrics in frequent loop operations or snapshot utilities.
