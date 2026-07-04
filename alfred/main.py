from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv

from alfred.brain.worker import run_worker_forever
from alfred.storage.db import init_db
from alfred.telegram.receiver import run_receiver_forever
from alfred.telegram.sender import run_sender_forever


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


async def run() -> None:
    init_db()
    await asyncio.gather(
        run_receiver_forever(
            poll_seconds=_float_env("ALFRED_RECEIVER_POLL_SECONDS", 1.0),
            long_poll_seconds=_int_env("ALFRED_TELEGRAM_LONG_POLL_SECONDS", 20),
        ),
        run_worker_forever(poll_seconds=_float_env("ALFRED_WORKER_POLL_SECONDS", 2.0)),
        run_sender_forever(poll_seconds=_float_env("ALFRED_SENDER_POLL_SECONDS", 2.0)),
    )


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("shutdown requested")


if __name__ == "__main__":
    main()
