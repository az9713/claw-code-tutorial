from __future__ import annotations

import json
import urllib.error
import urllib.request


def handle_web_fetch(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    url = params.get("url", "")
    if not url:
        return "Error: url is required"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            raw = response.read(100000)
            return raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return f"Error: HTTP {exc.code} {exc.reason} for URL: {url}"
    except urllib.error.URLError as exc:
        return f"Error: URL error for {url}: {exc.reason}"
    except ValueError as exc:
        return f"Error: Invalid URL {url!r}: {exc}"
    except OSError as exc:
        return f"Error fetching {url}: {exc}"


def handle_web_search(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    query = params.get("query", "")
    return (
        "Web search is not available without an external API key.\n"
        f"Query: {query}\n\n"
        "To enable web search, configure a search API key in config."
    )
