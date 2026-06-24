## 2026-06-24 - Optimize state persistence batching
**Learning:** Persisting progress state to Cloudflare R2 for every single message processed introduces significant network and I/O overhead. Batching this operation to occur once per batch of completed messages (e.g., after processing a concurrent group) results in a measurably more efficient pipeline (~98% reduction in state-related I/O calls for a batch of 50).
**Action:** Identify high-frequency I/O operations in data processing pipelines and implement batching to reduce overhead while maintaining enough durability for resume logic.
