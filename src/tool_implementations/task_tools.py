from __future__ import annotations

import dataclasses
import json

from .. import stores


def _task_dict(task: stores.TaskRecord) -> dict:
    return dataclasses.asdict(task)


def handle_task_create(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    name = params.get("name", "")
    description = params.get("description", "")

    if not name:
        return "Error: name is required"

    task = stores.create_task(name=name, description=description)
    return json.dumps(_task_dict(task), indent=2)


def handle_task_get(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    task_id = params.get("task_id", "")
    if not task_id:
        return "Error: task_id is required"

    task = stores.get_task(task_id)
    if task is None:
        return f"Task not found: {task_id}"

    return json.dumps(_task_dict(task), indent=2)


def handle_task_list(payload: str) -> str:
    tasks = stores.list_tasks()
    return json.dumps([_task_dict(t) for t in tasks], indent=2)


def handle_task_update(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    task_id = params.get("task_id", "")
    status = params.get("status", "")

    if not task_id:
        return "Error: task_id is required"
    if not status:
        return "Error: status is required"

    task = stores.update_task(task_id=task_id, status=status)
    if task is None:
        return f"Task not found: {task_id}"

    return json.dumps(_task_dict(task), indent=2)


def handle_task_output(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    task_id = params.get("task_id", "")
    output = params.get("output", "")

    if not task_id:
        return "Error: task_id is required"

    task = stores.record_task_output(task_id=task_id, output=output)
    if task is None:
        return f"Task not found: {task_id}"

    return json.dumps(_task_dict(task), indent=2)


def handle_task_stop(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    task_id = params.get("task_id", "")
    if not task_id:
        return "Error: task_id is required"

    task = stores.stop_task(task_id)
    if task is None:
        return f"Task not found: {task_id}"

    return json.dumps(_task_dict(task), indent=2)
