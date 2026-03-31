from __future__ import annotations

import json
import os


def handle_notebook_edit(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    notebook_path = params.get("notebook_path", "")
    if not notebook_path:
        return "Error: notebook_path is required"

    cell_index = params.get("cell_index", None)
    if cell_index is None:
        return "Error: cell_index is required"

    try:
        cell_index = int(cell_index)
    except (TypeError, ValueError):
        return "Error: cell_index must be an integer"

    new_source = params.get("new_source", "")
    cell_type = params.get("cell_type", "code")

    try:
        with open(notebook_path, "r", encoding="utf-8") as fh:
            notebook = json.load(fh)
    except FileNotFoundError:
        return f"Error: Notebook not found: {notebook_path}"
    except json.JSONDecodeError as exc:
        return f"Error: Not a valid notebook (JSON parse error): {exc}"
    except OSError as exc:
        return f"Error reading notebook: {exc}"

    try:
        cells = notebook["cells"]
    except KeyError:
        return f"Error: Not a valid notebook (missing 'cells' key): {notebook_path}"

    try:
        cell = cells[cell_index]
    except IndexError:
        return (
            f"Error: Cell index {cell_index} out of range "
            f"(notebook has {len(cells)} cells): {notebook_path}"
        )

    # Store the new source; ipynb format stores source as a list of lines or a single string
    if isinstance(cell.get("source"), list):
        # Preserve line-by-line format
        lines = new_source.splitlines(keepends=True)
        cell["source"] = lines
    else:
        cell["source"] = new_source

    # Update cell_type if provided
    if cell_type:
        cell["cell_type"] = cell_type

    try:
        with open(notebook_path, "w", encoding="utf-8") as fh:
            json.dump(notebook, fh, indent=1)
    except PermissionError:
        return f"Error: Permission denied writing: {notebook_path}"
    except OSError as exc:
        return f"Error writing notebook: {exc}"

    char_count = len(new_source)
    return f"Notebook {notebook_path}: cell {cell_index} updated ({char_count} chars)"
