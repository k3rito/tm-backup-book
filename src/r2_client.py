from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from logging import Logger
from typing import Any, AsyncIterator

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError, ConnectionClosedError, EndpointConnectionError, ReadTimeoutError

from utils import AppConfig, format_speed


RETRYABLE_EXCEPTIONS = (EndpointConnectionError, ConnectionClosedError, ReadTimeoutError, asyncio.TimeoutError)


@dataclass(frozen=True)
class UploadResult:
    key: str
    size_bytes: int
    duration_seconds: float
    bytes_per_second: float
    content_type: str
    existed: bool = False


class R2UploadError(RuntimeError):
    pass


class R2Client:
    def __init__(self, config: AppConfig, logger: Logger) -> None:
        self._config = config
        self._logger = logger
        self._session = aioboto3.Session()
        self._client_cm = None
        self._client = None

    async def connect(self) -> None:
        if self._client is not None:
            return

        self._client_cm = self._session.client(
            "s3",
            endpoint_url=self._config.r2_endpoint,
            aws_access_key_id=self._config.r2_access_key,
            aws_secret_access_key=self._config.r2_secret_key,
            region_name="auto",
            config=Config(
                s3={"addressing_style": "path"},
                connect_timeout=30,
                read_timeout=120,
                retries={"max_attempts": 1},
            ),
        )
        self._client = await self._client_cm.__aenter__()

    async def close(self) -> None:
        if self._client_cm is None:
            return
        await self._client_cm.__aexit__(None, None, None)
        self._client_cm = None
        self._client = None

    async def object_exists(self, key: str) -> bool:
        self._require_connected()
        client = self._client
        assert client is not None

        try:
            await self._retry("head_object", lambda: client.head_object(Bucket=self._config.r2_bucket, Key=key))
            return True
        except ClientError as exc:
            if self._is_not_found(exc):
                return False
            raise R2UploadError(f"R2 head_object failed for key: {key}") from exc

    async def download_text_object(self, key: str) -> str | None:
        self._require_connected()
        client = self._client
        assert client is not None

        try:
            response = await self._retry("get_object", lambda: client.get_object(Bucket=self._config.r2_bucket, Key=key))
        except ClientError as exc:
            if self._is_not_found(exc):
                return None
            raise R2UploadError(f"R2 get_object failed for key: {key}") from exc

        body = response.get("Body")
        if body is None:
            return None

        raw_bytes = await body.read()
        return raw_bytes.decode("utf-8")

    async def upload_text_object(
        self,
        *,
        key: str,
        body: str,
        content_type: str = "application/json",
        metadata: dict[str, str] | None = None,
    ) -> None:
        self._require_connected()
        client = self._client
        assert client is not None

        await self._retry(
            "put_text_object",
            lambda: client.put_object(
                Bucket=self._config.r2_bucket,
                Key=key,
                Body=body.encode("utf-8"),
                ContentType=content_type,
                Metadata=metadata or {},
            ),
        )

    async def upload_stream(
        self,
        *,
        key: str,
        stream: AsyncIterator[bytes],
        size_bytes: int,
        content_type: str,
        content_disposition: str,
        metadata: dict[str, str],
        chunk_size: int,
    ) -> UploadResult:
        self._require_connected()
        client = self._client
        assert client is not None


        if size_bytes == 0:
            started_at = time.perf_counter()
            await self._retry(
                "put_object_empty",
                lambda: client.put_object(
                    Bucket=self._config.r2_bucket,
                    Key=key,
                    Body=b"",
                    ContentType=content_type,
                    ContentDisposition=content_disposition,
                    Metadata=metadata,
                ),
            )
            duration_seconds = max(time.perf_counter() - started_at, 1e-6)
            return UploadResult(
                key=key,
                size_bytes=0,
                duration_seconds=duration_seconds,
                bytes_per_second=0.0,
                content_type=content_type,
            )

        upload_id = await self._create_multipart_upload(
            key=key,
            content_type=content_type,
            content_disposition=content_disposition,
            metadata=metadata,
        )
        started_at = time.perf_counter()
        uploaded_bytes = 0
        buffer = bytearray()
        parts: list[dict[str, Any]] = []
        part_number = 1

        try:
            async for chunk in stream:
                if not chunk:
                    continue
                buffer.extend(chunk)
                uploaded_bytes += len(chunk)

                while len(buffer) >= chunk_size:
                    part = bytes(buffer[:chunk_size])
                    del buffer[:chunk_size]
                    etag = await self._upload_part(key=key, upload_id=upload_id, part_number=part_number, body=part)
                    parts.append({"ETag": etag, "PartNumber": part_number})
                    part_number += 1

            if buffer or not parts:
                part = bytes(buffer)
                etag = await self._upload_part(key=key, upload_id=upload_id, part_number=part_number, body=part)
                parts.append({"ETag": etag, "PartNumber": part_number})

            if size_bytes and uploaded_bytes != size_bytes:
                raise R2UploadError(
                    f"Integrity check failed for key {key}: expected {size_bytes} bytes, received {uploaded_bytes} bytes"
                )

            await self._complete_upload(key=key, upload_id=upload_id, parts=parts)
            duration_seconds = max(time.perf_counter() - started_at, 1e-6)
            bytes_per_second = uploaded_bytes / duration_seconds
            return UploadResult(
                key=key,
                size_bytes=uploaded_bytes,
                duration_seconds=duration_seconds,
                bytes_per_second=bytes_per_second,
                content_type=content_type,
            )
        except Exception as exc:
            await self._abort_upload(key=key, upload_id=upload_id)
            raise R2UploadError(f"Multipart upload failed for key: {key}") from exc

    async def _create_multipart_upload(
        self,
        *,
        key: str,
        content_type: str,
        content_disposition: str,
        metadata: dict[str, str],
    ) -> str:
        client = self._client
        assert client is not None
        response = await self._retry(
            "create_multipart_upload",
            lambda: client.create_multipart_upload(
                Bucket=self._config.r2_bucket,
                Key=key,
                ContentType=content_type,
                ContentDisposition=content_disposition,
                Metadata=metadata,
            ),
        )
        upload_id = response.get("UploadId")
        if not upload_id:
            raise R2UploadError(f"R2 did not return an upload id for key: {key}")
        return str(upload_id)

    async def _upload_part(self, *, key: str, upload_id: str, part_number: int, body: bytes) -> str:
        client = self._client
        assert client is not None
        response = await self._retry(
            f"upload_part:{part_number}",
            lambda: client.upload_part(
                Bucket=self._config.r2_bucket,
                Key=key,
                UploadId=upload_id,
                PartNumber=part_number,
                Body=body,
            ),
        )
        etag = response.get("ETag")
        if not etag:
            raise R2UploadError(f"R2 did not return an etag for part {part_number} of key: {key}")
        return str(etag).strip('"')

    async def _complete_upload(self, *, key: str, upload_id: str, parts: list[dict[str, Any]]) -> None:
        client = self._client
        assert client is not None
        await self._retry(
            "complete_multipart_upload",
            lambda: client.complete_multipart_upload(
                Bucket=self._config.r2_bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            ),
        )

    async def _abort_upload(self, *, key: str, upload_id: str) -> None:
        try:
            client = self._client
            if client is None:
                return
            await client.abort_multipart_upload(
                Bucket=self._config.r2_bucket,
                Key=key,
                UploadId=upload_id,
            )
        except Exception:
            self._logger.exception("failed to abort multipart upload", extra={"key": key, "status": "abort_failed"})

    async def _retry(self, operation: str, call, max_attempts: int = 5):
        delay = 1.0
        last_exc: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                return await call()
            except ClientError as exc:
                if self._is_not_found(exc):
                    raise
                if attempt == max_attempts:
                    raise R2UploadError(f"R2 operation failed: {operation}") from exc
                last_exc = exc
            except RETRYABLE_EXCEPTIONS as exc:
                if attempt == max_attempts:
                    raise R2UploadError(f"R2 operation failed: {operation}") from exc
                last_exc = exc

            await asyncio.sleep(delay + random.uniform(0, 0.25))
            delay = min(delay * 2, 30.0)

        if last_exc is not None:
            raise R2UploadError(f"R2 operation failed: {operation}") from last_exc
        raise R2UploadError(f"R2 operation failed: {operation}")

    @staticmethod
    def _is_not_found(exc: ClientError) -> bool:
        error_code = str(exc.response.get("Error", {}).get("Code", "")).lower()
        return error_code in {"404", "notfound", "nosuchkey", "noSuchKey".lower()}

    def _require_connected(self) -> None:
        if self._client is None:
            raise R2UploadError("R2 client is not connected")
