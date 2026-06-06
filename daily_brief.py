# daily_brief.py
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from chat_history import record_chat_message
from display_sender import DisplaySendResult, send_display_state
from display_state import status_state
from memories import Memory, list_memories
from telegram_store import queue_outbox


BOT_SENDER_ID = "stevens"
BOT_SENDER_NAME = "Stevens"


@dataclass(frozen=True)
class DailyBriefResult:
    chat_id: int
    text: str
    display_result: DisplaySendResult


def local_today() -> Date:
    timezone_name = os.getenv("STEVENS_TIMEZONE", "America/Chicago")
    return datetime.now(ZoneInfo(timezone_name)).date()


def configured_chat_id() -> int:
    raw = os.getenv("TELEGRAM_CHAT_ID")
    if not raw:
        raise RuntimeError("TELEGRAM_CHAT_ID is required to queue a daily briefing")
    return int(raw)


def _clean_memory_text(memory: Memory) -> str:
    text = " ".join(memory.text.split())
    prefixes = [
        "weather forecast:",
        "calendar:",
        "mail:",
        "daily fact:",
    ]
    lowered = text.lower()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return text[len(prefix):].strip()
    return text


def _memory_bucket(memory: Memory) -> str:
    tags = (memory.tags or "").lower()
    created_by = (memory.createdBy or "").lower()
    text = memory.text.lower()

    if "weather" in tags or created_by == "weather" or text.startswith("weather forecast:"):
        return "weather"
    if "calendar" in tags or created_by == "calendar" or text.startswith("calendar:"):
        return "calendar"
    if "mail" in tags or created_by == "mail" or text.startswith("mail:"):
        return "mail"
    if "fact" in tags or created_by in {"daily_fact", "fact"} or text.startswith("daily fact:"):
        return "fact"
    return "other"


def get_briefing_memories(*, today: Date | None = None, limit: int = 50) -> list[Memory]:
    """Return memories suitable for the deterministic daily briefing."""
    today = today or local_today()
    today_text = today.isoformat()
    memories = list_memories(limit=limit, tag="briefing")

    dated = [m for m in memories if not m.date or m.date == today_text]
    if dated:
        return dated
    return memories


def build_daily_brief(*, today: Date | None = None, memories: list[Memory] | None = None) -> str:
    """Build a deterministic Telegram-friendly daily briefing.

    This deliberately does not call the local LLM. The briefing mechanism should
    work before any style-polishing model is introduced.
    """
    today = today or local_today()
    memories = memories if memories is not None else get_briefing_memories(today=today)

    buckets: dict[str, list[Memory]] = {
        "weather": [],
        "calendar": [],
        "mail": [],
        "fact": [],
        "other": [],
    }
    for memory in memories:
        buckets[_memory_bucket(memory)].append(memory)

    lines: list[str] = [
        "Good morning.",
        f"Daily briefing for {today.strftime('%A, %B %-d')}.",
        "",
    ]

    if buckets["weather"]:
        lines.append(f"Weather: {_clean_memory_text(buckets['weather'][0])}")

    if buckets["calendar"]:
        lines.append(f"Calendar: {_clean_memory_text(buckets['calendar'][0])}")

    if buckets["mail"]:
        lines.append(f"Mail: {_clean_memory_text(buckets['mail'][0])}")

    if buckets["other"]:
        lines.append("Notes:")
        for memory in buckets["other"][:3]:
            lines.append(f"- {_clean_memory_text(memory)}")

    if buckets["fact"]:
        lines.append(f"Daily fact: {_clean_memory_text(buckets['fact'][0])}")

    if not any(buckets.values()):
        lines.append("No briefing memories are recorded yet.")

    lines.extend(["", "At your service."])
    return "\n".join(lines)


def queue_daily_brief(*, chat_id: int | None = None, today: Date | None = None) -> DailyBriefResult:
    load_dotenv()
    chat_id = int(chat_id if chat_id is not None else configured_chat_id())
    today = today or local_today()
    text = build_daily_brief(today=today)

    queue_outbox(chat_id=chat_id, text=text, kind="daily_brief")
    record_chat_message(
        chat_id=chat_id,
        sender_id=BOT_SENDER_ID,
        sender_name=BOT_SENDER_NAME,
        message=text,
        is_bot=True,
    )
    display_result = send_display_state(
        status_state(
            source="briefing",
            line1="Brief queued",
            line2=today.isoformat(),
            line3="Telegram outbox",
        )
    )
    return DailyBriefResult(chat_id=chat_id, text=text, display_result=display_result)


def main() -> None:
    result = queue_daily_brief()
    print(f"Queued daily briefing for chat {result.chat_id}")
    print(result.text)
    if result.display_result.ok:
        print(f"display ok: {result.display_result.target}")
    else:
        print(f"display failed: {result.display_result.target}: {result.display_result.error}")
        if result.display_result.frame_path:
            print(f"frame saved: {result.display_result.frame_path}")


if __name__ == "__main__":
    main()
