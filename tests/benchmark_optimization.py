import time
import asyncio
import os
import sys
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

import utils

def benchmark_rss_original():
    # Simulate original current_rss_bytes
    def original_rss():
        try:
            import psutil
            process = psutil.Process()
            return int(process.memory_info().rss)
        except Exception:
            return 0

    start = time.perf_counter()
    for _ in range(1000):
        original_rss()
    end = time.perf_counter()
    print(f"Original rss_bytes (1000 calls): {end - start:.4f}s")

def benchmark_rss_optimized():
    import psutil
    _PROCESS = psutil.Process()
    def optimized_rss():
        try:
            return int(_PROCESS.memory_info().rss)
        except Exception:
            return 0

    start = time.perf_counter()
    for _ in range(1000):
        optimized_rss()
    end = time.perf_counter()
    print(f"Optimized rss_bytes (1000 calls): {end - start:.4f}s")

async def benchmark_persistence():
    # Mocking a few things to measure the impact of batching
    class MockR2Client:
        async def upload_text_object(self, **kwargs):
            # Simulate network latency
            await asyncio.sleep(0.01)

    async def save_progress_mock(path, state):
        # Simulate disk I/O
        await asyncio.sleep(0.001)

    # Per-message persistence (simulated)
    start = time.perf_counter()
    for i in range(50):
        # save_progress
        await asyncio.sleep(0.001)
        # r2 upload
        await asyncio.sleep(0.01)
    end = time.perf_counter()
    print(f"Per-message persistence (50 messages): {end - start:.4f}s")

    # Batched persistence (simulated)
    start = time.perf_counter()
    for i in range(50):
        pass # just process
    # save_progress once
    await asyncio.sleep(0.001)
    # r2 upload once
    await asyncio.sleep(0.01)
    end = time.perf_counter()
    print(f"Batched persistence (50 messages): {end - start:.4f}s")

if __name__ == "__main__":
    benchmark_rss_original()
    benchmark_rss_optimized()
    asyncio.run(benchmark_persistence())
