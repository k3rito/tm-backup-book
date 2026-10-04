from __future__ import annotations

import sys
from pathlib import Path

# Ensure src is on pythonpath for running tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import unittest  # noqa: E402
from datetime import UTC, datetime  # noqa: E402

from utils import (  # noqa: E402
    MediaDescriptor,
    build_storage_key,
    classify_media,
    current_rss_bytes,
    describe_message,
    normalize_channel_ref,
    resolve_media_filename,
    sanitize_filename,
)


class DummyFileInfo:
    def __init__(self, name: str | None = None, mime_type: str | None = None, size: int = 100):
        self.name = name
        self.mime_type = mime_type
        self.size = size


class DummyMessage:
    def __init__(
        self,
        msg_id: int = 42,
        photo: bool = False,
        video: bool = False,
        audio: bool = False,
        sticker: bool = False,
        name: str | None = None,
        mime_type: str | None = None,
        msg_date: datetime | None = None,
    ):
        self.id = msg_id
        self.sticker = True if sticker else None
        self.file = DummyFileInfo(name=name, mime_type=mime_type)
        self.photo = True if photo else None
        self.video = True if video else None
        self.video_note = None
        self.audio = True if audio else None
        self.voice = None
        self.date = msg_date or datetime(2025, 5, 20, 12, 0, 0, tzinfo=UTC)


class TestUtils(unittest.TestCase):
    def test_normalize_channel_ref(self) -> None:
        self.assertEqual(normalize_channel_ref("https://t.me/my_channel"), "my_channel")
        self.assertEqual(normalize_channel_ref("@my_channel"), "my_channel")
        self.assertEqual(normalize_channel_ref("my_channel"), "my_channel")

    def test_sanitize_filename(self) -> None:
        self.assertEqual(sanitize_filename("photo @ 123.jpg"), "photo_123.jpg")
        self.assertEqual(sanitize_filename("path/to/file.png"), "file.png")
        self.assertEqual(sanitize_filename("a" * 200 + ".txt"), "a" * 176 + ".txt")

    def test_classify_media(self) -> None:
        photo_msg = DummyMessage(photo=True, name="photo.jpg")
        self.assertEqual(classify_media(photo_msg), "photo")

        video_msg = DummyMessage(video=True, name="video.mp4")
        self.assertEqual(classify_media(video_msg), "video")

        audio_msg = DummyMessage(audio=True, name="audio.mp3")
        self.assertEqual(classify_media(audio_msg), "audio")

        archive_msg = DummyMessage(name="data.tar.gz")
        self.assertEqual(classify_media(archive_msg), "archive")

        doc_msg = DummyMessage(name="document.pdf", mime_type="application/pdf")
        self.assertEqual(classify_media(doc_msg), "document")

        sticker_msg = DummyMessage(sticker=True)
        self.assertIsNone(classify_media(sticker_msg))

    def test_resolve_media_filename(self) -> None:
        msg = DummyMessage(msg_id=10, name="custom_name.png")
        self.assertEqual(resolve_media_filename(msg, "photo"), "custom_name.png")

        msg_unnamed = DummyMessage(msg_id=15, name=None, mime_type="image/jpeg")
        self.assertEqual(resolve_media_filename(msg_unnamed, "photo"), "photo_15.jpg")

    def test_describe_message(self) -> None:
        msg = DummyMessage(msg_id=99, photo=True, name="image.jpg")
        desc = describe_message(msg)
        self.assertIsNotNone(desc)
        assert desc is not None
        self.assertEqual(desc.message_id, 99)
        self.assertEqual(desc.kind, "photo")
        self.assertEqual(desc.file_name, "image.jpg")

    def test_build_storage_key(self) -> None:
        dt = datetime(2025, 3, 15, 10, 30, tzinfo=UTC)
        desc = MediaDescriptor(
            message_id=456,
            kind="photo",
            file_name="snapshot.jpg",
            size_bytes=1000,
            content_type="image/jpeg",
            message_date=dt,
        )
        key = build_storage_key("https://t.me/test_chan", desc)
        self.assertEqual(key, "test_chan/2025/03/15/456_snapshot.jpg")

    def test_current_rss_bytes(self) -> None:
        rss = current_rss_bytes()
        self.assertIsInstance(rss, int)
        self.assertGreaterEqual(rss, 0)


if __name__ == "__main__":
    unittest.main()
