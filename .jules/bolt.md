## 2025-05-18 - Deferring file extension and MIME type parsing in classify_media
**Learning:** Parsing `Path(file_name).suffix` and MIME lowercasing upfront in `classify_media` incurred unnecessary `Path` object creation and string lowercasing overhead for common photo/video/audio messages before checking boolean message attributes.
**Action:** Order cheap boolean attribute checks (`photo`, `video`, `audio`) before string parsing and `os.path` operations, and use `os.path.splitext` instead of instantiating `pathlib.Path`.
