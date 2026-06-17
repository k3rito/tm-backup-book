# Bolt's Journal - Critical Learnings

## 2025-05-15 - [Redundant R2 HEAD requests and Batched Persistence]
**Learning:** Found that `R2Client.upload_stream` was performing an `object_exists` check (HEAD request) that was already being performed by `TransferService`. Removing it saves one round-trip per upload. Also, batching progress state persistence in `TransferService` significantly reduces R2 write operations. Caching `psutil.Process()` improves performance of memory logging by avoiding redundant system calls and object instantiation.
**Action:** Always check if existence checks are duplicated between service layers and ensure I/O operations like state persistence are batched when processing in loops.
