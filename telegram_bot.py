# telegram_bot.py
from __future__ import annotations

import os
import json
import asyncio
from datetime import datetime, date
from typing import Any

from dotenv import load_dotenv

from watson import watson_chat_reply, watson_hourly_brief
from memory_store import shorten
from telegram_store import queue_outbox

BASE_DIR = os.path.expanduser(os.getenv("BOT_BASE_DIR", os.getcwd()))
INBOX_PATH = os.path.join(BASE_DIR, "inbox.jsonl")
BRAIN_STATE_PATH = os.path.join(BASE_DIR, "brain_state.json")


def _load_brain_state() -> dict[str, Any]:
    try:
        with open(BRAIN_STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_update_id": 0}
    except Exception:
        return {"last_update_id": 0}


def _save_brain_state(state: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(BRAIN_STATE_PATH) or ".", exist_ok=True)
    with open(BRAIN_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def _read_inbox() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        with open(INBOX_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return []
    return items

async def hourly_briefing(*, now: datetime) -> None:

    today = now.date
    hour = now.hour
    # day + hour string
    when_str = now.strftime("%A %Y-%m-%d %H:00")

    # THIS is what you were missing:
    text = f"Hourly briefing for {when_str}"
    brief = await watson_hourly_brief(text=text, today=today, hour=hour)
    queue_outbox(chat_id=int(chat_id), text=brief)
    return brief

async def process_inbox_once(max_messages: int = 5000) -> None:
    """
    Read stored inbound messages and generate outbound replies into outbox.
    Marks progress by last_update_id in brain_state.json.
    """
    state = _load_brain_state()
    last_update_id = int(state.get("last_update_id") or 0)

    inbox = _read_inbox()
    if not inbox:
        print("No inbox messages found.")
        return

    # Only process messages newer than last_update_id
    new_msgs = [m for m in inbox if int(m.get("update_id") or 0) > last_update_id]
    new_msgs.sort(key=lambda x: int(x.get("update_id") or 0))

    if not new_msgs:
        print("No new messages to process.")
        return

    processed = 0
    max_seen = last_update_id

    for m in new_msgs:
        if processed >= max_messages:
            break

        update_id = int(m.get("update_id") or 0)
        chat_id = m.get("chat_id")
        text = (m.get("text") or "").strip()

        # Must have chat_id + text to respond
        if not chat_id or not text:
            max_seen = max(max_seen, update_id)
            continue

        # 1) Call LLM
        full_reply = await watson_chat_reply(text, today=date.today())

        # 2) Shorten for Telegram output (store in outbox)
        reply = shorten(full_reply, max_chars=1000)  # adjust if you want 225

        # 3) Queue outbound message
        queue_outbox(chat_id=int(chat_id), text=full_reply)

        processed += 1
        max_seen = max(max_seen, update_id)
        print(f"Processed update_id={update_id} -> queued reply ({len(reply)} chars)")

    # Save progress so we do not reprocess the same inbound messages
    state["last_update_id"] = max_seen
    _save_brain_state(state)
    print(f"Done. Processed={processed}. last_update_id={max_seen}")


def main() -> None:
    load_dotenv()  # reads .env if present; token used by telegram_pump, not needed here
    now = datetime.now()
    asyncio.run(process_inbox_once())
    asyncio.run(hourly_briefing(now=now))

if __name__ == "__main__":
    main()
