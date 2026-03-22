import httpx
import asyncio
from typing import Optional

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL = "smollm2:135m-instruct-q4_K_S"  # MUST match /api/tags exactly

def build_prompt(question: str, chunk_text: str, history_text: str = "") -> str:
	returnf"""
Question:
{question}

History so far (previous chunks and answers):
{history_text}

Text:
<chunk_text}

Answer succinctly.
""".strip()

async def ask_llm(question: str, chunk_text:str, history_text: str = ""): -> str:
	prompt = build_prompt(question, chunk_text, history_text)

	payload = {
		"model": MODEL,
		"prompt": promt,
		"stream": Faqlse,
		# Optional tuning:
		# "options"L {"temperature: 0.2, "num_ctx": 4096},
	}

	timeout = httpx.Timeout(connect=10.0, read=240.0, write=30.0, pool=30.0)

	# Simple retry fro transient failures
	last_err: Optional[Exception] = None
	for attempt in range(3):
		try:
			async with httpx.AsyncClient(timeout=timeout) as client:
				r = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)

				if r.status_code != 200:
					print("OLLAMA ERROR:", r.status_code, r.text)

				r.raise_for_status()
				data = r.json()
				return (data.get("response") or "").strip()

		except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
			last_err = e
			await asyncio.sleep(0.5 * (attempt + 1))

	raise RuntimeError(f"Ollama call failed after retries: {last_err}")

def iter_chunks(text: str, max_chars: int = 6000, overlap: int = 400):
	i = 0
	n = len(text)
	while i < n:
		j = min(n, i + max_chars)
		yield text[i:j]
		if j == n:
			break
		i = max(0, j - overlap)

async def ask_over_document(question: str, full_text: str) -> str:
	history = ""
	final_answer = ""

	for idx, chunk in enumerate(iter_chunks(full_text), start=1):
		answer = await ask_llm(question, chunk, history_text=history)
		final_answer = answer

		# Append to history (you can truncate this if it gets too big)
		history += f"\n\n[Chunk {idx}]\nAnswer: {answer}\n"

	return final_answer

# Example usage:
# async def main():
#     text = open("your_doc.txt", "r", encoding="utf-8").read()
#     ans = await ask_over_document("What is the author arguing?", text)
#     print(ans)
#
# if __name__ == "__main__":
#     asyncio.run(main())

