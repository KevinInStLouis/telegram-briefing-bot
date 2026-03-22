import sqlite3
import uuid
from datetime import datetime, timezone

DB_PATH = "memories_demo.db"
TABLE_NAME = "memories_demo"

def get_connection():
	return sqlite3.connect(DB_PATH)



def create_memories_demo_table(conn):
	cur = conn.cursor()
	cur.execute(f"""
		CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
			id TEXT PRIMARY KEY,
			date TEXT,
			text TEXT NOT NULL,
			createdBy TEXT,
			createdDate INTEGER,
			tags TEXT
		)
	""")
	conn.commit()
	print(f"Created table: {TABLE_NAME}")

if __name__ == "__main__":
	conn = get_connection()
	create_memories_demo_table(conn)
	conn.close()
