import asyncio
import time
from dataclasses import dataclass
from unittest.mock import MagicMock, AsyncMock

# Mock necessary parts for TransferService
@dataclass
class ProgressState:
    last_message_id: int = 0

class MockTransferService:
    def __init__(self):
        self._next_commit_id = 1
        self._completed_outcomes = {}
        self._record_outcome = MagicMock()
        self._progress_state = ProgressState()
        self._seen_ids = set()
        self._highest_seen_id = 100
        self._persist_progress_state = AsyncMock()

    # Original unoptimized version (simulated)
    async def flush_completed_unoptimized(self, force: bool = False) -> None:
        advanced = False
        while True:
            if self._next_commit_id in self._completed_outcomes:
                outcome = self._completed_outcomes.pop(self._next_commit_id)
                self._record_outcome(outcome)
                advanced = True
                self._progress_state = ProgressState(last_message_id=outcome.message_id)
                await self._persist_progress_state()
                self._seen_ids.discard(self._next_commit_id)
                self._next_commit_id += 1
                continue
            if self._next_commit_id < self._highest_seen_id and self._next_commit_id not in self._seen_ids:
                self._next_commit_id += 1
                continue
            break
        if force and not advanced:
            await self._persist_progress_state()

    # Optimized version (simulated)
    async def flush_completed_optimized(self, force: bool = False) -> None:
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

@dataclass
class MockOutcome:
    message_id: int

async def run_benchmark():
    num_messages = 50
    outcomes = {i: MockOutcome(message_id=i) for i in range(1, num_messages + 1)}

    # Benchmark unoptimized
    service_unopt = MockTransferService()
    service_unopt._completed_outcomes = outcomes.copy()

    start = time.perf_counter()
    await service_unopt.flush_completed_unoptimized()
    end = time.perf_counter()
    unopt_duration = end - start
    unopt_calls = service_unopt._persist_progress_state.call_count
    print(f"Unoptimized: {unopt_duration:.6f}s, Persist calls: {unopt_calls}")

    # Benchmark optimized
    service_opt = MockTransferService()
    service_opt._completed_outcomes = outcomes.copy()

    start = time.perf_counter()
    await service_opt.flush_completed_optimized()
    end = time.perf_counter()
    opt_duration = end - start
    opt_calls = service_opt._persist_progress_state.call_count
    print(f"Optimized: {opt_duration:.6f}s, Persist calls: {opt_calls}")

    reduction = (unopt_calls - opt_calls) / unopt_calls * 100 if unopt_calls > 0 else 0
    print(f"Reduction in I/O calls: {reduction:.2f}%")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
