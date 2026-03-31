from __future__ import annotations

import json

from .. import stores


def handle_enter_plan_mode(payload: str) -> str:
    stores.set_mode_flag("plan_mode", True)
    return "Plan mode activated. All tool calls will be planned before execution."


def handle_exit_plan_mode(payload: str) -> str:
    stores.set_mode_flag("plan_mode", False)
    return "Plan mode deactivated."


def handle_enter_worktree(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    # path and branch are optional; accepted but not acted upon in this port
    stores.set_mode_flag("worktree_mode", True)
    return "Worktree mode activated."


def handle_exit_worktree(payload: str) -> str:
    stores.set_mode_flag("worktree_mode", False)
    return "Worktree mode deactivated."
