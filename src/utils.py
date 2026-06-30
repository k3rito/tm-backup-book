from __future__ import annotations

import json
import mimetypes
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from aiofiles import open as aio_open
from dotenv import load_dotenv

# Pre-compile regex for performance
_RE_INVALID = re.compile(r"[^A-Za-z0-9._-]+")
_RE_REPEATED_UNDERSCORE = re.compile(r"_+")

# Cache psutil.Process() to avoid redundant instantiation
_PROCESS = None
try:
    import psutil  # type: ignore
    _PROCESS = psutil.Process()
except (ImportError, Exception):
    _PROCESS = None

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
STATE_DIR = DATA_DIR / "state"
LOGS_DIR = BASE_DIR / "logs"
PROGRESS_FILE = STATE_DIR / "progress.json"
APP_LOG_FILE = LOGS_DIR / "app.log"
R2_PROGRESS_KEY = "state/progress.json"
DEFAULT_CHUNK_SIZE = 8 * 1024 * 1024
TELEGRAM_REQUEST_SIZE = 512 * 1024
SUPPORTED_ARCHIVE_EXTENSIONS = {
    ".7z",
    ".bz2",
    ".gz",
    ".rar",
    ".tar",
    ".tgz",
    ".xz",
    ".zip",
}
SUPPORTED_ARCHIVE_MIME_TYPES = {
    "application/gzip",
    "application/java-archive",
    "application/octet-stream",
    "application/rar",
    "application/x-7z-compressed",
    "application/x-bzip2",
    "application/x-compressed",
    "application/x-tar",
    "application/x-xz",
    "application/zip",
}


@dataclass(frozen=True)
class AppConfig:
    api_id: int
    api_hash: str
    channel_username: str
    r2_endpoint: str
    r2_bucket: str
    r2_access_key: str
    r2_secret_key: str
    max_concurrent_uploads: int = 3
    telegram_session_name: str = "telegram_r2_backup"
    telegram_session_string: str | None = None
    chunk_size: int = DEFAULT_CHUNK_SIZE
    telegram_request_size: int = TELEGRAM_REQUEST_SIZE
    data_dir: Path = DATA_DIR
    sessions_dir: Path = SESSIONS_DIR
    state_dir: Path = STATE_DIR
    logs_dir: Path = LOGS_DIR
    progress_file: Path = PROGRESS_FILE
    log_file: Path = APP_LOG_FILE


@dataclass(frozen=True)
class ProgressState:
    last_message_id: int = 0


@dataclass(frozen=True)
class MediaDescriptor:
    message_id: int
    kind: str
    file_name: str
    size_bytes: int
    content_type: str
    message_date: datetime


@dataclass(frozen=True)
class HealthSnapshot:
    status: str
    uptime_seconds: float
    rss_bytes: int
    rss_mb: float
    progress_last_message_id: int
    queued_tasks: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


def load_config() -> AppConfig:
    load_dotenv(BASE_DIR / ".env", override=False)

    api_id = _read_int_env("API_ID", required=True)
    api_hash = _read_str_env("API_HASH", required=True)
    channel_username = normalize_channel_ref(_read_str_env("CHANNEL_USERNAME", required=True))
    r2_endpoint = _read_str_env("R2_ENDPOINT", required=True)
    r2_bucket = _read_str_env("R2_BUCKET", required=True)
    r2_access_key = _read_str_env("R2_ACCESS_KEY", required=True)
    r2_secret_key = _read_str_env("R2_SECRET_KEY", required=True)
    max_concurrent_uploads = _read_int_env("MAX_CONCURRENT_UPLOADS", default=3)
    telegram_session_name = _read_str_env("TELEGRAM_SESSION_NAME", default="telegram_r2_backup")
    telegram_session_string = _read_str_env("TELEGRAM_SESSION_STRING", required=True)

    return AppConfig(
        api_id=api_id,
        api_hash=api_hash,
        channel_username=channel_username,
        r2_endpoint=r2_endpoint,
        r2_bucket=r2_bucket,
        r2_access_key=r2_access_key,
        r2_secret_key=r2_secret_key,
        max_concurrent_uploads=max(1, max_concurrent_uploads),
        telegram_session_name=telegram_session_name,
        telegram_session_string=telegram_session_string,
    )


def ensure_runtime_directories(config: AppConfig) -> None:
    for path in (config.data_dir, config.sessions_dir, config.state_dir, config.logs_dir):
        path.mkdir(parents=True, exist_ok=True)


def normalize_channel_ref(value: str) -> str:
    value = value.strip()
    if value.startswith("https://t.me/") or value.startswith("http://t.me/"):
        parsed = urlparse(value)
        path = parsed.path.rstrip("/")
        if path:
            value = path.split("/")[-1]
    return value.lstrip("@").strip()


def sanitize_filename(value: str, fallback: str = "file") -> str:
    value = value.strip().replace("\\", "/")
    if "/" in value:
        value = value.split("/")[-1]
    # Use pre-compiled regex for ~1.3x speedup
    value = _RE_INVALID.sub("_", value)
    value = _RE_REPEATED_UNDERSCORE.sub("_", value).strip("._-")
    if not value:
        value = fallback
    if len(value) > 180:
        stem, suffix = os.path.splitext(value)
        allowed = max(1, 180 - len(suffix))
        value = stem[:allowed].rstrip("._-") + suffix
    return value


def _guess_extension(content_type: str | None) -> str:
    if not content_type:
        return ""
    extension = mimetypes.guess_extension(content_type, strict=False)
    return extension or ""


