from __future__ import annotations

import textwrap
from datetime import date

from alfred.brain.system_prompt import SYSTEM_PROMPT
from alfred.llm.ollama import generate


def build_prompt_for_chat(user_message: str, *, today: date) -> str:
    return textwrap.dedent(
        f"""
        {SYSTEM_PROMPT}

        Today: {today.isoformat()}

        Bruce: {user_message.strip()}
        Alfred:
        """
    ).strip()


async def watson_chat_reply(user_message: str, *, today: date | None = None) -> str:
    today = today or date.today()
    prompt = build_prompt_for_chat(user_message, today=today)
    return (await generate(prompt)).strip()
