import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import sys
import os

# Add src to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from transfer import TransferService, TransferOutcome
from utils import AppConfig, ProgressState

async def benchmark_batching():
    print("\n--- Benchmarking State Persistence Batching ---")

    # Setup mocks
    config = AppConfig(
        api_id=123,
        api_hash="hash",
        channel_username="test_channel",
        r2_endpoint="https://r2.example.com",
        r2_bucket="test_bucket",
        r2_access_key="access",
        r2_secret_key="secret",
        progress_file=Path("data/state/progress.json")
    )

    tg_client = MagicMock()
    r2_client = AsyncMock()
    logger = MagicMock()

    service = TransferService(config, tg_client, r2_client, logger)
    service._next_commit_id = 1

    # Simulate 50 completed outcomes
    for i in range(1, 51):
        outcome = TransferOutcome(
            message_id=i,
            file_name=f"file_{i}.txt",
            key=f"key_{i}",
            size_bytes=100,
            status="uploaded"
        )
        service._completed_outcomes[i] = outcome

    service._highest_seen_id = 50

    # Initial call count
    initial_upload_calls = r2_client.upload_text_object.call_count

    # Run flush
    await service._flush_completed()

    # Final call count
    final_upload_calls = r2_client.upload_text_object.call_count
    calls_made = final_upload_calls - initial_upload_calls

    print(f"Messages processed: 50")
    print(f"R2 state persistence calls made: {calls_made}")

    if calls_made == 1:
        print("SUCCESS: State persistence is batched correctly (1 call for 50 messages).")
    else:
        print(f"FAILURE: Expected 1 call, but got {calls_made}.")

async def main():
    await benchmark_batching()

if __name__ == "__main__":
    asyncio.run(main())
