# Bolt's Journal - Critical Learnings Only

## 2025-07-29 - Cache psutil.Process instance to minimize RSS query overhead
**Learning:** Calling `psutil.Process()` on every single RSS retrieval constructs a new `Process` object and triggers costly system-level queries. Caching the `psutil.Process()` instance globally reduces execution time by ~2.6x (from ~0.34s to ~0.13s for 5,000 iterations). Additionally, retrieving current RSS once and reusing it for byte and MB formatted logger parameters reduces redundant system-level queries.
**Action:** Lazily initialize a global `_PROCESS` variable inside `current_rss_bytes()` in `utils.py`, and assign/reuse RSS values in local variables before passing to logger calls.
