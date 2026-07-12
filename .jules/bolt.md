## 2026-07-12 - [Batching Progress State Persistence]
**Learning:** Found an O(N) bottleneck in `TransferService._flush_completed` where `_persist_progress_state()` (which involves an R2 network call) was inside a `while` loop. This caused significant delays during catch-up phases or when processing many messages simultaneously.
**Action:** Move state persistence outside of sequential loops to achieve O(1) I/O per batch cycle.
