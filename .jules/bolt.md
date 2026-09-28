# Bolt's Performance Journal

## 2025-05-18 - Batching State Persistence in Transfer Flushing
**Learning:** In batch message flushing loops, calling network-bound state persistence (`_persist_progress_state`) inside the `while` loop turns a sequential flush of N messages into N distinct network HTTP requests (R2 upload) and disk writes. Moving state persistence outside the loop reduces this to 1 network request per flush pass (O(N) -> O(1)).
**Action:** When flushing or committing sequential state updates in async event loops, accumulate/advance progress in-memory within the loop and batch state persistence calls once after the loop finishes.
