from __future__ import annotations

import json
import os
import subprocess

# Patterns that indicate destructive/dangerous commands
_BLOCKED_PATTERNS = [
    "rm -rf /",
    "rm -fr /",
    "mkfs",
    "dd if=/dev/",
    ":(){:|:&};:",
]

_MAX_OUTPUT = 100_000


def handle_bash_tool(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    command = params.get("command", "")
    if not command:
        return "Error: command is required"

    timeout_ms = int(params.get("timeout", 120_000))
    timeout_sec = timeout_ms / 1000.0

    # Security check: reject known destructive patterns
    for blocked in _BLOCKED_PATTERNS:
        if blocked in command:
            return f"Error: Command blocked for safety reasons (matched pattern: {blocked!r})"

    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            cwd=os.getcwd(),
        )
        output = proc.stdout
        if proc.stderr:
            output = output + proc.stderr if output else proc.stderr

        if len(output) > _MAX_OUTPUT:
            output = output[:_MAX_OUTPUT] + "\n[output truncated]"

        return output if output else ""

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout_sec:.0f}s"
    except PermissionError as exc:
        return f"Error: Permission denied: {exc}"
    except OSError as exc:
        return f"Error: {exc}"
