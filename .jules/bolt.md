# Bolt's Performance Journal ⚡

## 2025-02-17 - O(N) to O(1) Progress Sync Optimization in TransferService
**Learning:** In the loop inside `_flush_completed`, saving the progress state locally and uploading it to Cloudflare R2 on every single loop iteration (O(N) network calls and local I/O operations) is an unnecessary and massive bottleneck, especially when flushing many skipped or processed messages.
**Action:** Move state persistence out of the loop to commit and sync the final progress state exactly once (O(1)) after processing is completed for the batch.

## 2025-02-17 - psutil.Process Instance Caching Optimization
**Learning:** Creating a new `psutil.Process()` instance and re-importing `psutil` on every single memory metric calculation introduces considerable overhead.
**Action:** Cache the lazy-initialized `psutil.Process` instance globally so that subsequent memory checks reuse it, avoiding process lookup and module loading overhead.

## 2025-02-17 - Redundant Metric Checks Optimization
**Learning:** Querying `current_rss_bytes()` twice in the same logging statement (once for bytes and once for megabytes) performs redundant process state checks.
**Action:** Fetch the RSS value once per logging event and reuse it for both metrics.
