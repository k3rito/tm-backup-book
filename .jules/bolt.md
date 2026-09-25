# Bolt's Journal - Critical Learnings

## 2026-09-25 - Fast-pathing boolean media attributes over string parsing
**Learning:** Instantiating `pathlib.Path` and performing `.lower()` on MIME types or file names before checking basic object boolean attributes (like `message.photo` or `message.video`) introduces unnecessary CPU overhead when scanning large message feeds. Checking cheap boolean flags first yields an ~18.78x speedup for photos.
**Action:** Always place lightweight attribute checks before string manipulations, regular expressions, or module instantiations in hot loops or high-frequency classifier functions.
