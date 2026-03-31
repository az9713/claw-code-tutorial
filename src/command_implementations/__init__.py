from __future__ import annotations

# Command handler dispatch table.
# Handlers for specific commands are imported and registered here.
# Returns None for commands that have no explicit implementation yet,
# causing the caller to fall back to the default mirrored-command message.

from .config_commands import (
    handle_config_command,
    handle_hooks,
    handle_mcp,
    handle_permissions,
    handle_skills,
    handle_tasks,
)
from .core_commands import (
    handle_clear,
    handle_compact,
    handle_cost,
    handle_help,
    handle_status,
    handle_version,
)
from .session_commands import (
    handle_doctor,
    handle_memory,
    handle_model,
    handle_session,
    handle_summary,
)

COMMAND_DISPATCH: dict[str, object] = {
    "help": handle_help,
    "version": handle_version,
    "clear": handle_clear,
    "compact": handle_compact,
    "status": handle_status,
    "cost": handle_cost,
    "model": handle_model,
    "memory": handle_memory,
    "session": handle_session,
    "summary": handle_summary,
    "doctor": handle_doctor,
    "config": handle_config_command,
    "permissions": handle_permissions,
    "hooks": handle_hooks,
    "skills": handle_skills,
    "mcp": handle_mcp,
    "tasks": handle_tasks,
}


def dispatch_command(name: str, prompt: str) -> str | None:
    """Look up and invoke a handler by command name. Returns None if no handler registered."""
    handler = COMMAND_DISPATCH.get(name)
    if handler is None:
        return None
    return handler(prompt)  # type: ignore[operator]
