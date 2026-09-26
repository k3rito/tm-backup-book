# Bolt Performance Journal

## 2025-02-25 - Direct Date Attribute Formatting vs `strftime` in Hot Paths
**Learning:** `datetime.strftime` incurs format string parsing and C-level locale lookup overhead that makes it ~1.5x to ~3x slower than direct integer attribute formatting (`d.year`, `d.month`, `d.day`) in Python. When combined with `@functools.lru_cache` for invariant string arguments like channel reference normalization, string path construction in loop/batch processing achieves a ~3.6x speedup.
**Action:** When generating date-based storage keys or file paths in hot paths, format integer attributes (`year`, `month`, `day`) directly in f-strings rather than using `strftime`.
