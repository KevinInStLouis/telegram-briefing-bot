# Alfred Telegram Bot

A local, queue-based Telegram assistant backed by Ollama.

This repository now has an explicit scalable architecture:

```text
Telegram API
  -> alfred.telegram.receiver
  -> SQLite inbox queue
  -> alfred.brain.worker
  -> SQLite outbox queue
  -> alfred.telegram.sender
  -> Telegram API
```

The supervisor entrypoint is:

```bash
python -m alfred.main
```

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/init_db.py
```

Edit `.env`, then run:

```bash
python -m alfred.main
```

## Services

The components can also be run separately:

```bash
python -m alfred.telegram.receiver
python -m alfred.brain.worker
python -m alfred.telegram.sender
```

## Storage

Runtime state is stored in SQLite, defaulting to:

```text
./alfred.db
```

Set `BOT_DB_PATH` to place the database elsewhere.

Important tables:

- `bot_state` stores Telegram offsets and worker state.
- `telegram_inbox` stores inbound Telegram messages.
- `telegram_outbox` stores outbound Telegram messages and retry state.
- `memories` is reserved for long-term memory.
- `workflow_runs` is reserved for scheduled workflows.

## Current quarantine

The old root-level scripts and dashboard experiment are retained for reference, but the new architecture lives under `alfred/`. See `archive/README.md` for the quarantine rationale.
