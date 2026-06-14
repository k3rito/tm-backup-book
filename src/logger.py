from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in (
            "file_name",
            "size_bytes",
            "speed_bytes_per_sec",
            "status",
            "message_id",
            "key",
            "duration_seconds",
            "rss_mb",
            "rss_bytes",
            "progress_last_message_id",
            "queued_tasks",
        ):
            if hasattr(record, field):
                payload[field] = getattr(record, field)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


class PlainFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = f"{self.formatTime(record, self.datefmt)} | {record.levelname:<8} | {record.getMessage()}"
        extras: list[str] = []
        for field in ("file_name", "size_bytes", "speed_bytes_per_sec", "status", "message_id", "key"):
            if hasattr(record, field):
                extras.append(f"{field}={getattr(record, field)}")
        if extras:
            base = f"{base} | {' '.join(extras)}"
        if record.exc_info:
            base = f"{base}\n{self.formatException(record.exc_info)}"
        return base


def setup_logging(log_file: Path, level: int = logging.INFO) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(JsonFormatter())

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(PlainFormatter(datefmt="%Y-%m-%d %H:%M:%S"))

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return logging.getLogger("telegram-r2-backup")
