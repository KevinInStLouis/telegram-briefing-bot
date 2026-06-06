# display_sender.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from display_state import StevensDisplayState, encode_display_state


DEFAULT_DISPLAY_DEVICE = "/dev/ttyACM0"


@dataclass(frozen=True)
class DisplaySendResult:
    ok: bool
    target: str
    frame_path: str | None = None
    error: str | None = None


def _base_dir() -> Path:
    return Path(os.path.expanduser(os.getenv("BOT_BASE_DIR", os.getcwd())))


def _spool_path() -> Path:
    return _base_dir() / "data" / "last_display_frame.txt"


def _write_spool(frame: str) -> Path:
    path = _spool_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frame, encoding="ascii")
    return path


def send_display_frame(
    frame: str,
    *,
    device: str | None = None,
    spool_on_failure: bool = True,
) -> DisplaySendResult:
    """Write an encoded display frame to the Pico serial device.

    The frame is always ASCII. If the Pico is not attached, the frame is
    written to data/last_display_frame.txt so Telegram commands can still
    complete without losing the intended display state.
    """
    device = device or os.getenv("STEVENS_DISPLAY_DEVICE", DEFAULT_DISPLAY_DEVICE)
    dry_run = os.getenv("STEVENS_DISPLAY_DRY_RUN", "").lower() in {"1", "true", "yes"}

    if dry_run:
        path = _write_spool(frame)
        return DisplaySendResult(ok=True, target="spool", frame_path=str(path))

    try:
        with open(device, "wb", buffering=0) as f:
            f.write(frame.encode("ascii", "replace"))
        return DisplaySendResult(ok=True, target=device)
    except Exception as exc:
        if not spool_on_failure:
            return DisplaySendResult(ok=False, target=device, error=str(exc))
        path = _write_spool(frame)
        return DisplaySendResult(
            ok=False,
            target=device,
            frame_path=str(path),
            error=str(exc),
        )


def send_display_state(
    state: StevensDisplayState,
    *,
    device: str | None = None,
    spool_on_failure: bool = True,
) -> DisplaySendResult:
    return send_display_frame(
        encode_display_state(state),
        device=device,
        spool_on_failure=spool_on_failure,
    )
