# stevens_display_status.py
from __future__ import annotations

from display_sender import send_display_state
from display_state import status_state
from memories import list_memories


def main() -> None:
    memories = list_memories(limit=1)
    if memories:
        memory = memories[0]
        state = status_state(
            source="notebook",
            line1="Recent memory",
            line2=memory.text,
            line3=memory.id,
        )
    else:
        state = status_state(
            source="system",
            line1="Stevens online",
            line2="Display link ready",
            line3="Awaiting orders",
        )

    result = send_display_state(state)
    if result.ok:
        print(f"display ok: {result.target}")
    else:
        print(f"display failed: {result.target}: {result.error}")
        if result.frame_path:
            print(f"frame saved: {result.frame_path}")


if __name__ == "__main__":
    main()
