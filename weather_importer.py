import httpx
import sqlite3
import time
from datetime import date

DB_PATH = "memories.db"

def insert_memory(text: str, date_str: str | None, created_by: str, tags: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    created_ms = int(time.time() * 1000)
    mem_id = uuid.uuid4().hex[:10]
    cur.execute("""
        INSERT INTO memories (id, date, text, createdBy, createdDate, tags)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (mem_id, date_str, text, created_by, created_ms, tags))
    conn.commit()
    conn.close()

def import_weather():
    # Example: call some weather API or even a stub
    forecast_text = "weather forecast: High of 72, low of 54, partly cloudy"
    today = date.today().isoformat()
    insert_memory(forecast_text, today, "weather", "weather")

if __name__ == "__main__":
    import_weather()
