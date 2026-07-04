from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .db import connect


@dataclass(frozen=True)
class InboxMessage:
    id: int
    update_id: int
    chat_id: int | None
    sender_name: str | None
    text: str


@dataclass(frozen=True)
class OutboxMessage:
    id: int
    chat_id: int
    text: str
    attempts: int


def _message_from_update(update: dict[str, Any]) -> dict[str, Any] | None:
    return update.get("message") or update.get("edited_message")


def save_telegram_update(update: dict[str, Any]) -> bool:
    """Persist one Telegram update. Returns True when a text/caption record was inserted."""
    update_id = int(update.get("update_id") or 0)
    message = _message_from_update(update)
    if not update_id or not message:
        return False

    text = (message.get("text") or message.get("caption") or "").strip()
    if not text:
        return False

    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    sender_name = sender.get("username") or sender.get("first_name") or sender.get("id")

    with connect() as conn:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO telegram_inbox
                (update_id, chat_id, sender_name, text, raw_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (update_id, chat.get("id"), str(sender_name) if sender_name else None, text, json.dumps(update)),
        )
        return cur.rowcount > 0


def get_pending_inbox(limit: int = 50) -> list[InboxMessage]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, update_id, chat_id, sender_name, text
            FROM telegram_inbox
            WHERE status = 'pending'
            ORDER BY id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [InboxMessage(**dict(row)) for row in rows]


def mark_inbox_processed(message_id: int) -> None:
    with connect() as conn:
        conn.execute(
            """
            UPDATE telegram_inbox
            SET status = 'processed', processed_at = CURRENT_TIMESTAMP, error = NULL
            WHERE id = ?
            """,
            (message_id,),
        )


def mark_inbox_failed(message_id: int, error: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            UPDATE telegram_inbox
            SET status = 'failed', processed_at = CURRENT_TIMESTAMP, error = ?
            WHERE id = ?
            """,
            (error[:1000], message_id),
        )


def queue_outbox(chat_id: int, text: str, payload: dict[str, Any] | None = None) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO telegram_outbox (chat_id, text, payload_json)
            VALUES (?, ?, ?)
            """,
            (chat_id, text, json.dumps(payload) if payload else None),
        )
        return int(cur.lastrowid)


def get_pending_outbox(limit: int = 50) -> list[OutboxMessage]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, chat_id, text, attempts
            FROM telegram_outbox
            WHERE status = 'pending'
            ORDER BY id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [OutboxMessage(**dict(row)) for row in rows]


def mark_outbox_sent(message_id: int) -> None:
    with connect() as conn:
        conn.execute(
            """
            UPDATE telegram_outbox
            SET status = 'sent', sent_at = CURRENT_TIMESTAMP, last_error = NULL
            WHERE id = ?
            """,
            (message_id,),
        )


def mark_outbox_failed(message_id: int, error: str, *, retry: bool = True) -> None:
    status = "pending" if retry else "failed"
    with connect() as conn:
        conn.execute(
            """
            UPDATE telegram_outbox
            SET status = ?, attempts = attempts + 1, last_error = ?
            WHERE id = ?
            """,
            (status, error[:1000], message_id),
        )
