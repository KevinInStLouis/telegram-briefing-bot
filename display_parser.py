# display_parser.py
from __future__ import annotations

from dataclasses import dataclass

from display_state import StevensDisplayState, normalize_display_state


REQUIRED_KEYS = {
    "VERSION",
    "TIME",
    "STATUS",
    "SOURCE",
    "TITLE",
    "LINE1",
    "LINE2",
    "LINE3",
    "ALERT",
}


class DisplayFrameError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedDisplayFrame:
    version: int
    state: StevensDisplayState


def parse_display_frame(frame: str) -> ParsedDisplayFrame:
    """Parse the compact Stevens line protocol.

    This is the receive-side contract the Pico firmware should mirror. It is
    intentionally strict so bad frames are caught before hardware debugging.
    """
    values: dict[str, str] = {}
    saw_end = False

    for raw_line in frame.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "END":
            saw_end = True
            break
        if "=" not in line:
            raise DisplayFrameError(f"invalid display frame line: {line!r}")
        key, value = line.split("=", 1)
        key = key.strip().upper()
        if key in values:
            raise DisplayFrameError(f"duplicate display frame key: {key}")
        values[key] = value.strip()

    if not saw_end:
        raise DisplayFrameError("display frame is missing END")

    missing = REQUIRED_KEYS - set(values)
    if missing:
        raise DisplayFrameError(f"display frame missing keys: {', '.join(sorted(missing))}")

    try:
        version = int(values["VERSION"])
    except ValueError as exc:
        raise DisplayFrameError("VERSION must be an integer") from exc

    if version != 1:
        raise DisplayFrameError(f"unsupported display frame version: {version}")

    try:
        has_alert = int(values["ALERT"])
    except ValueError as exc:
        raise DisplayFrameError("ALERT must be 0 or 1") from exc

    if has_alert not in {0, 1}:
        raise DisplayFrameError("ALERT must be 0 or 1")

    state = normalize_display_state(
        StevensDisplayState(
            time=values["TIME"],
            status=values["STATUS"],
            source=values["SOURCE"],
            title=values["TITLE"],
            line1=values["LINE1"],
            line2=values["LINE2"],
            line3=values["LINE3"],
            has_alert=has_alert,
        )
    )
    return ParsedDisplayFrame(version=version, state=state)


def render_display_preview(state: StevensDisplayState) -> str:
    """Render a small terminal preview of what the LCD status screen should show."""
    state = normalize_display_state(state)
    alert = " ALERT" if state.has_alert else ""
    rows = [
        f"{state.title:<20} {state.status}{alert}",
        f"{state.source}",
        "-" * 32,
        state.line1,
        state.line2,
        state.line3,
        "-" * 32,
        state.time,
    ]
    return "\n".join(rows)
