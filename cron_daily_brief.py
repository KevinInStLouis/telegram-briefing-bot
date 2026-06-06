# cron_daily_brief.py
from __future__ import annotations

from dotenv import load_dotenv

from daily_brief import queue_daily_brief


def cron_daily_brief() -> None:
    """Queue one deterministic daily briefing for Telegram.

    This script is intentionally thin so cron/systemd can call it. Delivery is
    still handled by telegram_pump.py, preserving the inbox/outbox boundary.
    """
    load_dotenv()
    result = queue_daily_brief()
    print(f"Queued scheduled daily briefing for chat {result.chat_id}")
    if result.display_result.ok:
        print(f"display ok: {result.display_result.target}")
    else:
        print(f"display failed: {result.display_result.target}: {result.display_result.error}")
        if result.display_result.frame_path:
            print(f"frame saved: {result.display_result.frame_path}")


if __name__ == "__main__":
    cron_daily_brief()
