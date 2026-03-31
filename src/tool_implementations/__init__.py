from __future__ import annotations

from .agent_tools import (
    handle_agent_tool,
    handle_fork_subagent,
    handle_run_agent,
    handle_spawn_multi_agent,
)
from .bash_tool import handle_bash_tool
from .config_tool import handle_config
from .cron_tools import handle_cron_create, handle_cron_delete, handle_cron_list
from .file_edit_tool import handle_file_edit
from .file_read_tool import handle_file_read
from .file_write_tool import handle_file_write
from .glob_tool import handle_glob
from .grep_tool import handle_grep
from .mode_tools import (
    handle_enter_plan_mode,
    handle_enter_worktree,
    handle_exit_plan_mode,
    handle_exit_worktree,
)
from .notebook_tool import handle_notebook_edit
from .task_tools import (
    handle_task_create,
    handle_task_get,
    handle_task_list,
    handle_task_output,
    handle_task_stop,
    handle_task_update,
)
from .team_tools import handle_send_message, handle_team_create, handle_team_delete
from .todo_tool import handle_todo_write
from .tool_search_tool import handle_tool_search
from .user_tools import handle_ask_user
from .web_tools import handle_web_fetch, handle_web_search

TOOL_DISPATCH: dict[str, object] = {
    "BashTool": handle_bash_tool,
    "FileReadTool": handle_file_read,
    "FileWriteTool": handle_file_write,
    "FileEditTool": handle_file_edit,
    "GlobTool": handle_glob,
    "GrepTool": handle_grep,
    "TaskCreateTool": handle_task_create,
    "TaskGetTool": handle_task_get,
    "TaskListTool": handle_task_list,
    "TaskUpdateTool": handle_task_update,
    "TaskOutputTool": handle_task_output,
    "TaskStopTool": handle_task_stop,
    "TeamCreateTool": handle_team_create,
    "TeamDeleteTool": handle_team_delete,
    "SendMessageTool": handle_send_message,
    "AgentTool": handle_agent_tool,
    "runAgent": handle_run_agent,
    "forkSubagent": handle_fork_subagent,
    "spawnMultiAgent": handle_spawn_multi_agent,
    "WebFetchTool": handle_web_fetch,
    "WebSearchTool": handle_web_search,
    "AskUserQuestionTool": handle_ask_user,
    "TodoWriteTool": handle_todo_write,
    "ConfigTool": handle_config,
    "ToolSearchTool": handle_tool_search,
    "EnterPlanModeTool": handle_enter_plan_mode,
    "ExitPlanModeV2Tool": handle_exit_plan_mode,
    "EnterWorktreeTool": handle_enter_worktree,
    "ExitWorktreeTool": handle_exit_worktree,
    "NotebookEditTool": handle_notebook_edit,
    "CronCreateTool": handle_cron_create,
    "CronDeleteTool": handle_cron_delete,
    "CronListTool": handle_cron_list,
}


def dispatch_tool(name: str, payload: str) -> str | None:
    """Look up and invoke a handler by tool name. Returns None if no handler registered."""
    handler = TOOL_DISPATCH.get(name)
    if handler is None:
        return None
    return handler(payload)  # type: ignore[operator]
