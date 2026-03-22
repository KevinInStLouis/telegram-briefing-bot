# llm_interpreter.py
from __future__ import annotations

import os
import logging
from datetime import date, datetime
from memory_store import append_debug, update_memory, shorten
from watson import watson_chat_reply

# where we store the full llm output
THOUGHT_LOG_PATH = os.path.expanduser("~/alfred/watson_thoughts.txt")
DEBUG_LOG_PATH = os.path.expanduser("~/alfred/memory/watson_memory.txt")

# helpers

MEMORY_MAX_CHARS = 1000 # adjust from 1500 to 3000 chat recommends

def _ensure_parent(path: str) -> None:
	os.makedirs(os.path.dirname(path), exist_ok=True)

def _append_file(path: str, text: str) -> None:
	try:
		_ensure_parent(path)
		with open(path, "a", encoding="utf-8") as f:
			f.write(text)
	except Exception:
		logging.exception("Failed writing %s", path)

def _write_file(path: str, text: str) -> None:
	try:
		_ensure_parent(path)
		with open(path, "w", encoding="utf-8") as f:
			f.write(text)
	except Exception:
		logging.exception("Failed writing %s", path)

def _update_memory(new_entry: str) -> None:
	"""
	Append an entry to memroy, then hard-trim to last MEMORY_MAX_CHARS.
	"""
	current = _read_file(MEMORY_PATH)
	combined = (current + new_entry)
	if len(combined) > MEMORY_MAX_CHARS:
		combined = combined[-MEMORY_MAX_CHARS:]
	_write_file(MEMORY_PATH, combined)

def _append_to_thought_log(text: str) -> None:
	"""
	Append full Watson output to a text file with at imestamp.
	Never raises -- failures are logged only.
	"""
	try:
		os.makedirs(os.path.dirname(THOUGHT_LOG_PATH), exist_ok=True)
		with open(THOUGHT_LOG_PATH, "a", encoding="utf-8") as f:
			ts = datetime.now().isoformat(timespec="seconds")
			f.write(f"\n[{ts}]\n{text}\n")
	except Exception:
		logging.exception("Failed to write to watson_thoughts.txt")

def _shorten(text: str, max_chars: int = 200)-> str:
	"""
	Return <= max_chars. Adds ellipsis if truncated.
	Deterministic and safe for Telegram.
	"""
	if not text:
		return ""

	text = " ".join(text.split()) # normalize whitespace

	if len(text) <= max_chars:
		return text

	cut = max_chars -1
	if cut <= 0:
		return "..."

	return text[:cut].rstrip(",.;:-") + "..."

def load_memory(max_chars: int = MEMORY_MAX_CHARS) -> str:
	"""
	Watson-facing memory: last max_chars of the memory file.
	You will call this from watson.py to inject context.
	"""
	data = _read_file(MEMORY_PATH)
	return data[-max_chars:] if len(data) > max_chars else data


#  ---- public API -----

async def telegram_message(user_text: str, *, today: date | None = None) -> str:
	"""
	1. Calls watson_chat_reply (full response)
	- Writes full response to DEBUG log (posterity)
	- writes a curated entry to Watson memory (rolling)
	- returns <= chars to Telegram
	2. Appends the full response to watson_thoughts.txt
	3. Returns only the first 100 characters fro Telegram
	"""
	today = today or date.today()
	

	full_reply = await watson_chat_reply(user_text, today=today)

	# store the full reasoning for future prompts or inspection

	# 2 ) Wtson memory (fed back next time keep compact
	# store only the short outgoing message plus user input to keep tight
	short = shorten(full_reply, max_chars=225)
	append_debug(user_text, full_reply)
	update_memory(user_text, short)

	# What Telegram actually receives
	return short
