## 2025-05-14 - Batching state persistence
**Learning:** Persisting state to R2 on every message in a high-frequency loop creates significant I/O overhead. Batching these updates once per flush cycle (after processing a set of messages) significantly improves throughput.
**Action:** Always look for opportunities to batch network-bound or disk-bound persistence operations in high-frequency loops.

## 2025-05-14 - Resource monitoring overhead
**Learning:** Repeatedly importing modules and re-initializing system-level objects like `psutil.Process()` in frequently called utility functions (like memory monitoring) adds unnecessary micro-overhead that accumulates.
**Action:** Cache expensive system-level objects and move imports to the module level for utilities called in hot paths.
