# Bolt's Performance Journal ⚡

## 2025-05-14 - Batching Progress State Persistence
**Learning:** Persisting the resume state to Cloudflare R2 for every single Telegram message is highly inefficient, especially when processing large batches. This results in O(N) network calls where N is the number of messages. Batching this to once per batch of sequential messages reduces network overhead significantly.
**Action:** Move state persistence out of the per-message loop in `TransferService._flush_completed`.
