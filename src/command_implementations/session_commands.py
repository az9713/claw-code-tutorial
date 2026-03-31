from __future__ import annotations

import sys
from pathlib import Path

from .. import stores
from ..commands import PORTED_COMMANDS


def handle_model(prompt: str) -> str:
    model = stores.get_config("model", "claude-opus-4-6")
    return f"Current model: {model}\nTo change: set config model=<model-name>"


def handle_memory(prompt: str) -> str:
    # Search for CLAUDE.md starting from cwd and walking up parent directories
    search_path = Path.cwd()
    for directory in [search_path, *search_path.parents]:
        candidate = directory / "CLAUDE.md"
        if candidate.is_file():
            try:
                contents = candidate.read_text(encoding="utf-8")
                return f"Memory file: {candidate}\n\n{contents}"
            except OSError as exc:
                return f"Error reading memory file {candidate}: {exc}"

    return (
        "No CLAUDE.md memory file found in current directory or any parent directory.\n"
        "Create a CLAUDE.md file in your project root to store persistent instructions."
    )


def handle_session(prompt: str) -> str:
    session_id = stores.get_config("session_id", "(no active session)")
    return (
        f"Session ID: {session_id}\n"
        "Use 'python -m src.main load-session <id>' to restore a session."
    )


def handle_summary(prompt: str) -> str:
    from ..query_engine import QueryEnginePort
    return QueryEnginePort.from_workspace().render_summary()


def handle_doctor(prompt: str) -> str:
    checks: list[tuple[str, bool, str]] = []

    # Check Python version >= 3.10
    major, minor = sys.version_info.major, sys.version_info.minor
    py_ok = (major, minor) >= (3, 10)
    checks.append((
        "Python >= 3.10",
        py_ok,
        f"{major}.{minor}.{sys.version_info.micro}",
    ))

    # Check snapshot files exist
    from pathlib import Path as _Path
    ref_data = _Path(__file__).resolve().parent.parent / "reference_data"

    tools_snapshot = ref_data / "tools_snapshot.json"
    checks.append((
        "tools_snapshot.json",
        tools_snapshot.is_file(),
        str(tools_snapshot),
    ))

    commands_snapshot = ref_data / "commands_snapshot.json"
    checks.append((
        "commands_snapshot.json",
        commands_snapshot.is_file(),
        str(commands_snapshot),
    ))

    # Check stores are accessible
    try:
        stores.list_tasks()
        stores_ok = True
        stores_detail = "ok"
    except Exception as exc:
        stores_ok = False
        stores_detail = str(exc)
    checks.append(("stores accessible", stores_ok, stores_detail))

    lines = ["claw-code doctor report", ""]
    for label, passed, detail in checks:
        status = "PASS" if passed else "FAIL"
        lines.append(f"  [{status}] {label}: {detail}")

    overall = all(passed for _, passed, _ in checks)
    lines.append("")
    lines.append("Overall: OK" if overall else "Overall: ISSUES FOUND")
    return "\n".join(lines)
