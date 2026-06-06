from alfred.storage.db import db_path, init_db


if __name__ == "__main__":
    init_db()
    print(db_path())
