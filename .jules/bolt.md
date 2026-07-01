## 2025-05-15 - [Optimized RSS monitoring and filename sanitization]
**Learning:** Calling psutil.Process() repeatedly and compiling regex inside functions introduces measurable overhead. Consolidating identical function calls in logging blocks further reduces redundant system/library calls.
**Action:** Always cache expensive process handles and pre-compile regex patterns at the module level.
