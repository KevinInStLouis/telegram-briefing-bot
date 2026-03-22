# llm.py
import os
import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "smollm2:135m-instruct-Q4_K_S")

MAX_PROMPT_CHARS = 800

async def generate(prompt: str, *, model: str | None = None) -> str:
        # ---- hard safety cap on prompt size ----
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = prompt[-MAX_PROMPT_CHARS:]

    payload = {
        "model": model or OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=360) as client:
        r = await client.post(OLLAMA_URL, json=payload)
        r.raise_for_status()
        data = r.json()

    return (data.get("response") or "").strip()

