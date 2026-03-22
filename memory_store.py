# memory_store.py
from __future__ import annotations

import os
import logging
from datetime import datetime

# Files
DEBUG_LOG_PATH = os.path.expanduser("~/alfred/logs/watson_debug.log")
MEMORY_PATH = os.path.expanduser("~/alfred/memory/watson_memory.txt")

# Keep Watson memory bounded (Pi-friendly)
MEMORY_MAX_CHARS = 10000  # 1500–5000 is a reasonable range


def _ensure_parent(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def append_debug(user_text: str, full_reply: str) -> None:
    """
    Append-only posterity/debug log. Never fed back into prompts.
    """
    try:
        _ensure_parent(DEBUG_LOG_PATH)
        ts = datetime.now().isoformat(timespec="seconds")
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n[{ts}] USER: {user_text}\n")
            f.write(f"[{ts}] WATSON_FULL: {full_reply}\n")
    except Exception:
        logging.exception("Failed writing debug log")


def load_memory(max_chars: int = MEMORY_MAX_CHARS) -> str:
    """
    Load rolling Watson memory (bounded).
    This is what you append into the next prompt.
    """
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            data = f.read()
    except FileNotFoundError:
        return ""
    except Exception:
        logging.exception("Failed reading memory file")
        return ""

    return data[-max_chars:] if len(data) > max_chars else data


def update_memory(user_text: str, short_reply: str) -> None:
    """
    Append a compact entry to memory, then hard-trim to MEMORY_MAX_CHARS.
    """
    try:
        _ensure_parent(MEMORY_PATH)
        ts = datetime.now().isoformat(timespec="seconds")

        # Read existing
        current = load_memory(max_chars=MEMORY_MAX_CHARS)
        new_entry = f"\n[{ts}] U: {user_text}\n[{ts}] W: {short_reply}\n"

        combined = (current + new_entry)
        combined = combined[-MEMORY_MAX_CHARS:] if len(combined) > MEMORY_MAX_CHARS else combined

        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            f.write(combined)

    except Exception:
        logging.exception("Failed updating memory file")


def shorten(text: str, max_chars: int = 150) -> str:
    """
    Deterministic <= max_chars truncation with ellipsis.
    """
    if not text:
        return ""
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    cut = max_chars - 1
    if cut <= 0:
        return "…"
    return text[:cut].rstrip(" ,.;:-") + "…"
