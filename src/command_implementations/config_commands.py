from __future__ import annotations

import dataclasses
import json

from .. import stores
from ..commands import PORTED_COMMANDS


def handle_config_command(prompt: str) -> str:
    from ..tool_implementations.config_tool import handle_config

    prompt_stripped = prompt.strip()

    if "=" in prompt_stripped:
        key, _, value = prompt_stripped.partition("=")
        return handle_config(json.dumps({
            "action": "set",
            "key": key.strip(),
            "value": value.strip(),
        }))

    if prompt_stripped:
        return handle_config(json.dumps({
            "action": "get",
            "key": prompt_stripped,
        }))

    return handle_config('{"action": "list"}')


def handle_permissions(prompt: str) -> str:
    return (
        "Permission model: deny-list based (ToolPermissionContext).\n"
        "Configure via: --deny-tool <name> --deny-prefix <prefix>\n"
        "Bash is automatically gated unless explicitly routed."
    )


def handle_hooks(prompt: str) -> str:
    return (
        "No hooks configured.\n"
        "Hooks can be configured in CLAUDE.md or via session setup."
    )


def handle_skills(prompt: str) -> str:
    skills = [m for m in PORTED_COMMANDS if "skills" in m.source_hint.lower()]
    if not skills:
        return "No skills registered."
    lines = ["Available skills:"]
    for s in skills:
        lines.append(f"  /{s.name} — {s.responsibility}")
    return "\n".join(lines)


def handle_mcp(prompt: str) -> str:
    return (
        "MCP (Model Context Protocol) server management.\n"
        "This port does not include a live MCP client.\n"
        "MCP tool stubs are available in the tool inventory."
    )


def handle_tasks(prompt: str) -> str:
    tasks = stores.list_tasks()
    if not tasks:
        return "No tasks."
    return json.dumps([dataclasses.asdict(t) for t in tasks], indent=2)
