## 2025-05-15 - R2 Persistence Overhead in Pipeline
**Learning:** Calling R2 for state persistence on every single message completion creates a massive performance bottleneck due to network latency and API overhead, especially when processing many small messages or catching up.
**Action:** Batch state persistence to R2 by moving it out of the completion loop, ensuring we only persist once per batch of processed messages.

## 2025-05-15 - Inline Import Overhead
**Learning:** `import` statements inside frequently called utility functions like `current_rss_bytes` add unnecessary overhead for every execution. While Python caches modules, there is still a lookup cost.
**Action:** Move library imports to the module level to ensure they are loaded once and shared across all calls.
