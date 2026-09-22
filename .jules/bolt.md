## 2025-05-18 - Batch Progress State Persistence in `_flush_completed` Loop
**Learning:** Calling async network/disk persistence inside an inner loop processing batch outcomes creates an $O(N)$ overhead where $N$ network calls to R2 and disk writes are executed per flush. Moving persistence outside the loop updates the state once per batch ($O(1)$ operations).
**Action:** When flushing or committing sequential state updates in async worker loops, batch the persistence/sync operation after all items in the current batch have been processed.
