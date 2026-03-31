from __future__ import annotations

import json
import platform
import sys

from .. import stores
from ..commands import PORTED_COMMANDS, find_commands


def handle_help(prompt: str) -> str:
    prompt_stripped = prompt.strip()

    # If a specific command name is given, show detailed info
    if prompt_stripped:
        matches = find_commands(prompt_stripped, limit=1)
        if matches:
            cmd = matches[0]
            return (
                f"/{cmd.name}\n"
                f"  Responsibility: {cmd.responsibility}\n"
                f"  Source: {cmd.source_hint}\n"
                f"  Status: {cmd.status}"
            )
        return f"No command found matching: {prompt_stripped}"

    # Group commands by source_hint prefix
    groups: dict[str, list[str]] = {}
    for cmd in PORTED_COMMANDS:
        # Use the first path segment of source_hint as group key
        parts = cmd.source_hint.split("/")
        group_key = parts[0] if parts else "other"
        groups.setdefault(group_key, []).append(f"  /{cmd.name} — {cmd.responsibility}")

    lines = [f"claw-code — {len(PORTED_COMMANDS)} commands available", ""]
    for group, entries in sorted(groups.items()):
        lines.append(f"[{group}]")
        lines.extend(entries)
        lines.append("")

    lines.append("Use '/help <command>' for details on a specific command.")
    return "\n".join(lines)


def handle_version(prompt: str) -> str:
    return (
        f"claw-code v0.1.0\n"
        f"Python {sys.version}\n"
        f"Platform: {platform.platform()}"
    )


def handle_clear(prompt: str) -> str:
    return "Conversation cleared. Starting fresh context."


def handle_compact(prompt: str) -> str:
    return "Conversation compacted. Older messages summarized."


def handle_status(prompt: str) -> str:
    lines = [
        f"Platform: {platform.platform()}",
        f"Python: {sys.version.split()[0]}",
        f"Plan mode: {stores.get_mode_flag('plan_mode')}",
        f"Worktree mode: {stores.get_mode_flag('worktree_mode')}",
        f"Active tasks: {len(stores.list_tasks())}",
        f"Active agents: {len(stores.list_agents())}",
    ]
    return "\n".join(lines)


def handle_cost(prompt: str) -> str:
    return (
        "Usage tracking: word-count approximation (no real token billing in port).\n"
        "No cost data available."
    )
