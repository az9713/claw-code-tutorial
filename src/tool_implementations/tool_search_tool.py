from __future__ import annotations

import json

from ..tools import find_tools


def handle_tool_search(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    query = params.get("query", "")
    if not query:
        return "Error: query is required"

    max_results = int(params.get("max_results", 5))

    matches = find_tools(query, limit=max_results)

    if not matches:
        return f"No tools found matching: {query}"

    lines = [f"Found {len(matches)} tools:"]
    for tool in matches:
        lines.append(f"- {tool.name}: {tool.responsibility}")
        lines.append(f"  source: {tool.source_hint}")

    return "\n".join(lines)
