## 2025-02-14 - Cache Process Object for RSS Monitoring
**Learning:** Instantiating `psutil.Process()` on every call to fetch the RSS memory metric incurs a significant performance penalty (about 2.9x slower) due to repeated library/system overhead.
**Action:** Lazily instantiate and cache `psutil.Process()` in a module-level variable to avoid redundant construction when retrieving RSS memory statistics.
