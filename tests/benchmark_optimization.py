import sys
import os
import time
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from utils import current_rss_bytes
from transfer import TransferService, TransferOutcome

async def benchmark_rss(iterations=10000):
    print(f"Benchmarking current_rss_bytes with {iterations} iterations...")
    start = time.perf_counter()
    for _ in range(iterations):
        current_rss_bytes()
    end = time.perf_counter()
    duration = end - start
    print(f"Total time: {duration:.4f}s")
    print(f"Average time: {duration/iterations*1e6:.2f}μs per call")
    return duration

async def benchmark_flush(iterations=100):
    print(f"\nBenchmarking TransferService._flush_completed with {iterations} iterations...")

    config = MagicMock()
    config.max_concurrent_uploads = 3
    config.channel_username = "test_channel"
    config.progress_file = "test_progress.json"

    tg_client = MagicMock()
    r2_client = MagicMock()
    logger = MagicMock()

    service = TransferService(config, tg_client, r2_client, logger)
    service._persist_progress_state = AsyncMock()

    # Simulate some completed outcomes
    # If we have 10 outcomes to flush
    for i in range(1, 11):
        service._completed_outcomes[i] = TransferOutcome(
            message_id=i, file_name=f"file_{i}.txt", key=f"key_{i}",
            size_bytes=100, status="uploaded"
        )

    service._next_commit_id = 1
    service._highest_seen_id = 10
    service._seen_ids = set(range(1, 11))

    start = time.perf_counter()
    await service._flush_completed()
    end = time.perf_counter()

    persist_calls = service._persist_progress_state.call_count
    print(f"Flush completed. Persist state calls: {persist_calls}")
    print(f"Flush duration: {end - start:.4f}s")
    return persist_calls

async def main():
    await benchmark_rss()
    await benchmark_flush()

if __name__ == "__main__":
    asyncio.run(main())
