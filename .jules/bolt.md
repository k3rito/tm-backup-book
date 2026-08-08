# Bolt's Performance Journal

This journal records critical learnings regarding specific bottlenecks, failed optimizations, or surprising performance edge cases encountered during the development of the Telegram R2 Backup service.

## 2025-02-27 - Initial Setup
**Learning:** Found that R2 upload network operations can block the transfer loops if called excessively (e.g. inside loops).
**Action:** Always optimize loops doing remote network operations, batching state updates to avoid redundant requests.
