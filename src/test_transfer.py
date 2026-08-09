from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
import pytest

from transfer import TransferService, TransferOutcome
from utils import AppConfig


@pytest.fixture
def mock_config() -> AppConfig:
    return AppConfig(
        api_id=12345,
        api_hash="hash123",
        channel_username="testchannel",
        r2_endpoint="https://endpoint.com",
        r2_bucket="mybucket",
        r2_access_key="accesskey",
        r2_secret_key="secretkey",
        telegram_session_string="sessionstr",
    )


@pytest.fixture
def mock_telegram_client() -> MagicMock:
    client = MagicMock()
    client.connect = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_r2_client() -> MagicMock:
    client = MagicMock()
    client.connect = AsyncMock()
    client.close = AsyncMock()
    client.upload_text_object = AsyncMock()
    return client


@pytest.fixture
def mock_logger() -> MagicMock:
    return MagicMock()


@pytest.mark.asyncio
async def test_flush_completed_batches_persistence(
    mock_config, mock_telegram_client, mock_r2_client, mock_logger
):
    # Instantiate the service
    service = TransferService(
        config=mock_config,
        telegram_client=mock_telegram_client,
        r2_client=mock_r2_client,
        logger=mock_logger,
    )

    # Initialize next commit ID
    service._next_commit_id = 1
    # Mock _persist_progress_state to track how many times it was called
    service._persist_progress_state = AsyncMock()

    # Setup completed outcomes (sequential message IDs 1, 2, 3)
    outcome1 = TransferOutcome(message_id=1, file_name="f1", key="k1", size_bytes=100, status="uploaded")
    outcome2 = TransferOutcome(message_id=2, file_name="f2", key="k2", size_bytes=200, status="uploaded")
    outcome3 = TransferOutcome(message_id=3, file_name="f3", key="k3", size_bytes=300, status="uploaded")

    service._completed_outcomes = {
        1: outcome1,
        2: outcome2,
        3: outcome3,
    }
    service._highest_seen_id = 3
    service._seen_ids = {1, 2, 3}

    # Call _flush_completed
    await service._flush_completed()

    # Verify that the progress state advanced to the latest message ID
    assert service._progress_state.last_message_id == 3
    assert service._next_commit_id == 4
    assert len(service._completed_outcomes) == 0

    # Verify that _persist_progress_state was called exactly once (batched!)
    # Previously, it would have been called 3 times (once per outcome in the loop).
    service._persist_progress_state.assert_called_once()


@pytest.mark.asyncio
async def test_flush_completed_with_force_no_advance(
    mock_config, mock_telegram_client, mock_r2_client, mock_logger
):
    service = TransferService(
        config=mock_config,
        telegram_client=mock_telegram_client,
        r2_client=mock_r2_client,
        logger=mock_logger,
    )

    service._next_commit_id = 1
    service._persist_progress_state = AsyncMock()
    service._completed_outcomes = {}  # Empty

    # Call with force=True, advanced=False
    await service._flush_completed(force=True)

    # It should still call _persist_progress_state once because force is True
    service._persist_progress_state.assert_called_once()


@pytest.mark.asyncio
async def test_flush_completed_no_force_no_advance(
    mock_config, mock_telegram_client, mock_r2_client, mock_logger
):
    service = TransferService(
        config=mock_config,
        telegram_client=mock_telegram_client,
        r2_client=mock_r2_client,
        logger=mock_logger,
    )

    service._next_commit_id = 1
    service._persist_progress_state = AsyncMock()
    service._completed_outcomes = {}  # Empty

    # Call with force=False, advanced=False
    await service._flush_completed(force=False)

    # It should not call _persist_progress_state
    service._persist_progress_state.assert_not_called()


@pytest.mark.asyncio
async def test_flush_completed_handles_gaps(
    mock_config, mock_telegram_client, mock_r2_client, mock_logger
):
    service = TransferService(
        config=mock_config,
        telegram_client=mock_telegram_client,
        r2_client=mock_r2_client,
        logger=mock_logger,
    )

    service._next_commit_id = 1
    service._persist_progress_state = AsyncMock()

    # Outcome for message 1 is completed. Message 2 is a gap (not seen). Outcome for message 3 is completed.
    outcome1 = TransferOutcome(message_id=1, file_name="f1", key="k1", size_bytes=100, status="uploaded")
    outcome3 = TransferOutcome(message_id=3, file_name="f3", key="k3", size_bytes=300, status="uploaded")

    service._completed_outcomes = {
        1: outcome1,
        3: outcome3,
    }
    service._highest_seen_id = 3
    # 2 is a gap, so it's not in seen_ids
    service._seen_ids = {1, 3}

    # First call to _flush_completed should process 1, skip gap 2, and process 3.
    await service._flush_completed()

    assert service._progress_state.last_message_id == 3
    assert service._next_commit_id == 4
    assert len(service._completed_outcomes) == 0
    service._persist_progress_state.assert_called_once()
