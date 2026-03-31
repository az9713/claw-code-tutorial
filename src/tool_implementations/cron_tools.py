from __future__ import annotations

import dataclasses
import json

from .. import stores


def handle_cron_create(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    schedule = params.get("schedule", "")
    if not schedule:
        return "Error: schedule is required"

    command = params.get("command", "")
    if not command:
        return "Error: command is required"

    entry = stores.create_cron(schedule, command)
    return json.dumps({
        "cron_id": entry.cron_id,
        "schedule": entry.schedule,
        "command": entry.command,
    })


def handle_cron_delete(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    cron_id = params.get("cron_id", "")
    if not cron_id:
        return "Error: cron_id is required"

    deleted = stores.delete_cron(cron_id)
    if deleted:
        return f"Cron {cron_id} deleted."
    return f"Cron not found: {cron_id}"


def handle_cron_list(payload: str) -> str:
    entries = stores.list_crons()
    return json.dumps([dataclasses.asdict(e) for e in entries], indent=2)