def classify_media(message: Any) -> str | None:
    if getattr(message, "sticker", None):
        return None

    file_info = getattr(message, "file", None)
    if file_info is None:
        return None

    file_name = getattr(file_info, "name", None) or ""
    content_type = (getattr(file_info, "mime_type", None) or "").lower()
    extension = Path(file_name).suffix.lower()

    if getattr(message, "photo", None):
        return "photo"
    if getattr(message, "video", None) or getattr(message, "video_note", None):
        return "video"
    if getattr(message, "audio", None) or getattr(message, "voice", None):
        return "audio"

    if extension in SUPPORTED_ARCHIVE_EXTENSIONS or content_type in SUPPORTED_ARCHIVE_MIME_TYPES:
        return "archive"

    return "document"


def is_supported_media(message: Any) -> bool:
    return classify_media(message) is not None


def resolve_media_filename(message: Any, kind: str) -> str:
    file_info = getattr(message, "file", None)
    original_name = sanitize_filename(getattr(file_info, "name", None) or "", fallback="") if file_info else ""
    content_type = (getattr(file_info, "mime_type", None) or "").lower() if file_info else ""
    message_id = getattr(message, "id", 0) or 0

    if original_name:
        return original_name

    if kind == "photo":
        extension = _guess_extension(content_type) or ".jpg"
        return sanitize_filename(f"photo_{message_id}{extension}", fallback=f"photo_{message_id}{extension}")

    if kind == "video":
        extension = _guess_extension(content_type) or ".mp4"
        return sanitize_filename(f"video_{message_id}{extension}", fallback=f"video_{message_id}{extension}")

    if kind == "audio":
        extension = _guess_extension(content_type) or ".mp3"
        return sanitize_filename(f"audio_{message_id}{extension}", fallback=f"audio_{message_id}{extension}")

    if kind == "archive":
        extension = _guess_extension(content_type) or ".zip"
        return sanitize_filename(f"archive_{message_id}{extension}", fallback=f"archive_{message_id}{extension}")

    extension = _guess_extension(content_type) or ".bin"
    return sanitize_filename(f"document_{message_id}{extension}", fallback=f"document_{message_id}{extension}")


def describe_message(message: Any) -> MediaDescriptor | None:
    kind = classify_media(message)
    if kind is None:
        return None

    file_info = getattr(message, "file", None)
    size_bytes = int(getattr(file_info, "size", 0) or 0)
    content_type = (getattr(file_info, "mime_type", None) or "application/octet-stream").lower()
    file_name = resolve_media_filename(message, kind)
    message_date = getattr(message, "date", None) or datetime.now(tz=UTC)
    if message_date.tzinfo is None:
        message_date = message_date.replace(tzinfo=UTC)

    return MediaDescriptor(
        message_id=int(getattr(message, "id", 0) or 0),
        kind=kind,
        file_name=file_name,
        size_bytes=size_bytes,
        content_type=content_type,
        message_date=message_date,
    )


def build_storage_key(channel_username: str, descriptor: MediaDescriptor) -> str:
    safe_channel = sanitize_filename(normalize_channel_ref(channel_username), fallback="channel")
    date_path = descriptor.message_date.astimezone(UTC).strftime("%Y/%m/%d")
    return f"{safe_channel}/{date_path}/{descriptor.message_id}_{descriptor.file_name}"


def progress_state_to_json(state: ProgressState) -> str:
    return json.dumps(asdict(state), ensure_ascii=False, indent=2) + "\n"


def progress_state_from_json(raw: str) -> ProgressState:
    payload = json.loads(raw)
    return ProgressState(last_message_id=int(payload.get("last_message_id", 0) or 0))


async def load_progress(path: Path) -> ProgressState:
    if not path.exists():
        return ProgressState()

    try:
        async with aio_open(path, "r", encoding="utf-8") as handle:
            raw = await handle.read()
        return progress_state_from_json(raw)
    except Exception:
        return ProgressState()


async def save_progress(path: Path, state: ProgressState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = progress_state_to_json(state)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    async with aio_open(temp_path, "w", encoding="utf-8") as handle:
        await handle.write(payload)
        await handle.flush()
    os.replace(temp_path, path)


async def ensure_progress_file(path: Path) -> None:
    if path.exists():
        return
    await save_progress(path, ProgressState())


def format_bytes(value: int | float) -> str:
    if value < 0:
        value = 0
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    unit = units[0]
    for candidate in units:
        unit = candidate
        if size < 1024.0 or candidate == units[-1]:
            break
        size /= 1024.0
    if unit == "B":
        return f"{int(size)} {unit}"
    return f"{size:.2f} {unit}"


def format_speed(bytes_per_second: float) -> str:
    if bytes_per_second <= 0:
        return "0 B/s"
    return f"{format_bytes(bytes_per_second)}/s"


def current_rss_bytes() -> int:
    """Returns the current RSS (Resident Set Size) in bytes, cached for performance."""
    if _PROCESS is None:
        return 0
    try:
        return int(_PROCESS.memory_info().rss)
    except Exception:
        return 0


def health_snapshot(
    *,
    start_time: datetime,
    progress_last_message_id: int,
    queued_tasks: int = 0,
    extra: dict[str, Any] | None = None,
) -> HealthSnapshot:
    now = datetime.now(tz=UTC)
    uptime = max(0.0, (now - start_time).total_seconds())
    rss = current_rss_bytes()
    return HealthSnapshot(
        status="healthy",
        uptime_seconds=uptime,
        rss_bytes=rss,
        rss_mb=round(rss / (1024 * 1024), 2),
        progress_last_message_id=progress_last_message_id,
        queued_tasks=queued_tasks,
        extra=extra or {},
    )


def _read_str_env(name: str, *, required: bool = False, default: str = "") -> str:
    value = os.getenv(name, default).strip()
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _read_int_env(name: str, *, required: bool = False, default: int = 0) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        if required:
            raise RuntimeError(f"Missing required environment variable: {name}")
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer") from exc
