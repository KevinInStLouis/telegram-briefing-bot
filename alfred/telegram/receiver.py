from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv

from alfred.storage.db import init_db
from alfred.storage.queues import save_telegram_update
from alfred.storage.state import get_state, set_state

log = logging.getLogger(__name__)
STATE_KEY_LAST_UPDATE_ID = "telegram.last_update_id"


def _api_base() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or ":" not in token:
        raise RuntimeError("Missing or invalid TELEGRAM_BOT_TOKEN")
    return f"https://api.telegram.org/bot{token}"


async def fetch_updates(client: httpx.AsyncClient, *, offset: int, timeout: int) -> list[dict[str, Any]]:
    payload = {
        "offset": offset,
        "limit": 100,
        "timeout": timeout,
        "allowed_updates": ["message", "edited_message"],
    }
    response = await client.post(f"{_api_base()}/getUpdates", json=payload)
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram getUpdates failed: {data}")
    return data.get("result", [])


async def run_receiver_once(*, long_poll_seconds: int = 20) -> int:
    init_db()
    last_update_id = int(get_state(STATE_KEY_LAST_UPDATE_ID, 0) or 0)
    offset = last_update_id + 1 if last_update_id else 0

    async with httpx.AsyncClient(timeout=long_poll_seconds + 10) as client:
        updates = await fetch_updates(client, offset=offset, timeout=long_poll_seconds)

    max_update_id = last_update_id
    inserted = 0
    for update in updates:
        update_id = int(update.get("update_id") or 0)
        max_update_id = max(max_update_id, update_id)
        if save_telegram_update(update):
            inserted += 1

    if max_update_id > last_update_id:
        set_state(STATE_KEY_LAST_UPDATE_ID, max_update_id)

    log.info("receiver fetched=%d inserted=%d last_update_id=%d", len(updates), inserted, max_update_id)
    return inserted


async def run_receiver_forever(*, poll_seconds: float = 1.0, long_poll_seconds: int = 20) -> None:
    while True:
        try:
            await run_receiver_once(long_poll_seconds=long_poll_seconds)
        except Exception:
            log.exception("receiver iteration failed")
        await asyncio.sleep(poll_seconds)


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    asyncio.run(run_receiver_forever())


if __name__ == "__main__":
    main()
