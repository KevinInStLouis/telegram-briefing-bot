# memories.py
from __future__ import annotations

import secrets
import sqlite3
import time
from dataclasses import dataclass
from datetime import date as Date
from typing import Any

from db import open_migrated_db


@dataclass(frozen=True)
class Memory:
    id: str
    date: str | None
    text: str
    tags: str | None
    createdBy: str | None
    createdDate: int


def new_memory_id(length: int = 10) -> str:
    """Generate a short URL-safe id similar in spirit to nanoid(10)."""
    return secrets.token_urlsafe(length)[:length]


def now_ms() -> int:
    return int(time.time() * 1000)


def _row_to_memory(row: sqlite3.Row) -> Memory:
    return Memory(
        id=str(row["id"]),
        date=row["date"],
        text=str(row["text"]),
        tags=row["tags"],
        createdBy=row["createdBy"],
        createdDate=int(row["createdDate"] or 0),
    )


def create_memory(
    text: str,
    *,
    date: str | Date | None = None,
    tags: str | None = None,
    created_by: str = "telegram",
    memory_id: str | None = None,
    created_date: int | None = None,
    conn: sqlite3.Connection | None = None,
) -> Memory:
    """Create one permanent notebook memory."""
    text = " ".join((text or "").split())
    if not text:
        raise ValueError("memory text cannot be empty")

    if isinstance(date, Date):
        date_text: str | None = date.isoformat()
    else:
        date_text = date

    memory = Memory(
        id=memory_id or new_memory_id(),
        date=date_text,
        text=text,
        tags=tags,
        createdBy=created_by,
        createdDate=created_date or now_ms(),
    )

    should_close = conn is None
    conn = conn or open_migrated_db()
    try:
        conn.execute(
            """
            INSERT INTO memories (id, date, text, tags, createdBy, createdDate)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                memory.id,
                memory.date,
                memory.text,
                memory.tags,
                memory.createdBy,
                memory.createdDate,
            ),
        )
        conn.commit()
        return memory
    finally:
        if should_close:
            conn.close()


def list_memories(
    *,
    limit: int = 20,
    tag: str | None = None,
    created_by: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> list[Memory]:
    """Return recent memories from Stevens' permanent notebook."""
    limit = max(1, min(int(limit), 100))
    where: list[str] = []
    params: list[Any] = []

    if tag:
        where.append("tags LIKE ?")
        params.append(f"%{tag}%")
    if created_by:
        where.append("createdBy = ?")
        params.append(created_by)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    should_close = conn is None
    conn = conn or open_migrated_db()
    try:
        rows = conn.execute(
            f"""
            SELECT id, date, text, tags, createdBy, createdDate
            FROM memories
            {where_sql}
            ORDER BY createdDate DESC
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
        return [_row_to_memory(row) for row in rows]
    finally:
        if should_close:
            conn.close()


def get_memory(memory_id: str, *, conn: sqlite3.Connection | None = None) -> Memory | None:
    should_close = conn is None
    conn = conn or open_migrated_db()
    try:
        row = conn.execute(
            """
            SELECT id, date, text, tags, createdBy, createdDate
            FROM memories
            WHERE id = ?
            """,
            (memory_id,),
        ).fetchone()
        return _row_to_memory(row) if row else None
    finally:
        if should_close:
            conn.close()


def delete_memory(memory_id: str, *, conn: sqlite3.Connection | None = None) -> bool:
    should_close = conn is None
    conn = conn or open_migrated_db()
    try:
        cur = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        if should_close:
            conn.close()


def format_memory_for_telegram(memory: Memory) -> str:
    parts = [f"{memory.id}: {memory.text}"]
    meta: list[str] = []
    if memory.date:
        meta.append(memory.date)
    if memory.tags:
        meta.append(memory.tags)
    if memory.createdBy:
        meta.append(memory.createdBy)
    if meta:
        parts.append(f"  ({', '.join(meta)})")
    return "\n".join(parts)
