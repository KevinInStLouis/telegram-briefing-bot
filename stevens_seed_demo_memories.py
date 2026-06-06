# stevens_seed_demo_memories.py
from __future__ import annotations

from datetime import datetime, timezone

from db import get_db_path, open_migrated_db
from memories import new_memory_id


DEMO_MEMORIES_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories_demo (
    id TEXT PRIMARY KEY,
    date TEXT,
    text TEXT NOT NULL,
    tags TEXT,
    createdBy TEXT,
    createdDate INTEGER
);
"""


DEMO_ROWS = [
    {
        "date": "2026-06-06",
        "text": "weather forecast: High of 75, low of 60, partly cloudy with showers after 2pm.",
        "tags": "weather,briefing",
        "createdBy": "weather",
    },
    {
        "date": "2026-06-06",
        "text": "calendar: No fixed appointments are recorded for this morning.",
        "tags": "calendar,briefing",
        "createdBy": "calendar",
    },
    {
        "date": "2026-06-06",
        "text": "mail: No urgent postal notices are recorded.",
        "tags": "mail,briefing",
        "createdBy": "mail",
    },
    {
        "date": "2026-06-06",
        "text": "daily fact: Honey never spoils when sealed and stored properly.",
        "tags": "fact,briefing",
        "createdBy": "daily_fact",
    },
]


def main() -> None:
    db_path = get_db_path()
    now = int(datetime.now(timezone.utc).timestamp() * 1000)

    with open_migrated_db(db_path) as conn:
        conn.executescript(DEMO_MEMORIES_SCHEMA)
        conn.execute("DELETE FROM memories_demo")

        for index, row in enumerate(DEMO_ROWS):
            conn.execute(
                """
                INSERT INTO memories_demo
                  (id, date, text, tags, createdBy, createdDate)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    new_memory_id(),
                    row["date"],
                    row["text"],
                    row["tags"],
                    row["createdBy"],
                    now + index,
                ),
            )
        conn.commit()

    print(f"Seeded {len(DEMO_ROWS)} demo memories into memories_demo: {db_path}")


if __name__ == "__main__":
    main()
