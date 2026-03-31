from __future__ import annotations

import json


def handle_file_read(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    file_path = params.get("file_path", "")
    if not file_path:
        return "Error: file_path is required"

    offset = int(params.get("offset", 0))
    limit = int(params.get("limit", 2000))

    try:
        raw_bytes = open(file_path, "rb").read()
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except IsADirectoryError:
        return f"Error: Path is a directory: {file_path}"
    except PermissionError:
        return f"Error: Permission denied: {file_path}"
    except OSError as exc:
        return f"Error reading file: {exc}"

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return f"Binary file: {len(raw_bytes)} bytes"

    lines = text.splitlines(keepends=True)
    selected = lines[offset : offset + limit]

    formatted_lines = []
    for i, line in enumerate(selected, start=offset + 1):
        formatted_lines.append(f"{i}\t{line.rstrip(chr(10)).rstrip(chr(13))}")

    return "\n".join(formatted_lines)
