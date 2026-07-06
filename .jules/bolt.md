## 2025-05-15 - Caching psutil.Process instance
**Learning:** Instantiating `psutil.Process()` repeatedly to monitor RSS memory usage during frequent logging operations introduces unnecessary overhead due to system calls and object setup.
**Action:** Always cache the `psutil.Process()` instance globally or in a long-lived object when frequent memory monitoring is required.
