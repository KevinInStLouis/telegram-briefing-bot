# stevens_import_weather.py
from __future__ import annotations

from display_sender import send_display_state
from display_state import status_state
from weather_importer import import_weather_memory


def main() -> None:
    memory = import_weather_memory()
    print(f"Imported weather memory: {memory.id}")
    print(memory.text)

    result = send_display_state(
        status_state(
            source="weather",
            line1="Weather imported",
            line2=memory.text,
            line3=memory.date or memory.id,
        )
    )
    if result.ok:
        print(f"display ok: {result.target}")
    else:
        print(f"display failed: {result.target}: {result.error}")
        if result.frame_path:
            print(f"frame saved: {result.frame_path}")


if __name__ == "__main__":
    main()
