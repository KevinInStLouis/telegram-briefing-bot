# chat_history.py
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass

from db import open_migrated_db


@dataclass(frozen=True)
class ChatMessage:
    id: int
    chat_id: int
    sender_id: str
    sender_name: str
    message: str
    timestamp: int
    is_bot: int


def now_ms() -> int:
    return int(time.time() * 1000)


def _row_to_chat_message(row: sqlite3.Row) -> ChatMessage:
    return ChatMessage(
        id=int(row["id"]),
        chat_id=int(row["chat_id"]),
        sender_id=str(row["sender_id"]),
        sender_name=str(row["sender_name"]),
        message=str(row["message"]),
        timestamp=int(row["timestamp"]),
        is_bot=int(row["is_bot"]),
    )


def record_chat_message(
    *,
    chat_id: int,
    sender_id: str,
    sender_name: str,
    message: str,
    is_bot: bool,
    timestamp: int | None = None,
    conn: sqlite3.Connection | None = None,
) -> int:
    """Store Telegram conversation history. This is not long-term memory."""
    message = message or ""
    if not message.strip():
        raise ValueError("message cannot be empty")

    should_close = conn is None
    conn = conn or open_migrated_db()
    try:
        cur = conn.execute(
            """
            INSERT INTO telegram_chats
              (chat_id, sender_id, sender_name, message, timestamp, is_bot)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                int(chat_id),
                sender_id or "unknown",
                sender_name or "unknown",
                message,
                timestamp or now_ms(),
                1 if is_bot else 0,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        if should_close:
            conn.close()


def list_chat_history(
    *,
    chat_id: int | None = None,
    limit: int = 50,
    conn: sqlite3.Connection | None = None,
) -> list[ChatMessage]:
    limit = max(1, min(int(limit), 500))

    should_close = conn is None
    conn = conn or open_migrated_db()
    try:
        if chat_id is None:
            rows = conn.execute(
                """
                SELECT id, chat_id, sender_id, sender_name, message, timestamp, is_bot
                FROM telegram_chats
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, chat_id, sender_id, sender_name, message, timestamp, is_bot
                FROM telegram_chats
                WHERE chat_id = ?
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (int(chat_id), limit),
            ).fetchall()

        return [_row_to_chat_message(row) for row in rows]
    finally:
        if should_close:
            conn.close()
