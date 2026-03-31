from __future__ import annotations

import json


def handle_file_edit(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    file_path = params.get("file_path", "")
    if not file_path:
        return "Error: file_path is required"

    old_string = params.get("old_string", "")
    new_string = params.get("new_string", "")
    replace_all = bool(params.get("replace_all", False))

    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            original = fh.read()
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except IsADirectoryError:
        return f"Error: Path is a directory: {file_path}"
    except PermissionError:
        return f"Error: Permission denied: {file_path}"
    except OSError as exc:
        return f"Error reading file: {exc}"

    count = original.count(old_string)

    if replace_all:
        if count == 0:
            return f"Error: old_string not found in {file_path}"
    else:
        if count == 0:
            return f"Error: old_string not found in {file_path}"
        if count > 1:
            return (
                f"Error: old_string appears {count} times in {file_path}. "
                "Use replace_all=true to replace all occurrences, or provide more context to make it unique."
            )

    if replace_all:
        updated = original.replace(old_string, new_string)
        replacements = count
    else:
        updated = original.replace(old_string, new_string, 1)
        replacements = 1

    try:
        with open(file_path, "w", encoding="utf-8") as fh:
            fh.write(updated)
    except PermissionError:
        return f"Error: Permission denied writing: {file_path}"
    except OSError as exc:
        return f"Error writing file: {exc}"

    old_preview = old_string[:60].replace("\n", "\\n")
    new_preview = new_string[:60].replace("\n", "\\n")
    return (
        f"Edited {file_path}: replaced {replacements} occurrence(s) of "
        f"{old_preview!r} with {new_preview!r}"
    )
