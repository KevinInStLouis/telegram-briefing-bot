# telegram_bot.py
from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv

from chat_history import record_chat_message
from telegram_commands import handle_telegram_command
from telegram_store import queue_outbox

BASE_DIR = os.path.expanduser(os.getenv("BOT_BASE_DIR", os.getcwd()))
INBOX_PATH = os.path.join(BASE_DIR, "inbox.jsonl")
BRAIN_STATE_PATH = os.path.join(BASE_DIR, "brain_state.json")

BOT_SENDER_ID = "stevens"
BOT_SENDER_NAME = "Stevens"


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


def _sender_id(message: dict[str, Any]) -> str:
    raw = message.get("raw") or {}
    msg = raw.get("message") or raw.get("edited_message") or {}
    sender = msg.get("from") or {}
    return str(sender.get("id") or message.get("from") or "unknown")


def _sender_name(message: dict[str, Any]) -> str:
    raw = message.get("raw") or {}
    msg = raw.get("message") or raw.get("edited_message") or {}
    sender = msg.get("from") or {}
    username = sender.get("username")
    first_name = sender.get("first_name")
    last_name = sender.get("last_name")
    if username:
        return str(username)
    if first_name or last_name:
        return " ".join(part for part in [first_name, last_name] if part)
    return str(message.get("from") or "unknown")


def process_inbox_once(max_messages: int = 5000) -> None:
    """
    Read stored Telegram inbox messages and run deterministic Stevens commands.

    This is the current vertical slice:
      Telegram message -> SQLite chat history / memories -> outbox reply
      and selected commands -> compact display state.
    """
    state = _load_brain_state()
    last_update_id = int(state.get("last_update_id") or 0)

    inbox = _read_inbox()
    if not inbox:
        print("No inbox messages found.")
        return

    new_msgs = [m for m in inbox if int(m.get("update_id") or 0) > last_update_id]
    new_msgs.sort(key=lambda x: int(x.get("update_id") or 0))

    if not new_msgs:
        print("No new messages to process.")
        return

    processed = 0
    max_seen = last_update_id

    for message in new_msgs:
        if processed >= max_messages:
            break

        update_id = int(message.get("update_id") or 0)
        chat_id = message.get("chat_id")
        text = (message.get("text") or "").strip()

        if not chat_id or not text:
            max_seen = max(max_seen, update_id)
            continue

        chat_id_int = int(chat_id)

        record_chat_message(
            chat_id=chat_id_int,
            sender_id=_sender_id(message),
            sender_name=_sender_name(message),
            message=text,
            is_bot=False,
        )

        result = handle_telegram_command(text, chat_id=chat_id_int)
        reply_text = result.text

        queue_outbox(chat_id=chat_id_int, text=reply_text, kind=result.kind)
        record_chat_message(
            chat_id=chat_id_int,
            sender_id=BOT_SENDER_ID,
            sender_name=BOT_SENDER_NAME,
            message=reply_text,
            is_bot=True,
        )

        processed += 1
        max_seen = max(max_seen, update_id)
        print(f"Processed update_id={update_id} -> queued {result.kind}")

    state["last_update_id"] = max_seen
    _save_brain_state(state)
    print(f"Done. Processed={processed}. last_update_id={max_seen}")


def main() -> None:
    load_dotenv()
    process_inbox_once()


if __name__ == "__main__":
    main()
