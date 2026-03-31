from __future__ import annotations

import json
from pathlib import Path


def handle_glob(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    pattern = params.get("pattern", "**/*")
    base_path = params.get("path", ".")

    try:
        root = Path(base_path)
        if not root.exists():
            return f"Error: Path does not exist: {base_path}"

        matches = list(root.glob(pattern))
        # Sort by modification time descending (most recently modified first)
        matches.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)

        # Limit to 1000 results
        matches = matches[:1000]

        if not matches:
            return ""

        return "\n".join(str(p) for p in matches)
    except OSError as exc:
        return f"Error: {exc}"
    except ValueError as exc:
        # pathlib raises ValueError for invalid patterns on some platforms
        return f"Error: Invalid glob pattern: {exc}"
