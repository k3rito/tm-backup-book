from __future__ import annotations

import asyncio
from dataclasses import dataclass
from logging import Logger
from typing import Any, AsyncIterator

from telethon import TelegramClient
from telethon.errors import FloodWaitError, RPCError
from telethon.sessions import StringSession

from utils import AppConfig, MediaDescriptor, describe_message, normalize_channel_ref


@dataclass(frozen=True)
class TelegramClientState:
    channel_ref: str
    session_name: str


class TelegramSourceError(RuntimeError):
    pass


class TelegramSourceClient:
    def __init__(self, config: AppConfig, logger: Logger) -> None:
        self._config = config
        self._logger = logger
        self._client: TelegramClient | None = None
        self._channel: Any = None
        self._state = TelegramClientState(
            channel_ref=normalize_channel_ref(config.channel_username),
            session_name=config.telegram_session_name,
        )

    async def connect(self) -> None:
        if self._client is not None:
            return

        session = self._build_session()
        client = TelegramClient(
            session,
            self._config.api_id,
            self._config.api_hash,
            flood_sleep_threshold=60,
            timeout=30,
            connection_retries=5,
            retry_delay=1,
            auto_reconnect=True,
        )

        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            raise TelegramSourceError(
                "TELEGRAM_SESSION_STRING is required and must contain an authorized Telegram StringSession."
            )

        try:
            self._channel = await client.get_entity(self._state.channel_ref)
        except (ValueError, RPCError) as exc:
            await client.disconnect()
            raise TelegramSourceError(f"Unable to resolve Telegram channel: {self._state.channel_ref}") from exc

        self._client = client

    async def close(self) -> None:
        client = self._client
        if client is None:
            return
        await client.disconnect()
        self._client = None
        self._channel = None

    async def iter_messages(self, min_message_id: int) -> AsyncIterator[Any]:
        self._require_connected()
        client = self._client
        channel = self._channel
        assert client is not None
        assert channel is not None

        while True:
            try:
                async for message in client.iter_messages(
                    channel,
                    min_id=min_message_id,
                    reverse=True,
                    wait_time=0,
                ):
                    yield message
                return
            except FloodWaitError as exc:
                self._logger.warning(
                    "telegram flood wait",
                    extra={"status": "flood_wait", "speed_bytes_per_sec": 0, "size_bytes": 0},
                )
                await asyncio.sleep(exc.seconds + 1)
            except RPCError as exc:
                raise TelegramSourceError("Telegram API request failed while iterating messages") from exc

    async def stream_media(self, message: Any) -> AsyncIterator[bytes]:
        self._require_connected()
        client = self._client
        assert client is not None
        if not getattr(message, "file", None):
            return

        while True:
            try:
                async for chunk in client.iter_download(
                    message,
                    request_size=self._config.telegram_request_size,
                ):
                    if chunk:
                        yield chunk
                return
            except FloodWaitError as exc:
                await asyncio.sleep(exc.seconds + 1)
            except RPCError as exc:
                raise TelegramSourceError(f"Telegram media stream failed for message {getattr(message, 'id', 'unknown')}") from exc

    def describe(self, message: Any) -> MediaDescriptor | None:
        return describe_message(message)

    def _build_session(self) -> str | StringSession:
        if not self._config.telegram_session_string:
            raise TelegramSourceError("TELEGRAM_SESSION_STRING is required")
        return StringSession(self._config.telegram_session_string)

    def _require_connected(self) -> None:
        if self._client is None or self._channel is None:
            raise TelegramSourceError("Telegram client is not connected")
