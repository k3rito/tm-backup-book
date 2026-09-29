from datetime import UTC, datetime
from types import SimpleNamespace
from utils import (
    classify_media,
    current_rss_bytes,
    describe_message,
    sanitize_filename,
)


def test_sanitize_filename():
    assert sanitize_filename("hello world!.mp4") == "hello_world_.mp4"
    assert sanitize_filename("a/b/c/file.txt") == "file.txt"
    assert sanitize_filename("") == "file"


def test_classify_media():
    msg = SimpleNamespace(
        file=SimpleNamespace(name="video.mp4", mime_type="video/mp4", size=100),
        video=True,
    )
    assert classify_media(msg) == "video"


def test_describe_message():
    msg = SimpleNamespace(
        id=42,
        file=SimpleNamespace(name="photo.jpg", mime_type="image/jpeg", size=200),
        photo=True,
        date=datetime.now(tz=UTC),
    )
    desc = describe_message(msg)
    assert desc is not None
    assert desc.message_id == 42
    assert desc.kind == "photo"
    assert desc.file_name == "photo.jpg"


def test_current_rss_bytes():
    rss = current_rss_bytes()
    assert isinstance(rss, int)
    assert rss >= 0
