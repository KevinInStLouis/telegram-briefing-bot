# telegram_commands.py
from __future__ import annotations

from dataclasses import dataclass

from memories import (
    create_memory,
    delete_memory,
    format_memory_for_telegram,
    list_memories,
)


@dataclass(frozen=True)
class CommandResult:
    handled: bool
    text: str
    kind: str = "command_reply"


HELP_TEXT = """At your service. Current commands:
/start - introduce Stevens
/ping - confirm the bot is awake
/remember <text> - save a memory
/memories [limit] - show recent memories
/forget <id> - delete a memory
/display - report display status"""


def _split_command(message: str) -> tuple[str, str]:
    stripped = (message or "").strip()
    if not stripped.startswith("/"):
        return "", stripped

    first, _, rest = stripped.partition(" ")
    command = first.split("@", 1)[0].lower()
    return command, rest.strip()


def handle_telegram_command(message: str) -> CommandResult:
    """
    Handle Stevens' deterministic Telegram command layer.

    This is intentionally narrow. It proves Telegram -> SQLite -> Telegram
    before any local LLM behavior is reintroduced.
    """
    command, arg = _split_command(message)

    if not command:
        return CommandResult(
            handled=True,
            text=(
                "I am presently operating in command mode. "
                "Use /remember <text>, /memories, /forget <id>, or /ping."
            ),
        )

    if command in {"/start", "/help"}:
        return CommandResult(handled=True, text=HELP_TEXT)

    if command == "/ping":
        return CommandResult(handled=True, text="At your service.", kind="ping")

    if command == "/remember":
        if not arg:
            return CommandResult(
                handled=True,
                text="Please provide the memory text, for example: /remember The garage code is 1234.",
            )
        memory = create_memory(arg, created_by="telegram", tags="telegram")
        return CommandResult(
            handled=True,
            text=f"Memory saved.\n{format_memory_for_telegram(memory)}",
            kind="memory_saved",
        )

    if command == "/memories":
        limit = 10
        tag = None
        if arg:
            first = arg.split()[0]
            if first.isdigit():
                limit = max(1, min(int(first), 25))
            else:
                tag = first.lstrip("#")

        memories = list_memories(limit=limit, tag=tag)
        if not memories:
            if tag:
                return CommandResult(handled=True, text=f"No memories found for tag: {tag}")
            return CommandResult(handled=True, text="No memories recorded yet.")

        lines = ["Recent memories:"]
        for memory in memories:
            lines.append(format_memory_for_telegram(memory))
        return CommandResult(handled=True, text="\n\n".join(lines), kind="memories_listed")

    if command == "/forget":
        if not arg:
            return CommandResult(handled=True, text="Please provide a memory id, for example: /forget abc123")
        memory_id = arg.split()[0]
        deleted = delete_memory(memory_id)
        if deleted:
            return CommandResult(handled=True, text=f"Memory forgotten: {memory_id}", kind="memory_deleted")
        return CommandResult(handled=True, text=f"No memory found with id: {memory_id}")

    if command == "/display":
        return CommandResult(
            handled=True,
            text=(
                "Display command received. The Pico display sender is not wired into this slice yet. "
                "Current status: Stevens remembers and can report memories."
            ),
            kind="display_status",
        )

    return CommandResult(
        handled=True,
        text=f"Unknown command: {command}\n\n{HELP_TEXT}",
    )
