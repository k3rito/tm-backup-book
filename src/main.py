from __future__ import annotations

import asyncio
import logging
import signal
import sys

from logger import setup_logging
from r2_client import R2Client
from telegram_client import TelegramSourceClient
from transfer import TransferService, TransferServiceError
from utils import ensure_runtime_directories, load_config


async def main() -> None:
    config = load_config()
    ensure_runtime_directories(config)
    logger = setup_logging(config.log_file)

    logger.info(
        "configuration loaded",
        extra={
            "status": "ready",
            "progress_last_message_id": 0,
            "queued_tasks": 0,
        },
    )

    telegram_client = TelegramSourceClient(config, logger)
    r2_client = R2Client(config, logger)
    transfer_service = TransferService(config, telegram_client, r2_client, logger)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def request_shutdown() -> None:
        logger.warning("shutdown requested", extra={"status": "shutdown"})
        stop_event.set()

    for signal_name in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signal_name, request_shutdown)
        except NotImplementedError:
            signal.signal(signal_name, lambda *_: request_shutdown())

    transfer_task = asyncio.create_task(transfer_service.run())
    shutdown_task = asyncio.create_task(stop_event.wait())

    try:
        done, pending = await asyncio.wait({transfer_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED)

        if shutdown_task in done and not transfer_task.done():
            transfer_task.cancel()

        await transfer_task
    except KeyboardInterrupt:
        logger.warning("shutdown requested by user", extra={"status": "shutdown"})
    except asyncio.CancelledError:
        logger.warning("service cancelled", extra={"status": "cancelled"})
    except TransferServiceError:
        sys.exit(1)
    except Exception:
        logger.exception("unexpected failure", extra={"status": "failed"})
        sys.exit(1)
    finally:
        shutdown_task.cancel()
        await telegram_client.close()
        await r2_client.close()


if __name__ == "__main__":
    asyncio.run(main())
