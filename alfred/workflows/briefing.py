from __future__ import annotations

"""
Scheduled workflows belong here, not inside the Telegram chat worker.

This module is intentionally a scaffold. The old daily/hourly briefing code had
broken imports and undefined state. Rebuild it here once the chat loop is stable.
"""


async def run_daily_briefing() -> None:
    raise NotImplementedError("Daily briefing workflow has not been rebuilt yet.")
