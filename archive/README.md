# Quarantine notes

The new scalable core is under `alfred/`.

Keep using:

- `alfred/main.py`
- `alfred/telegram/receiver.py`
- `alfred/telegram/sender.py`
- `alfred/brain/worker.py`
- `alfred/brain/watson.py`
- `alfred/llm/ollama.py`
- `alfred/storage/*`

The old root-level files are retained for reference until the new path is fully validated on the Raspberry Pi:

- `telegram_pump.py` mixed receiving and sending.
- `telegram_bot.py` mixed chat processing with broken hourly briefing logic.
- `telegram_store.py` was a JSON/JSONL prototype store.
- `daily_brief.py` and `cron_daily_brief.py` used imports that did not match the repository layout.
- `app.py` was a Flask hello-world remnant.
- `dashboard/` and related TypeScript files are a separate Val Town/React experiment.

Do not add new work to the old files. Port useful behavior into the package under `alfred/`, then delete or physically move the old files once the package is live.
