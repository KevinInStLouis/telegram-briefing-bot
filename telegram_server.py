#!/usr/bin/env python3
"""
telegram_server.py
Deterministic fixed-interval Telegram loop:
- every N seconds:
  - getUpdates(offset=last_update_id+1)
  - append raw messages to an inbox log
  - for each new message:
      - build prompt = SYSTEM_PROMPT + rolling memory + user msg (capped)
      - call local LLM
      - append response to posterity log
      - update rolling memory (<= max chars)
      - send reply (optionally truncated)
  - persist last_update_id durably
Resilient to transient Telegram/network errors; never crashes the loop.
"""

import os
import json
import time
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

# ---- your existing modules ----
try:
    from system_prompt import SYSTEM_PROMPT
except Exception:
    SYSTEM_PROMPT = "You are Watson."

# llm.generate can be sync or async; we handle both.
try:
    import llm
except Exception as e:
    llm = None


# ---------- config ----------
def env_int(name: str, default: int) -> int:
    v = os.environ.get(name, "").strip()
    if not v:
        return default
    try:
        return int(v)
    except ValueError:
        return default


@dataclass
class Config:
    token: str
    check_interval: int
    state_path: str
    raw_inbox_log: str
    posterity_log: str
    rolling_memory_path: str
    rolling_memory_max_chars: int
    prompt_max_chars: int
    reply_max_chars: int


def load_config() -> Config:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN in environment/.env")

    return Config(
        token=token,
        check_interval=env_int("CHECK_INTERVAL_SECONDS", 300),
        state_path=os.environ.get("STATE_PATH", "./telegram_state.json"),
        raw_inbox_log=os.environ.get("RAW_INBOX_LOG", "./telegram_inbox_raw.log"),
        posterity_log=os.environ.get("POSTERITY_LOG", "./posterity.log"),
        rolling_memory_path=os.environ.get("ROLLING_MEMORY_PATH", "./rolling_memory.txt"),
        rolling_memory_max_chars=env_int("ROLLING_MEMORY_MAX_CHARS", 1000),
        prompt_max_chars=env_int("PROMPT_MAX_CHARS", 3500),
        reply_max_chars=env_int("REPLY_MAX_CHARS", 100),
    )


# ---------- state ----------
def load_state(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_update_id": None}
    except Exception:
        # corrupted state: keep running, but don't spam old messages forever
        return {"last_update_id": None}


def save_state(path: str, state: Dict[str, Any]) -> None:
    tmp = path + ".tmp"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)
    os.replace(tmp, path)


# ---------- logging ----------
def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_line(path: str, line: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line.rstrip("\n") + "\n")


def posterity(cfg: Config, text: str) -> None:
    append_line(cfg.posterity_log, f"[{now_utc_iso()}] {text}")


def log_raw_message(cfg: Config, meta: Dict[str, Any], text: str) -> None:
    # plain-text append-only log, minimal metadata
    line = json.dumps(
        {
            "ts": now_utc_iso(),
            "chat_id": meta.get("chat_id"),
            "message_id": meta.get("message_id"),
            "date": meta.get("date"),
            "from_id": meta.get("from_id"),
            "from_username": meta.get("from_username"),
            "text": text,
        },
        ensure_ascii=False,
    )
    append_line(cfg.raw_inbox_log, line)


