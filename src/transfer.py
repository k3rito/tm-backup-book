from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from logging import Logger
from typing import Any

from r2_client import R2Client, UploadResult
from telegram_client import TelegramSourceClient
from utils import (
    AppConfig,
    ProgressState,
    R2_PROGRESS_KEY,
    build_storage_key,
    current_rss_bytes,
    ensure_progress_file,
    health_snapshot,
    progress_state_from_json,
    progress_state_to_json,
    save_progress,
)


@dataclass
class TransferMetrics:
    scanned_messages: int = 0
    supported_messages: int = 0
    uploaded_messages: int = 0
    skipped_existing: int = 0
    skipped_unsupported: int = 0
    failed_messages: int = 0
    bytes_uploaded: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    def summary(self) -> dict[str, Any]:
        elapsed = max((datetime.now(tz=UTC) - self.started_at).total_seconds(), 1e-6)
        return {
            "scanned_messages": self.scanned_messages,
            "supported_messages": self.supported_messages,
            "uploaded_messages": self.uploaded_messages,
            "skipped_existing": self.skipped_existing,
            "skipped_unsupported": self.skipped_unsupported,
            "failed_messages": self.failed_messages,
            "bytes_uploaded": self.bytes_uploaded,
            "elapsed_seconds": elapsed,
            "throughput_bytes_per_sec": self.bytes_uploaded / elapsed if self.bytes_uploaded else 0.0,
        }


@dataclass(frozen=True)
class TransferOutcome:
    message_id: int
    file_name: str | None
    key: str | None
    size_bytes: int
    status: str
    duration_seconds: float = 0.0
    bytes_per_second: float = 0.0


class TransferServiceError(RuntimeError):
    pass


