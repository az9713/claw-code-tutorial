from __future__ import annotations

import dataclasses
import json

from .. import stores


def handle_todo_write(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    action = params.get("action", "")

    # Handle explicit action keywords
    if action == "list":
        todos = stores.list_todos()
        return json.dumps([dataclasses.asdict(t) for t in todos], indent=2)

    if action == "complete":
        todo_id = params.get("todo_id", "")
        if not todo_id:
            return "Error: todo_id is required for action=complete"
        updated = stores.complete_todo(todo_id)
        if updated is None:
            return f"Error: Todo not found: {todo_id}"
        return json.dumps(dataclasses.asdict(updated))

    if action == "delete":
        todo_id = params.get("todo_id", "")
        if not todo_id:
            return "Error: todo_id is required for action=delete"
        deleted = stores.delete_todo(todo_id)
        if deleted:
            return f"Todo {todo_id} deleted."
        return f"Error: Todo not found: {todo_id}"

    # Batch creation: {"todos": [...]}
    if "todos" in params:
        todos_spec = params["todos"]
        if not isinstance(todos_spec, list):
            return "Error: todos must be a list"
        created = []
        for item in todos_spec:
            if not isinstance(item, dict):
                continue
            content = item.get("content", "")
            if not content:
                continue
            todo = stores.create_todo(content)
            # If done=true was specified, mark it completed
            if item.get("done", False):
                completed = stores.complete_todo(todo.todo_id)
                if completed is not None:
                    todo = completed
            created.append(dataclasses.asdict(todo))
        return json.dumps(created, indent=2)

    # Single creation: {"content": "...", "done": false}
    content = params.get("content", "")
    if content:
        todo = stores.create_todo(content)
        if params.get("done", False):
            completed = stores.complete_todo(todo.todo_id)
            if completed is not None:
                todo = completed
        return json.dumps(dataclasses.asdict(todo))

    # Default: list all todos
    todos = stores.list_todos()
    return json.dumps([dataclasses.asdict(t) for t in todos], indent=2)
