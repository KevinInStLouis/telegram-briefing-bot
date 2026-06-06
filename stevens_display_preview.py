# stevens_display_preview.py
from __future__ import annotations

import os
from pathlib import Path

from display_parser import parse_display_frame, render_display_preview


def default_frame_path() -> Path:
    base_dir = Path(os.path.expanduser(os.getenv("BOT_BASE_DIR", os.getcwd())))
    return base_dir / "data" / "last_display_frame.txt"


def main() -> None:
    path = default_frame_path()
    if not path.exists():
        raise SystemExit(f"No display frame found at {path}. Run stevens_display_status.py first.")

    frame = path.read_text(encoding="ascii")
    parsed = parse_display_frame(frame)
    print(render_display_preview(parsed.state))


if __name__ == "__main__":
    main()
