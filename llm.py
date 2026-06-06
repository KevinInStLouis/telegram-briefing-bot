# llm.py
from __future__ import annotations

import os

import httpx

from stevens_env import load_stevens_env


load_stevens_env()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "smollm2:135m-instruct-Q4_K_S")
MAX_PROMPT_CHARS = int(os.getenv("LLM_MAX_PROMPT_CHARS", "800"))
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "360"))


async def generate(prompt: str, *, model: str | None = None) -> str:
    # Hard safety cap on prompt size. Keep this small for Pi Zero class hardware.
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = prompt[-MAX_PROMPT_CHARS:]

    payload = {
        "model": model or OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT_SECONDS) as client:
        r = await client.post(OLLAMA_URL, json=payload)
        r.raise_for_status()
        data = r.json()

    return (data.get("response") or "").strip()
