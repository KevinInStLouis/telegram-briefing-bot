from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def base_dir() -> Path:
    return Path(os.getenv("BOT_BASE_DIR", os.getcwd())).expanduser().resolve()


def db_path() -> Path:
    configured = os.getenv("BOT_DB_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return base_dir() / "alfred.db"


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS bot_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS telegram_inbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                update_id INTEGER NOT NULL UNIQUE,
                chat_id INTEGER,
                sender_name TEXT,
                text TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                processed_at TEXT,
                error TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_telegram_inbox_status_id
                ON telegram_inbox(status, id);

            CREATE TABLE IF NOT EXISTS telegram_outbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                payload_json TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                attempts INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                sent_at TEXT,
                last_error TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_telegram_outbox_status_id
                ON telegram_outbox(status, id);

            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                date TEXT,
                text TEXT NOT NULL,
                created_by TEXT,
                created_at INTEGER NOT NULL,
                tags TEXT
            );

            CREATE TABLE IF NOT EXISTS workflow_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_name TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                finished_at TEXT,
                details_json TEXT
            );
            """
        )
