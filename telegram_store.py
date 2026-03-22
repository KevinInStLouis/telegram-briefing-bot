# telegram_store.py
from __future__ import annotations

import json
import os
from typing import Any

BASE_DIR = os.path.expanduser(os.getenv("BOT_BASE_DIR", os.getcwd()))

STATE_PATH = os.path.join(BASE_DIR, "telegram_state.json")
INBOX_PATH = os.path.join(BASE_DIR, "inbox.jsonl")
OUTBOX_PATH = os.path.join(BASE_DIR, "outbox.jsonl")


def _read_json(path: str, default: dict[str, Any]) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except Exception:
        return default


def _write_json(path: str, obj: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)


def load_state() -> dict[str, Any]:
    return _read_json(STATE_PATH, {"last_update_id": 0})


def save_state(state: dict[str, Any]) -> None:
    _write_json(STATE_PATH, state)


def append_inbox(item: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(INBOX_PATH) or ".", exist_ok=True)
    with open(INBOX_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def read_outbox_all() -> list[dict[str, Any]]:
    try:
        with open(OUTBOX_PATH, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    except FileNotFoundError:
        return []


def write_outbox_all(items: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(OUTBOX_PATH) or ".", exist_ok=True)
    with open(OUTBOX_PATH, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def queue_outbox(
    chat_id: int, 
    text: str, 
    parse_mode: str | None = None,
    kind: str | None = None,
) -> None:
    """
    Append a messge to outbox.jsonl.
    chat_id  - Telegram chat this should eventually be sent to
    text     - full message text (we are no longer shortening)
    parse_mode - optional Telegram parse_mode (for example MmarkDown)
    kind     - optional logical typ, eg "chat_reply", "daily_brief"
    """
    items = read_outbox_all()
    obj: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if parse_mode:
        obj["parse_mode"] = parse_mode
    if kind:
        obj["kind"] = kind
    items.append(obj)
    write_outbox_all(items)
