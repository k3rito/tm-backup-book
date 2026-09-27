import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from transfer import TransferOutcome, TransferService
from utils import AppConfig, ProgressState


class TestTransferFlush(unittest.IsolatedAsyncioTestCase):
    async def test_flush_completed_batches_persistence(self):
        config = MagicMock(spec=AppConfig)
        config.progress_file = Path("/tmp/dummy_progress.json")
        telegram_client = MagicMock()
        r2_client = MagicMock()
        logger = MagicMock()

        service = TransferService(config, telegram_client, r2_client, logger)
        service._persist_progress_state = AsyncMock()

        # Populate completed outcomes for messages 1, 2, 3
        service._completed_outcomes = {
            1: TransferOutcome(message_id=1, file_name="f1.txt", key="k1", size_bytes=100, status="uploaded"),
            2: TransferOutcome(message_id=2, file_name="f2.txt", key="k2", size_bytes=200, status="uploaded"),
            3: TransferOutcome(message_id=3, file_name="f3.txt", key="k3", size_bytes=300, status="uploaded"),
        }
        service._next_commit_id = 1
        service._highest_seen_id = 3

        await service._flush_completed()

        # _persist_progress_state should be called exactly ONCE despite flushing 3 outcomes
        self.assertEqual(service._persist_progress_state.call_count, 1)
        self.assertEqual(service._progress_state.last_message_id, 3)
        self.assertEqual(service._next_commit_id, 4)


if __name__ == "__main__":
    unittest.main()
