import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.abspath("src"))

from transfer import TransferOutcome, TransferService  # noqa: E402
from utils import (  # noqa: E402
    AppConfig,
    ProgressState,
    current_rss_bytes,
    progress_state_from_json,
    progress_state_to_json,
)


def test_current_rss_bytes():
    # Verify that current_rss_bytes returns a non-negative integer and doesn't crash
    rss = current_rss_bytes()
    assert isinstance(rss, int)
    assert rss >= 0


def test_progress_serialization():
    state = ProgressState(last_message_id=42)
    serialized = progress_state_to_json(state)
    deserialized = progress_state_from_json(serialized)
    assert deserialized.last_message_id == 42


@pytest.mark.asyncio
async def test_flush_completed():
    # Setup mocks
    config = MagicMock(spec=AppConfig)
    config.progress_file = "dummy_progress.json"
    config.channel_username = "dummy_channel"

    telegram_client = MagicMock()
    r2_client = MagicMock()
    # Mock persist method
    r2_client.upload_text_object = AsyncMock()

    logger = MagicMock()

    service = TransferService(config, telegram_client, r2_client, logger)
    service._progress_state = ProgressState(last_message_id=10)
    service._next_commit_id = 11
    service._highest_seen_id = 15
    service._seen_ids = {11, 12, 13, 14, 15}

    # Mock outcomes for sequential IDs
    service._completed_outcomes = {
        11: TransferOutcome(message_id=11, file_name="f1", key="k1", size_bytes=100, status="uploaded"),
        12: TransferOutcome(message_id=12, file_name="f2", key="k2", size_bytes=200, status="uploaded"),
    }

    # Mock _persist_progress_state as an AsyncMock
    service._persist_progress_state = AsyncMock()

    # Call _flush_completed
    await service._flush_completed()

    # Verify we advanced the commit ID and updated state to 12
    assert service._next_commit_id == 13
    assert service._progress_state.last_message_id == 12

    # Verify _persist_progress_state was called exactly once for the batch instead of twice
    assert service._persist_progress_state.await_count == 1
