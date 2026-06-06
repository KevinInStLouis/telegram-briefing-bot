# telegram_pump.py
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any

import httpx
from dotenv import load_dotenv

from telegram_store import (
    append_inbox,
    load_state,
    read_outbox_all,
    save_state,
    write_outbox_all,
)

logging.basicConfig(level=logging.INFO)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN or ":" not in TOKEN:
    raise SystemExit("Missing/invalid TELEGRAM_BOT_TOKEN (check .env)")

API_BASE = f"https://api.telegram.org/bot{TOKEN}"
HTTP_TIMEOUT = 30

# Optional safety rail. When TELEGRAM_CHAT_ID is set, Stevens only ingests
# messages from that chat. This keeps the appliance single-household by default.
_ALLOWED_CHAT_ID_RAW = os.getenv("TELEGRAM_CHAT_ID")
ALLOWED_CHAT_ID = int(_ALLOWED_CHAT_ID_RAW) if _ALLOWED_CHAT_ID_RAW else None

TELEGRAM_SEND_KEYS = {
    "chat_id",
    "text",
    "parse_mode",
    "disable_web_page_preview",
    "disable_notification",
    "reply_to_message_id",
    "allow_sending_without_reply",
}


def _is_text_message(update: dict[str, Any]) -> bool:
    msg = update.get("message") or update.get("edited_message")
    return bool(msg and (msg.get("text") or msg.get("caption")))


def _message_from_update(update: dict[str, Any]) -> dict[str, Any]:
    return update.get("message") or update.get("edited_message") or {}


def _is_allowed_chat(chat_id: Any) -> bool:
    if ALLOWED_CHAT_ID is None:
        return True
    try:
        return int(chat_id) == ALLOWED_CHAT_ID
    except (TypeError, ValueError):
        return False


async def fetch_updates(client: httpx.AsyncClient, offset: int) -> list[dict[str, Any]]:
    # Short polling is deliberate here. Cron/systemd can run this periodically.
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
    # Local queue metadata such as "kind" is for Stevens, not Telegram.
    payload = {key: value for key, value in item.items() if key in TELEGRAM_SEND_KEYS}
    r = await client.post(f"{API_BASE}/sendMessage", json=payload)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram sendMessage not ok: {data}")


async def main() -> None:
    state = load_state()
    last_update_id = int(state.get("last_update_id") or 0)
    offset = last_update_id + 1 if last_update_id else 0

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        # 1) Fetch inbound Telegram messages into Stevens' local inbox.
        updates = await fetch_updates(client, offset=offset)
        logging.info("Fetched %d updates", len(updates))

        max_update_id = last_update_id
        appended = 0
        ignored = 0

        for update in updates:
            update_id = int(update.get("update_id", 0))
            max_update_id = max(max_update_id, update_id)

            if not _is_text_message(update):
                ignored += 1
                continue

            msg = _message_from_update(update)
            chat = msg.get("chat") or {}
            chat_id = chat.get("id")

            if not _is_allowed_chat(chat_id):
                ignored += 1
                continue

            sender = msg.get("from") or {}
            record = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "update_id": update_id,
                "chat_id": chat_id,
                "from": sender.get("username") or sender.get("first_name"),
                "text": msg.get("text") or msg.get("caption") or "",
                "raw": update,
            }
            append_inbox(record)
            appended += 1

        if max_update_id != last_update_id:
            state["last_update_id"] = max_update_id
            save_state(state)
            logging.info("Advanced offset to update_id=%d", max_update_id)

        logging.info("Inbox appended=%d ignored=%d", appended, ignored)

        # 2) Send queued outbound messages.
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
                # Keep unsent items for next run.
                logging.error("Send failed; keeping in outbox. Error: %s", e)
                remaining.append(item)

        write_outbox_all(remaining)
        logging.info("Sent %d messages; %d remaining in outbox", sent, len(remaining))


if __name__ == "__main__":
    asyncio.run(main())
