## 2026-08-30 - Batch Progress State Persistence in Flush Loops
**Learning:** Persisting progress state inside the item-by-item flush loop in `TransferService._flush_completed()` creates an $O(N)$ overhead where each completed media item triggers local disk and R2 network I/O.
**Action:** Always batch state updates outside item-by-item completion loops so that progress state is persisted once per flush batch ($O(1)$ complexity).
