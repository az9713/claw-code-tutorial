from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import uuid4


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    name: str
    description: str
    status: str  # "pending" | "in_progress" | "completed" | "stopped"
    output: str = ''


@dataclass(frozen=True)
class TeamRecord:
    team_id: str
    name: str
    member_names: tuple[str, ...]


@dataclass(frozen=True)
class AgentRecord:
    agent_id: str
    prompt: str
    status: str  # "running" | "completed"
    result: str = ''
    parent_id: str = ''


@dataclass(frozen=True)
class TodoItem:
    todo_id: str
    content: str
    done: bool = False


@dataclass(frozen=True)
class CronEntry:
    cron_id: str
    schedule: str
    command: str


# Module-level mutable stores
_tasks: dict[str, TaskRecord] = {}
_teams: dict[str, TeamRecord] = {}
_agents: dict[str, AgentRecord] = {}
_todos: dict[str, TodoItem] = {}
_crons: dict[str, CronEntry] = {}
_config: dict[str, str] = {}
_mode_flags: dict[str, bool] = {"plan_mode": False, "worktree_mode": False}


def _new_id() -> str:
    return uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Task CRUD
# ---------------------------------------------------------------------------

def create_task(name: str, description: str) -> TaskRecord:
    task = TaskRecord(task_id=_new_id(), name=name, description=description, status='pending')
    _tasks[task.task_id] = task
    return task


def get_task(task_id: str) -> TaskRecord | None:
    return _tasks.get(task_id)


def list_tasks() -> tuple[TaskRecord, ...]:
    return tuple(_tasks.values())


def update_task(task_id: str, status: str) -> TaskRecord | None:
    task = _tasks.get(task_id)
    if task is None:
        return None
    updated = replace(task, status=status)
    _tasks[task_id] = updated
    return updated


def record_task_output(task_id: str, output: str) -> TaskRecord | None:
    task = _tasks.get(task_id)
    if task is None:
        return None
    updated = replace(task, output=output)
    _tasks[task_id] = updated
    return updated


def stop_task(task_id: str) -> TaskRecord | None:
    return update_task(task_id, 'stopped')


# ---------------------------------------------------------------------------
# Team CRUD
# ---------------------------------------------------------------------------

def create_team(name: str, members: list[str]) -> TeamRecord:
    team = TeamRecord(team_id=_new_id(), name=name, member_names=tuple(members))
    _teams[team.team_id] = team
    return team


def get_team(team_id: str) -> TeamRecord | None:
    return _teams.get(team_id)


def list_teams() -> tuple[TeamRecord, ...]:
    return tuple(_teams.values())


def delete_team(team_id: str) -> bool:
    if team_id in _teams:
        del _teams[team_id]
        return True
    return False


# ---------------------------------------------------------------------------
# Agent CRUD
# ---------------------------------------------------------------------------

def create_agent(prompt: str, parent_id: str = '') -> AgentRecord:
    agent = AgentRecord(agent_id=_new_id(), prompt=prompt, status='running', parent_id=parent_id)
    _agents[agent.agent_id] = agent
    return agent


def get_agent(agent_id: str) -> AgentRecord | None:
    return _agents.get(agent_id)


def list_agents() -> tuple[AgentRecord, ...]:
    return tuple(_agents.values())


def complete_agent(agent_id: str, result: str) -> AgentRecord | None:
    agent = _agents.get(agent_id)
    if agent is None:
        return None
    updated = replace(agent, status='completed', result=result)
    _agents[agent_id] = updated
    return updated


# ---------------------------------------------------------------------------
# Todo CRUD
# ---------------------------------------------------------------------------

def create_todo(content: str) -> TodoItem:
    todo = TodoItem(todo_id=_new_id(), content=content)
    _todos[todo.todo_id] = todo
    return todo


def get_todo(todo_id: str) -> TodoItem | None:
    return _todos.get(todo_id)


def list_todos() -> tuple[TodoItem, ...]:
    return tuple(_todos.values())


def complete_todo(todo_id: str) -> TodoItem | None:
    todo = _todos.get(todo_id)
    if todo is None:
        return None
    updated = replace(todo, done=True)
    _todos[todo_id] = updated
    return updated


def delete_todo(todo_id: str) -> bool:
    if todo_id in _todos:
        del _todos[todo_id]
        return True
    return False


# ---------------------------------------------------------------------------
# Cron CRUD
# ---------------------------------------------------------------------------

def create_cron(schedule: str, command: str) -> CronEntry:
    entry = CronEntry(cron_id=_new_id(), schedule=schedule, command=command)
    _crons[entry.cron_id] = entry
    return entry


def list_crons() -> tuple[CronEntry, ...]:
    return tuple(_crons.values())


def delete_cron(cron_id: str) -> bool:
    if cron_id in _crons:
        del _crons[cron_id]
        return True
    return False


# ---------------------------------------------------------------------------
# Config get/set
# ---------------------------------------------------------------------------

def get_config(key: str, default: str = '') -> str:
    return _config.get(key, default)


def set_config(key: str, value: str) -> None:
    _config[key] = value


def all_config() -> dict[str, str]:
    return dict(_config)


# ---------------------------------------------------------------------------
# Mode flags
# ---------------------------------------------------------------------------

def get_mode_flag(key: str) -> bool:
    return _mode_flags.get(key, False)


def set_mode_flag(key: str, value: bool) -> None:
    _mode_flags[key] = value
