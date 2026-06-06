from __future__ import annotations

import asyncio
import logging
import os

import httpx
from dotenv import load_dotenv

from alfred.storage.db import init_db
from alfred.storage.queues import get_pending_outbox, mark_outbox_failed, mark_outbox_sent

log = logging.getLogger(__name__)


def _api_base() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or ":" not in token:
        raise RuntimeError("Missing or invalid TELEGRAM_BOT_TOKEN")
    return f"https://api.telegram.org/bot{token}"


async def send_message(client: httpx.AsyncClient, *, chat_id: int, text: str) -> None:
    response = await client.post(
        f"{_api_base()}/sendMessage",
        json={"chat_id": chat_id, "text": text},
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram sendMessage failed: {data}")


async def run_sender_once(*, limit: int = 50, max_attempts: int = 5) -> int:
    init_db()
    messages = get_pending_outbox(limit=limit)
    if not messages:
        log.info("sender outbox empty")
        return 0

    sent = 0
    async with httpx.AsyncClient(timeout=30) as client:
        for message in messages:
            try:
                await send_message(client, chat_id=message.chat_id, text=message.text)
                mark_outbox_sent(message.id)
                sent += 1
            except Exception as exc:
                retry = (message.attempts + 1) < max_attempts
                mark_outbox_failed(message.id, str(exc), retry=retry)
                log.exception("sender failed outbox_id=%s retry=%s", message.id, retry)

    log.info("sender sent=%d checked=%d", sent, len(messages))
    return sent


async def run_sender_forever(*, poll_seconds: float = 2.0) -> None:
    while True:
        try:
            await run_sender_once()
        except Exception:
            log.exception("sender iteration failed")
        await asyncio.sleep(poll_seconds)


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    asyncio.run(run_sender_forever())


if __name__ == "__main__":
    main()
