# stevens_env.py
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


ENV_PATH_VAR = "STEVENS_ENV_PATH"
_LOADED = False
_LOADED_PATH: Path | None = None


def _candidate_paths() -> list[Path]:
    explicit = os.getenv(ENV_PATH_VAR)
    if explicit:
        return [Path(explicit).expanduser()]

    candidates: list[Path] = []

    bot_base_dir = os.getenv("BOT_BASE_DIR")
    if bot_base_dir:
        candidates.append(Path(bot_base_dir).expanduser() / ".env")

    candidates.append(Path.cwd() / ".env")
    candidates.append(Path.cwd() / "stevens.env")
    return candidates


def find_env_file() -> Path | None:
    for path in _candidate_paths():
        if path.exists():
            return path
    return None


def load_stevens_env(*, required: bool = False, override: bool = False) -> Path | None:
    """Load Stevens configuration from one env file.

    Set STEVENS_ENV_PATH=/path/to/.env to choose the file explicitly.
    Otherwise Stevens tries BOT_BASE_DIR/.env, then ./.env, then ./stevens.env.
    """
    global _LOADED, _LOADED_PATH

    if _LOADED and not override:
        return _LOADED_PATH

    path = find_env_file()
    if path is None:
        if required:
            raise RuntimeError(
                "No Stevens env file found. Set STEVENS_ENV_PATH=/path/to/.env "
                "or create .env in the repository/BOT_BASE_DIR."
            )
        _LOADED = True
        _LOADED_PATH = None
        return None

    load_dotenv(dotenv_path=path, override=override)
    _LOADED = True
    _LOADED_PATH = path
    return path


def require_env(name: str) -> str:
    load_stevens_env(required=True)
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


def optional_env(name: str, default: str | None = None) -> str | None:
    load_stevens_env(required=False)
    return os.getenv(name, default)
