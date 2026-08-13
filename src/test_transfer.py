import pytest
from unittest.mock import AsyncMock, MagicMock
from transfer import TransferService, TransferOutcome
from utils import AppConfig


@pytest.mark.asyncio
async def test_flush_completed_batches_persist():
    # Setup mock clients and config
    config = MagicMock(spec=AppConfig)
    config.progress_file = "dummy_path"
    config.max_concurrent_uploads = 3
    telegram_client = MagicMock()
    r2_client = MagicMock()

    # Mock _persist_progress_state to trace calls
    service = TransferService(config, telegram_client, r2_client, MagicMock())
    service._persist_progress_state = AsyncMock()

    # Populate mock completed outcomes to flush
    service._next_commit_id = 1
    service._highest_seen_id = 5
    service._seen_ids = {1, 2, 3, 4, 5}
    service._completed_outcomes = {
        1: TransferOutcome(1, "file1", "key1", 100, "uploaded"),
        2: TransferOutcome(2, "file2", "key2", 100, "uploaded"),
        3: TransferOutcome(3, "file3", "key3", 100, "uploaded"),
    }

    # Run the flush
    await service._flush_completed()

    # Assert _persist_progress_state is called exactly once despite flushing 3 items (O(1) complexity)
    assert service._persist_progress_state.call_count == 1
    assert service._progress_state.last_message_id == 3
