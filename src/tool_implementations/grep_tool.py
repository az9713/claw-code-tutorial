from __future__ import annotations

import fnmatch
import json
import os
import re
from pathlib import Path


def handle_grep(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    pattern = params.get("pattern", "")
    if not pattern:
        return "Error: pattern is required"

    search_path = params.get("path", ".")
    glob_filter = params.get("glob", None)
    output_mode = params.get("output_mode", "files_with_matches")
    head_limit = int(params.get("head_limit", 250))
    case_insensitive = bool(params.get("-i", False))
    show_line_numbers = bool(params.get("-n", True))
    context_lines = int(params.get("context", 0))

    # Compile the regex
    try:
        flags = re.IGNORECASE if case_insensitive else 0
        regex = re.compile(pattern, flags)
    except re.error as exc:
        return f"Error: Invalid regex pattern: {exc}"

    root = Path(search_path)
    if not root.exists():
        return f"Error: Path does not exist: {search_path}"

    # Collect files to search
    if root.is_file():
        files_to_search = [root]
    else:
        files_to_search = [p for p in root.rglob("*") if p.is_file()]
        if glob_filter:
            files_to_search = [
                p for p in files_to_search
                if fnmatch.fnmatch(p.name, glob_filter) or fnmatch.fnmatch(str(p), glob_filter)
            ]

    results: list[str] = []
    matched_files: list[str] = []
    count_map: dict[str, int] = {}

    for file_path in sorted(files_to_search):
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            continue

        lines = text.splitlines()
        file_matches: list[tuple[int, str]] = []

        for lineno, line in enumerate(lines, start=1):
            if regex.search(line):
                file_matches.append((lineno, line))

        if not file_matches:
            continue

        file_str = str(file_path)

        if output_mode == "files_with_matches":
            results.append(file_str)
            if len(results) >= head_limit:
                break

        elif output_mode == "count":
            count_map[file_str] = len(file_matches)

        elif output_mode == "content":
            if context_lines > 0:
                # Collect unique line indices with context
                matched_indices = {lineno - 1 for lineno, _ in file_matches}
                context_indices: set[int] = set()
                for idx in matched_indices:
                    for ci in range(max(0, idx - context_lines), min(len(lines), idx + context_lines + 1)):
                        context_indices.add(ci)

                for idx in sorted(context_indices):
                    lineno = idx + 1
                    line = lines[idx]
                    if show_line_numbers:
                        results.append(f"{file_str}:{lineno}:{line}")
                    else:
                        results.append(f"{file_str}:{line}")
            else:
                for lineno, line in file_matches:
                    if show_line_numbers:
                        results.append(f"{file_str}:{lineno}:{line}")
                    else:
                        results.append(f"{file_str}:{line}")

            if len(results) >= head_limit:
                results = results[:head_limit]
                break

    if output_mode == "count":
        count_lines = [f"{path}: {cnt}" for path, cnt in sorted(count_map.items())]
        count_lines = count_lines[:head_limit]
        return "\n".join(count_lines)

    return "\n".join(results)
