# daily_brief.py
import os
import asyncio
from datetime import date
import httpx
from dotenv import load_dotenv


from watson import watson_daily_brief

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN:
    raise SystemExit("Missing TELEGRAM_BOT_TOKEN in .env")
if not CHAT_ID:
    raise SystemExit("Missing TELEGRAM_CHAT_ID in .env (needed for push messages)")


async def run() -> None:
    brief = await watson_daily_brief(today=date.today())

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": brief},
        )
        r.raise_for_status()

if __name__ == "__main__":
    asyncio.run(run())
