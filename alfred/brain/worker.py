from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv

from alfred.brain.watson import watson_chat_reply
from alfred.storage.db import init_db
from alfred.storage.queues import (
    get_pending_inbox,
    mark_inbox_failed,
    mark_inbox_processed,
    queue_outbox,
)

log = logging.getLogger(__name__)


def _shorten(text: str, *, max_chars: int = 3500) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


async def run_worker_once(*, limit: int = 20) -> int:
    init_db()
    messages = get_pending_inbox(limit=limit)
    if not messages:
        log.info("worker inbox empty")
        return 0

    processed = 0
    for message in messages:
        if message.chat_id is None:
            mark_inbox_failed(message.id, "Missing chat_id")
            continue

        try:
            reply = await watson_chat_reply(message.text)
            queue_outbox(chat_id=int(message.chat_id), text=_shorten(reply))
            mark_inbox_processed(message.id)
            processed += 1
        except Exception as exc:
            mark_inbox_failed(message.id, str(exc))
            log.exception("worker failed inbox_id=%s update_id=%s", message.id, message.update_id)

    log.info("worker processed=%d checked=%d", processed, len(messages))
    return processed


async def run_worker_forever(*, poll_seconds: float = 2.0) -> None:
    while True:
        try:
            await run_worker_once()
        except Exception:
            log.exception("worker iteration failed")
        await asyncio.sleep(poll_seconds)


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    asyncio.run(run_worker_forever())


if __name__ == "__main__":
    main()