class TransferService:
    def __init__(
        self,
        config: AppConfig,
        telegram_client: TelegramSourceClient,
        r2_client: R2Client,
        logger: Logger,
    ) -> None:
        self._config = config
        self._telegram_client = telegram_client
        self._r2_client = r2_client
        self._logger = logger
        self._metrics = TransferMetrics()
        self._progress_state = ProgressState()
        self._next_commit_id = 1
        self._completed_outcomes: dict[int, TransferOutcome] = {}
        self._pending_tasks: dict[int, asyncio.Task[TransferOutcome]] = {}
        self._task_ids: dict[asyncio.Task[TransferOutcome], int] = {}
        self._failure: Exception | None = None
        self._highest_seen_id = 0
        self._seen_ids: set[int] = set()
        self._started_at = datetime.now(tz=UTC)

    async def run(self) -> None:
        await ensure_progress_file(self._config.progress_file)
        await self._r2_client.connect()
        await self._telegram_client.connect()
        self._progress_state = await self._load_progress_state()
        self._next_commit_id = self._progress_state.last_message_id + 1

        rss_bytes = current_rss_bytes()
        self._logger.info(
            "starting transfer",
            extra={
                "status": "started",
                "progress_last_message_id": self._progress_state.last_message_id,
                "queued_tasks": 0,
                "rss_bytes": rss_bytes,
                "rss_mb": round(rss_bytes / (1024 * 1024), 2),
            },
        )
        try:
            await self._run_pipeline()
            await self._flush_completed(force=True)
            await self._emit_summary()
        except asyncio.CancelledError:
            self._logger.warning("transfer cancelled", extra={"status": "cancelled"})
            raise
        except Exception as exc:
            await self._cancel_pending()
            self._logger.exception("transfer failed", extra={"status": "failed"})
            raise TransferServiceError(str(exc)) from exc
        finally:
            try:
                await asyncio.shield(self._persist_progress_state())
            except Exception:
                self._logger.exception("failed to persist progress state during shutdown", extra={"status": "state_sync_failed"})
            await self._r2_client.close()
            await self._telegram_client.close()

    async def _run_pipeline(self) -> None:
        scan_backoff = 1.0
        attempt = 1
        while self._failure is None:
            try:
                async for message in self._telegram_client.iter_messages(self._progress_state.last_message_id):
                    if self._failure is not None:
                        break
                    message_id = int(getattr(message, "id", 0) or 0)
                    self._metrics.scanned_messages += 1
                    self._highest_seen_id = max(self._highest_seen_id, message_id)
                    self._seen_ids.add(message_id)
                    task = asyncio.create_task(self._process_message_with_retry(message))
                    self._pending_tasks[message_id] = task
                    self._task_ids[task] = message_id
                    if len(self._pending_tasks) >= self._config.max_concurrent_uploads:
                        await self._wait_for_any()
                        await self._flush_completed()
                        if self._failure is not None:
                            break
                break
            except Exception:
                if attempt >= 5:
                    raise
                rss_bytes = current_rss_bytes()
                self._logger.warning(
                    "telegram scan retry",
                    extra={
                        "status": "retrying",
                        "message_id": self._progress_state.last_message_id,
                        "rss_bytes": rss_bytes,
                        "rss_mb": round(rss_bytes / (1024 * 1024), 2),
                    },
                )
                await asyncio.sleep(scan_backoff)
                scan_backoff = min(scan_backoff * 2, 30.0)
                attempt += 1

        while self._pending_tasks and self._failure is None:
            await self._wait_for_any()
            await self._flush_completed()

        if self._failure is not None:
            await self._flush_completed()
            await self._cancel_pending()
            raise self._failure

    async def _wait_for_any(self) -> None:
        if not self._pending_tasks:
            return

        done, _ = await asyncio.wait(set(self._pending_tasks.values()), return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            message_id = self._task_ids.pop(task, None)
            if message_id is None:
                continue
            self._pending_tasks.pop(message_id, None)
            try:
                outcome = task.result()
            except Exception as exc:
                self._metrics.failed_messages += 1
                self._failure = exc
                rss_bytes = current_rss_bytes()
                self._logger.exception(
                    "message processing failed",
                    extra={
                        "status": "failed",
                        "message_id": message_id,
                        "rss_bytes": rss_bytes,
                        "rss_mb": round(rss_bytes / (1024 * 1024), 2),
                    },
                )
            else:
                self._completed_outcomes[outcome.message_id] = outcome

    async def _process_message_with_retry(self, message: Any) -> TransferOutcome:
        backoff = 1.0
        for attempt in range(1, 6):
            try:
                return await self._process_message(message)
            except Exception:
                if attempt == 5:
                    raise
                rss_bytes = current_rss_bytes()
                self._logger.warning(
                    "message retry",
                    extra={
                        "status": "retrying",
                        "message_id": int(getattr(message, "id", 0) or 0),
                        "rss_bytes": rss_bytes,
                        "rss_mb": round(rss_bytes / (1024 * 1024), 2),
                    },
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30.0)

    async def _process_message(self, message: Any) -> TransferOutcome:
        descriptor = self._telegram_client.describe(message)
        message_id = int(getattr(message, "id", 0) or 0)

        if descriptor is None:
            self._metrics.skipped_unsupported += 1
            return TransferOutcome(
                message_id=message_id,
                file_name=None,
                key=None,
                size_bytes=0,
                status="skipped_unsupported",
            )

        self._metrics.supported_messages += 1
        storage_key = build_storage_key(self._config.channel_username, descriptor)

        if await self._r2_client.object_exists(storage_key):
            return TransferOutcome(
                message_id=message_id,
                file_name=descriptor.file_name,
                key=storage_key,
                size_bytes=descriptor.size_bytes,
                status="skipped_existing",
            )

        content_disposition = f'attachment; filename="{descriptor.file_name}"'
        started_at = time.perf_counter()
        upload_result: UploadResult = await self._r2_client.upload_stream(
            key=storage_key,
            stream=self._telegram_client.stream_media(message),
            size_bytes=descriptor.size_bytes,
            content_type=descriptor.content_type,
            content_disposition=content_disposition,
            metadata={
                "telegram-message-id": str(message_id),
                "telegram-channel": self._config.channel_username,
                "telegram-kind": descriptor.kind,
                "telegram-filename": descriptor.file_name,
            },
            chunk_size=self._config.chunk_size,
        )
        duration_seconds = max(time.perf_counter() - started_at, 1e-6)

        return TransferOutcome(
            message_id=message_id,
            file_name=descriptor.file_name,
            key=storage_key,
            size_bytes=upload_result.size_bytes,
            status="uploaded",
            duration_seconds=duration_seconds,
            bytes_per_second=upload_result.bytes_per_second,
        )

    async def _flush_completed(self, force: bool = False) -> None:
        advanced = False
        while True:
            if self._next_commit_id in self._completed_outcomes:
                outcome = self._completed_outcomes.pop(self._next_commit_id)
                self._record_outcome(outcome)
                advanced = True
                self._progress_state = ProgressState(last_message_id=outcome.message_id)
                self._seen_ids.discard(self._next_commit_id)
                self._next_commit_id += 1
                continue

            if self._next_commit_id < self._highest_seen_id and self._next_commit_id not in self._seen_ids:
                self._next_commit_id += 1
                continue

            break

        if advanced or force:
            await self._persist_progress_state()

    async def _load_progress_state(self) -> ProgressState:
        remote_payload = await self._r2_client.download_text_object(R2_PROGRESS_KEY)
        if remote_payload:
            state = progress_state_from_json(remote_payload)
            await save_progress(self._config.progress_file, state)
            return state

        return ProgressState()

    async def _persist_progress_state(self) -> None:
        await save_progress(self._config.progress_file, self._progress_state)
        await self._r2_client.upload_text_object(
            key=R2_PROGRESS_KEY,
            body=progress_state_to_json(self._progress_state),
            content_type="application/json",
        )

    def _record_outcome(self, outcome: TransferOutcome) -> None:
        if outcome.status == "uploaded":
            self._metrics.uploaded_messages += 1
            self._metrics.bytes_uploaded += outcome.size_bytes
        elif outcome.status == "skipped_existing":
            self._metrics.skipped_existing += 1
        elif outcome.status == "skipped_unsupported":
            self._metrics.skipped_unsupported += 1

        rss_bytes = current_rss_bytes()
        self._logger.info(
            "message processed",
            extra={
                "status": outcome.status,
                "message_id": outcome.message_id,
                "file_name": outcome.file_name or "",
                "key": outcome.key or "",
                "size_bytes": outcome.size_bytes,
                "speed_bytes_per_sec": outcome.bytes_per_second,
                "duration_seconds": round(outcome.duration_seconds, 3),
                "rss_bytes": rss_bytes,
                "rss_mb": round(rss_bytes / (1024 * 1024), 2),
            },
        )

    async def _cancel_pending(self) -> None:
        if not self._pending_tasks:
            return
        for task in self._pending_tasks.values():
            task.cancel()
        await asyncio.gather(*self._pending_tasks.values(), return_exceptions=True)
        self._pending_tasks.clear()
        self._task_ids.clear()

    async def _emit_summary(self) -> None:
        snapshot = health_snapshot(
            start_time=self._started_at,
            progress_last_message_id=self._progress_state.last_message_id,
            queued_tasks=0,
            extra=self._metrics.summary(),
        )
        summary = self._metrics.summary()
        self._logger.info(
            "transfer summary",
            extra={
                "status": snapshot.status,
                "rss_bytes": snapshot.rss_bytes,
                "rss_mb": snapshot.rss_mb,
                "progress_last_message_id": snapshot.progress_last_message_id,
                "queued_tasks": snapshot.queued_tasks,
            },
        )
        rss_bytes = current_rss_bytes()
        self._logger.info(
            "transfer finished",
            extra={
                "status": "finished",
                "scanned_messages": summary["scanned_messages"],
                "supported_messages": summary["supported_messages"],
                "uploaded_messages": summary["uploaded_messages"],
                "skipped_existing": summary["skipped_existing"],
                "skipped_unsupported": summary["skipped_unsupported"],
                "failed_messages": summary["failed_messages"],
                "bytes_uploaded": summary["bytes_uploaded"],
                "throughput_bytes_per_sec": summary["throughput_bytes_per_sec"],
                "rss_bytes": rss_bytes,
                "rss_mb": round(rss_bytes / (1024 * 1024), 2),
            },
        )
