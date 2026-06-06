# telegram_commands.py
from __future__ import annotations

from dataclasses import dataclass

from display_sender import DisplaySendResult, send_display_state
from display_state import memory_saved_state, status_state
from memories import (
    Memory,
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
/display - refresh the Pico display"""


def _split_command(message: str) -> tuple[str, str]:
    stripped = (message or "").strip()
    if not stripped.startswith("/"):
        return "", stripped

    first, _, rest = stripped.partition(" ")
    command = first.split("@", 1)[0].lower()
    return command, rest.strip()


def _display_result_text(result: DisplaySendResult) -> str:
    if result.ok and result.target == "spool":
        return f"Display frame saved: {result.frame_path}"
    if result.ok:
        return f"Display refreshed: {result.target}"
    if result.frame_path:
        return f"Pico display not reachable; frame saved: {result.frame_path}"
    return f"Display refresh failed: {result.error or 'unknown error'}"


def _recent_memory_display_state(memory: Memory | None):
    if memory is None:
        return status_state(
            source="notebook",
            line1="No memories yet",
            line2="Use /remember <text>",
            line3="Awaiting orders",
        )

    return status_state(
        source="notebook",
        line1="Recent memory",
        line2=memory.text,
        line3=memory.id,
    )


def handle_telegram_command(message: str) -> CommandResult:
    """
    Handle Stevens' deterministic Telegram command layer.

    This is intentionally narrow. It proves Telegram -> SQLite -> Telegram
    and now Telegram -> compact display state before local LLM behavior is
    reintroduced.
    """
    command, arg = _split_command(message)

    if not command:
        return CommandResult(
            handled=True,
            text=(
                "I am presently operating in command mode. "
                "Use /remember <text>, /memories, /forget <id>, /display, or /ping."
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
        display_result = send_display_state(memory_saved_state(memory.text))
        return CommandResult(
            handled=True,
            text=(
                f"Memory saved.\n{format_memory_for_telegram(memory)}\n\n"
                f"{_display_result_text(display_result)}"
            ),
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
        memories = list_memories(limit=1)
        state = _recent_memory_display_state(memories[0] if memories else None)
        display_result = send_display_state(state)
        return CommandResult(
            handled=True,
            text=_display_result_text(display_result),
            kind="display_status",
        )

    return CommandResult(
        handled=True,
        text=f"Unknown command: {command}\n\n{HELP_TEXT}",
    )
