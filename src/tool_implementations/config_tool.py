from __future__ import annotations

import json

from .. import stores


def handle_config(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    action = params.get("action", "list")

    if action == "get":
        key = params.get("key", "")
        if not key:
            return "Error: key is required for action=get"
        return stores.get_config(key, "")

    if action == "set":
        key = params.get("key", "")
        value = params.get("value", "")
        if not key:
            return "Error: key is required for action=set"
        stores.set_config(key, value)
        return f"Set {key} = {value}"

    # Default: list all config
    return json.dumps(stores.all_config(), indent=2)
