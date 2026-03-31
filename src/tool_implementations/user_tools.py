from __future__ import annotations

import json
import sys


def handle_ask_user(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    question = params.get("question", "")
    if not question:
        question = params.get("input", "")

    options = params.get("options", [])

    if sys.stdin.isatty():
        print(question)
        if options:
            for i, option in enumerate(options, start=1):
                print(f"  {i}. {option}")
        try:
            return input()
        except EOFError:
            return "[No input received]"

    return f"[Non-interactive mode] Question: {question}"
