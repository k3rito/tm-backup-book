# Bolt ⚡ Performance Journal

**Mission:** Identify and implement one small performance improvement that makes the application measurably faster or more efficient.

**Philosophy:**
- Speed is a feature
- Every millisecond counts
- Measure first, optimize second
- Don't sacrifice readability for micro-optimizations

## Critical Learnings

## 2025-05-14 - Batching Progress Persistence
**Learning:** Persisting state to R2 and local disk for every message in a batch creates O(N) network and I/O overhead. Batching these updates reduces it to O(1) per flush cycle.
**Action:** Always consider if state persistence can be deferred to the end of a logical unit of work (like a batch flush) rather than per-item.
