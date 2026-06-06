# display_state.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


DISPLAY_LIMITS = {
    "time": 16,
    "status": 16,
    "source": 16,
    "title": 32,
    "line1": 48,
    "line2": 48,
    "line3": 48,
}


@dataclass(frozen=True)
class StevensDisplayState:
    """Compact Pi-to-Pico display contract.

    The Pico should receive status frames, not raw memories, Telegram data,
    JSON, weather payloads, or LLM output.
    """

    time: str
    status: str
    source: str
    title: str
    line1: str
    line2: str = ""
    line3: str = ""
    has_alert: int = 0


def _clean(value: object, limit: int) -> str:
    text = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())
    text = text.encode("ascii", "replace").decode("ascii")
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3].rstrip() + "..."


def current_display_time(now: datetime | None = None) -> str:
    now = now or datetime.now()
    return now.strftime("%-I:%M %p")


def normalize_display_state(state: StevensDisplayState) -> StevensDisplayState:
    return StevensDisplayState(
        time=_clean(state.time, DISPLAY_LIMITS["time"]),
        status=_clean(state.status, DISPLAY_LIMITS["status"]),
        source=_clean(state.source, DISPLAY_LIMITS["source"]),
        title=_clean(state.title, DISPLAY_LIMITS["title"]),
        line1=_clean(state.line1, DISPLAY_LIMITS["line1"]),
        line2=_clean(state.line2, DISPLAY_LIMITS["line2"]),
        line3=_clean(state.line3, DISPLAY_LIMITS["line3"]),
        has_alert=1 if state.has_alert else 0,
    )


def encode_display_state(state: StevensDisplayState) -> str:
    """Encode one Stevens display frame using the agreed line protocol."""
    state = normalize_display_state(state)
    return "\n".join(
        [
            "VERSION=1",
            f"TIME={state.time}",
            f"STATUS={state.status}",
            f"SOURCE={state.source}",
            f"TITLE={state.title}",
            f"LINE1={state.line1}",
            f"LINE2={state.line2}",
            f"LINE3={state.line3}",
            f"ALERT={state.has_alert}",
            "END",
            "",
        ]
    )


def status_state(
    *,
    line1: str,
    line2: str = "",
    line3: str = "",
    source: str = "system",
    status: str = "OK",
    title: str = "Stevens",
    has_alert: bool = False,
    now: datetime | None = None,
) -> StevensDisplayState:
    return StevensDisplayState(
        time=current_display_time(now),
        status=status,
        source=source,
        title=title,
        line1=line1,
        line2=line2,
        line3=line3,
        has_alert=1 if has_alert else 0,
    )


def memory_saved_state(memory_text: str, *, now: datetime | None = None) -> StevensDisplayState:
    return status_state(
        source="notebook",
        line1="Memory saved",
        line2=memory_text,
        line3="Awaiting orders",
        now=now,
    )
