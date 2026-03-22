# cron_daily_brief.py

from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from alfred.daily_brief import send_daily_briefing

def cron_daily_brief() -> None:
	"""
	Python analogue of the TypeScript cronDailyBrief.

	Designed to be called from cron or systemd:
		- reads TELEGRAM_CHAT_ID from environment
		- Uses 'today' in your local timezone
		' Calls Send_Daily_breifing(chat_id, today)
	"""
	chat_id = os.environ.get("TELEGRAM_CHAT_ID")
	if not chat_id:
		print("TELEGRAM_CHAT_ID is not configured.")
		return

	# use your houselholds tiem zone
	tz = ZoneInfo("America/Chicago")
	today = datetime.now(tz).replace(
		hour=0,
		minute=0,
		second=0,
		microsecond=0,
	)

	print(f"Sending scheduled daily briefing for {today.date()}...")

	try:
		result = send_daily_briefing(chat_id, today)
		print("Result:", result)
	except Exception as e:
		print("error sending scheduled daily briefing:", e)
		# let the process exit non-zero if something goes wrong
		raise

if __name__ == "__main__":
	cron_daily_brief()
