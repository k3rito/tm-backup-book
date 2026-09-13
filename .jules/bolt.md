# Bolt's Journal - Critical Learnings

## 2025-05-15 - Optimizing file extension extraction in high-frequency message scanning
**Learning:** Instantiating `pathlib.Path(file_name)` to retrieve file extensions in high-frequency message scanning introduces significant overhead compared to standard library string manipulation with `os.path.splitext(file_name)[1]`.
**Action:** Prefer `os.path.splitext` over `Path().suffix` when processing high-volume data streams/loops in Python.
