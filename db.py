# db.py
from __future__ import annotations

import os
import sqlite3
from pathlib import Path


DEFAULT_DB_RELATIVE_PATH = Path("data") / "stevens.db"


MEMORIES_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    date TEXT,
    text TEXT NOT NULL,
    tags TEXT,
    createdBy TEXT,
    createdDate INTEGER
);
"""


TELEGRAM_CHATS_SCHEMA = """
CREATE TABLE IF NOT EXISTS telegram_chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    sender_id TEXT NOT NULL,
    sender_name TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    is_bot INTEGER NOT NULL
);
"""


INDEXES_SCHEMA = """
CREATE INDEX IF NOT EXISTS idx_memories_createdDate
ON memories(createdDate DESC);

CREATE INDEX IF NOT EXISTS idx_memories_date
ON memories(date);

CREATE INDEX IF NOT EXISTS idx_memories_createdBy
ON memories(createdBy);

CREATE INDEX IF NOT EXISTS idx_telegram_chats_chat_timestamp
ON telegram_chats(chat_id, timestamp DESC);
"""


def get_db_path() -> Path:
    """
    Return the Stevens SQLite path.

    Priority:
    1. STEVENS_DB_PATH, if set.
    2. BOT_BASE_DIR/data/stevens.db, if BOT_BASE_DIR is set.
    3. ./data/stevens.db from the current working directory.
    """
    explicit = os.getenv("STEVENS_DB_PATH")
    if explicit:
        return Path(explicit).expanduser()

    base_dir = Path(os.path.expanduser(os.getenv("BOT_BASE_DIR", os.getcwd())))
    return base_dir / DEFAULT_DB_RELATIVE_PATH


def open_db(path: str | os.PathLike[str] | None = None) -> sqlite3.Connection:
    db_path = Path(path).expanduser() if path else get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    """Create the permanent notebook and Telegram chat-history tables."""
    conn.executescript(MEMORIES_SCHEMA)
    conn.executescript(TELEGRAM_CHATS_SCHEMA)
    conn.executescript(INDEXES_SCHEMA)
    conn.commit()


def open_migrated_db(path: str | os.PathLike[str] | None = None) -> sqlite3.Connection:
    conn = open_db(path)
    migrate(conn)
    return conn
