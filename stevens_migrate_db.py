# stevens_migrate_db.py
from __future__ import annotations

from db import get_db_path, open_db, migrate


def main() -> None:
    db_path = get_db_path()
    with open_db(db_path) as conn:
        migrate(conn)
    print(f"Stevens database migrated: {db_path}")


if __name__ == "__main__":
    main()
