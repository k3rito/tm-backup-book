# Bolt ⚡ Journal

## 2025-05-15 - Batching State Persistence
**Learning:** Performing network and disk I/O (R2 upload + local file write) inside a message processing loop creates a significant bottleneck when processing batches of messages or skipping large gaps in Telegram message IDs.
**Action:** Always batch persistence operations to O(1) per flush cycle. Ensure progress state advances correctly even when messages are skipped to maintain efficient resume behavior.