# ---------- rolling memory ----------
def load_rolling_memory(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""
    except Exception:
        return ""


def save_rolling_memory(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def update_rolling_memory(cfg: Config, user_text: str, assistant_text: str) -> None:
    mem = load_rolling_memory(cfg.rolling_memory_path).strip()
    # keep compact; don’t store huge blobs
    u = user_text.strip().replace("\n", " ")
    a = assistant_text.strip().replace("\n", " ")

    # clip per-entry to avoid memory being dominated by one message
    u = u[:300]
    a = a[:300]

    entry = f"U:{u}\nA:{a}\n"
    combined = (mem + "\n" + entry).strip() if mem else entry.strip()

    # enforce max chars by keeping the *most recent* tail
    if len(combined) > cfg.rolling_memory_max_chars:
        combined = combined[-cfg.rolling_memory_max_chars :]

    save_rolling_memory(cfg.rolling_memory_path, combined)


# ---------- prompt building ----------
def build_prompt(cfg: Config, user_text: str) -> str:
    mem = load_rolling_memory(cfg.rolling_memory_path).strip()
    user_text = user_text.strip()

    # keep prompt short and stable
    parts = []
    parts.append(SYSTEM_PROMPT.strip())
    if mem:
        parts.append("Memory:\n" + mem)
    parts.append("User:\n" + user_text)
    parts.append("Assistant:")

    prompt = "\n\n".join(parts)

    if len(prompt) > cfg.prompt_max_chars:
        # trim memory first; keep system + user intact as much as possible
        budget = cfg.prompt_max_chars
        sys_part = SYSTEM_PROMPT.strip()
        user_part = f"User:\n{user_text}\n\nAssistant:"
        # leftover budget for memory block (and separators)
        overhead = len(sys_part) + 4 + len(user_part)
        mem_budget = max(0, budget - overhead)
        mem_trim = mem[-mem_budget:] if mem_budget and mem else ""
        prompt = "\n\n".join([sys_part, ("Memory:\n" + mem_trim) if mem_trim else "", user_part]).strip()

    return prompt


# ---------- LLM call (sync or async) ----------
async def _call_llm_async(prompt: str) -> str:
    # If llm.generate is async, await it; else run sync in thread.
    gen = getattr(llm, "generate", None)
    if gen is None:
        return "(LLM module not available.)"

    if asyncio.iscoroutinefunction(gen):
        return (await gen(prompt)).strip()

    # run sync generate without blocking event loop too much
    return (await asyncio.to_thread(gen, prompt)).strip()


def call_llm(prompt: str) -> str:
    # single call wrapper; safe regardless of sync/async llm.generate
    try:
        return asyncio.run(_call_llm_async(prompt))
    except RuntimeError:
        # already in an event loop (rare here); fallback:
        return "(LLM runtime loop error.)"
    except Exception as e:
        return f"(LLM error: {e})"


# ---------- Telegram API ----------
TELEGRAM_BASE = "https://api.telegram.org"


def tg_url(token: str, method: str) -> str:
    return f"{TELEGRAM_BASE}/bot{token}/{method}"


def get_updates(
    client: httpx.Client,
    cfg: Config,
    offset: Optional[int],
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {"timeout": 0, "limit": 100}
    if offset is not None:
        params["offset"] = offset

    r = client.get(tg_url(cfg.token, "getUpdates"), params=params)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram getUpdates not ok: {data}")
    return data.get("result", [])


def send_message(client: httpx.Client, cfg: Config, chat_id: int, text: str) -> None:
    payload = {"chat_id": chat_id, "text": text}
    r = client.post(tg_url(cfg.token, "sendMessage"), json=payload)
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram sendMessage not ok: {data}")


def extract_message(update: Dict[str, Any]) -> Optional[Tuple[Dict[str, Any], str]]:
    """
    Returns (meta, text) for normal message updates; ignore non-text.
    """
    msg = update.get("message")
    if not msg:
        return None

    text = msg.get("text")
    if not text:
        return None

    chat = msg.get("chat") or {}
    frm = msg.get("from") or {}

    meta = {
        "chat_id": chat.get("id"),
        "message_id": msg.get("message_id"),
        "date": msg.get("date"),
        "from_id": frm.get("id"),
        "from_username": frm.get("username"),
        "update_id": update.get("update_id"),
    }
    return meta, text


# ---------- main loop ----------
def run_loop(cfg: Config) -> None:
    state = load_state(cfg.state_path)
    last_update_id = state.get("last_update_id", None)

    posterity(cfg, "telegram_server starting")
    posterity(cfg, f"state_path={cfg.state_path} last_update_id={last_update_id}")

    timeout = httpx.Timeout(connect=10.0, read=20.0, write=20.0, pool=20.0)

    while True:
        cycle_started = now_utc_iso()
        max_update_id_this_cycle: Optional[int] = None

        try:
            with httpx.Client(timeout=timeout) as client:
                offset = (last_update_id + 1) if isinstance(last_update_id, int) else None

                updates = get_updates(client, cfg, offset=offset)

                if updates:
                    posterity(cfg, f"cycle {cycle_started}: got {len(updates)} update(s)")

                for upd in updates:
                    upd_id = upd.get("update_id")
                    if isinstance(upd_id, int):
                        max_update_id_this_cycle = (
                            upd_id if max_update_id_this_cycle is None else max(max_update_id_this_cycle, upd_id)
                        )

                    extracted = extract_message(upd)
                    if not extracted:
                        continue

                    meta, text = extracted
                    chat_id = meta.get("chat_id")
                    if not isinstance(chat_id, int):
                        continue

                    # 1) persist raw message
                    log_raw_message(cfg, meta, text)

                    # 2) build prompt + call LLM
                    prompt = build_prompt(cfg, text)
                    resp = call_llm(prompt)

                    posterity(cfg, f"chat_id={chat_id} msg_id={meta.get('message_id')} U={text!r}")
                    posterity(cfg, f"chat_id={chat_id} A={resp!r}")

                    # 3) update rolling memory
                    update_rolling_memory(cfg, text, resp)

                    # 4) send reply (truncate if requested)
                    reply = resp.strip()
                    if cfg.reply_max_chars > 0 and len(reply) > cfg.reply_max_chars:
                        reply = reply[: cfg.reply_max_chars].rstrip() + "…"

                    try:
                        send_message(client, cfg, chat_id=chat_id, text=reply or "(empty)")
                    except Exception as e:
                        posterity(cfg, f"sendMessage error: {e}")

                # 5) commit cursor *after* processing batch
                if isinstance(max_update_id_this_cycle, int):
                    last_update_id = max_update_id_this_cycle
                    save_state(cfg.state_path, {"last_update_id": last_update_id})
                    posterity(cfg, f"cycle {cycle_started}: saved last_update_id={last_update_id}")

        except (httpx.TimeoutException, httpx.HTTPError) as e:
            # transient net / Telegram failure -> log and retry next cycle
            posterity(cfg, f"cycle {cycle_started}: http error: {e}")
        except Exception as e:
            # never crash the loop
            posterity(cfg, f"cycle {cycle_started}: unexpected error: {e}")

        time.sleep(max(1, cfg.check_interval))


def main() -> None:
    cfg = load_config()
    run_loop(cfg)


if __name__ == "__main__":
    main()
