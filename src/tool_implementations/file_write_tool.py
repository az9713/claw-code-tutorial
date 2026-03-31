from __future__ import annotations

import json
import os


def handle_file_write(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    file_path = params.get("file_path", "")
    if not file_path:
        return "Error: file_path is required"

    content = params.get("content", "")

    try:
        parent = os.path.dirname(os.path.abspath(file_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        byte_count = len(content.encode("utf-8"))
        return f"File written: {file_path} ({byte_count} bytes)"
    except PermissionError:
        return f"Error: Permission denied: {file_path}"
    except OSError as exc:
        return f"Error writing file: {exc}"
