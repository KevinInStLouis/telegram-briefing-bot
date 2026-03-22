# telegram_pump.py
from __future__ import annotations

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Any

import httpx
from dotenv import load_dotenv

from telegram_store import (
    load_state,
    save_state,
    append_inbox,
    read_outbox_all,
    write_outbox_all,
)

logging.basicConfig(level=logging.INFO)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN or ":" not in TOKEN:
    raise SystemExit("Missing/invalid TELEGRAM_BOT_TOKEN (check .env)")

API_BASE = f"https://api.telegram.org/bot{TOKEN}"
HTTP_TIMEOUT = 30


def _is_text_message(update: dict[str, Any]) -> bool:
    msg = update.get("message") or update.get("edited_message")
    return bool(msg and (msg.get("text") or msg.get("caption")))


async def fetch_updates(client: httpx.AsyncClient, offset: int) -> list[dict[str, Any]]:
    # short poll (not long poll) because cron runs it periodically
    payload = {
        "offset": offset,
        "limit": 100,
        "timeout": 0,
        "allowed_updates": ["message", "edited_message"],
    }
    r = await client.post(f"{API_BASE}/getUpdates", json=payload)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram getUpdates not ok: {data}")
    return data.get("result", [])


async def send_message(client: httpx.AsyncClient, item: dict[str, Any]) -> None:
    r = await client.post(f"{API_BASE}/sendMessage", json=item)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram sendMessage not ok: {data}")


async def main() -> None:
    state = load_state()
    last_update_id = int(state.get("last_update_id") or 0)
    offset = last_update_id + 1 if last_update_id else 0

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        # 1) FETCH inbound
        updates = await fetch_updates(client, offset=offset)
        logging.info("Fetched %d updates", len(updates))

        max_update_id = last_update_id
        for upd in updates:
            uid = int(upd.get("update_id", 0))
            max_update_id = max(max_update_id, uid)

            # Store everything (or filter)
            msg = upd.get("message") or upd.get("edited_message") or {}
            chat = msg.get("chat") or {}
            record = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "update_id": uid,
                "chat_id": chat.get("id"),
                "from": (msg.get("from") or {}).get("username") or (msg.get("from") or {}).get("first_name"),
                "text": msg.get("text") or msg.get("caption") or "",
                "raw": upd,  # keep full payload for debugging
            }
            append_inbox(record)

        if max_update_id != last_update_id:
            state["last_update_id"] = max_update_id
            save_state(state)
            logging.info("Advanced offset to update_id=%d", max_update_id)

        # 2) SEND outbound queue
        outbox = read_outbox_all()
        if not outbox:
            logging.info("Outbox empty")
            return

        remaining: list[dict[str, Any]] = []
        sent = 0

        for item in outbox:
            try:
                await send_message(client, item)
                sent += 1
            except Exception as e:
                # Keep unsent items for next run
                logging.error("Send failed; keeping in outbox. Error: %s", e)
                remaining.append(item)

        write_outbox_all(remaining)
        logging.info("Sent %d messages; %d remaining in outbox", sent, len(remaining))


if __name__ == "__main__":
    asyncio.run(main())
