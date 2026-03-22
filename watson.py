# watson.py
from __future__ import annotations
from memory_store import load_memory, shorten

import textwrap
from datetime import date, datetime
from typing import Any, Iterable, Optional
from pathlib import Path
from system_prompt import SYSTEM_PROMPT
from llm import generate

def format_memories_for_prompt(memories: list[dict[str, Any]], fiulepath: str = "short-term_memory.md") -> None:
    """
    Turn markdown memory rows (dicts) into a compact text block for the prompt.
    """
    if not memories:
        return "(none)"

    lines: list[str] = []
    for m in memories:
        d = m.get("date")
        created_by = m.get("createdBy") or ""
        tags = m.get("tags") or ""
        text = (m.get("text") or "").strip()
        if not text:
            continue

        # Keep it short and prompt-friendly
        if d:
            lines.append(f"- {d} [{created_by}] ({tags}): {text}")
        else:
            lines.append(f"- (undated) [{created_by}] ({tags}): {text}")

    return "\n".join(lines) if lines else "(none)"


def build_prompt_for_chat(user_message: str, today_str: str) -> str:
    return textwrap.dedent(f"""
    {SYSTEM_PROMPT}
    Bruce: {user_message.strip()}
    Alfred:
    """).strip()


def build_prompt_for_hourly_brief(
    memories_text: str, 
    when_str: str, 
    weekday_name: str, 
    is_sunday: bool,
) -> str:
    memories_text = shorten(memories_text, 150)
    return textwrap.dedent(f"""
    {SYSTEM_PROMPT}
    MODE: HOURLY BRIEFING
    Today: {when_str} ({weekday_name})
    Is today Sunday? {"yes" if is_sunday else "no"}
    MEMORIES:
    {memories_text}
    Alfred:
    """).strip()

async def watson_chat_reply(user_message: str, *, today: Optional[date] = None) -> str:
    today = today or date.today()
    prompt = build_prompt_for_chat(
        user_message=user_message,
        today_str=today.isoformat()
    )
    return (await generate(prompt)).strip()

async def watson_hourly_brief(text: str, today: date, hour: int) -> str:
    now = datetime.now()
    today = now.date
    hour = now.hour
    memories = fetch_relevant_memories_for_date(today)
    memories_full = format_memories_for_prompt(memories)
    memories_text = shorten(memories_full)
    weekday_name = today.strftime("%A")
    is_sunday = (weekday_name == "Sunday")
    prompt = build_prompt_for_hourly_brief(
        memories_text=memories_text,
        now_str=now.strftime("%A %Y-%m-%d %H:00"),
        weekday_name=weekday_name,
        is_sunday=is_sunday,
    )
    return (await generate(prompt)).strip()

