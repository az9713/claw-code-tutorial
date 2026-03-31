# Python API Reference

## Package Exports (`src/__init__.py`)

Primary exported symbols:

- `QueryEnginePort`, `TurnResult`
- `PortRuntime`, `RuntimeSession`
- `PortManifest`, `build_port_manifest`
- `ParityAuditResult`, `run_parity_audit`
- `PORTED_COMMANDS`, `build_command_backlog`
- `PORTED_TOOLS`, `build_tool_backlog`
- `StoredSession`, `save_session`, `load_session`
- `build_system_init_message`

## Core Types

### `src/models.py`

- `Subsystem`: top-level module metadata
- `PortingModule`: mirrored command/tool module metadata
- `PermissionDenial`: denial reason record
- `UsageSummary`: simple token accounting (word-count approximation)
- `PortingBacklog`: list wrapper with markdown summary helpers

### `src/query_engine.py`

- `QueryEngineConfig`
  - `max_turns`, `max_budget_tokens`, `compact_after_turns`
  - `structured_output`, `structured_retry_limit`
- `TurnResult`
  - prompt, output, matched command/tool tuples, denials, usage, stop reason
- `QueryEnginePort`
  - `from_workspace()`, `from_saved_session(session_id)`
  - `submit_message(...)`, `stream_submit_message(...)`
  - `compact_messages_if_needed()`, `persist_session()`, `render_summary()`

### `src/runtime.py`

- `RoutedMatch`: route match tuple (`kind`, `name`, `score`, `source_hint`)
- `RuntimeSession`: bootstrap session aggregate (context/setup/history/output)
- `PortRuntime`
  - `route_prompt(prompt, limit=5)`
  - `bootstrap_session(prompt, limit=5)`
  - `run_turn_loop(prompt, limit=5, max_turns=3, structured_output=False)`

## Inventory APIs

### Commands (`src/commands.py`)

- Constants:
  - `SNAPSHOT_PATH`
  - `PORTED_COMMANDS`
- Functions:
  - `load_command_snapshot()`
  - `built_in_command_names()`
  - `get_command(name)`
  - `get_commands(...)`
  - `find_commands(query, limit=20)`
  - `execute_command(name, prompt='')`
  - `render_command_index(limit=20, query=None)`

### Tools (`src/tools.py`)

- Constants:
  - `SNAPSHOT_PATH`
  - `PORTED_TOOLS`
- Functions:
  - `load_tool_snapshot()`
  - `get_tool(name)`
  - `get_tools(simple_mode=False, include_mcp=True, permission_context=None)`
  - `find_tools(query, limit=20)`
  - `execute_tool(name, payload='')`
  - `render_tool_index(limit=20, query=None)`

### Tool Implementations (`src/tool_implementations/`)

- `TOOL_DISPATCH: dict[str, Callable[[str], str]]` — maps tool name to handler
- `dispatch_tool(name: str, payload: str) -> str | None` — invokes handler or returns `None`

### Command Implementations (`src/command_implementations/`)

- `COMMAND_DISPATCH: dict[str, Callable[[str], str]]` — maps command name to handler
- `dispatch_command(name: str, prompt: str) -> str | None` — invokes handler or returns `None`

### State Store (`src/stores.py`)

- Dataclasses (all `frozen=True`):
  - `TaskRecord` — task_id, name, description, status, output
  - `TeamRecord` — team_id, name, member_names
  - `AgentRecord` — agent_id, prompt, status, result, parent_id
  - `TodoItem` — todo_id, content, done
  - `CronEntry` — cron_id, schedule, command
- Task CRUD: `create_task`, `get_task`, `list_tasks`, `update_task`, `record_task_output`, `stop_task`
- Team CRUD: `create_team`, `get_team`, `list_teams`, `delete_team`
- Agent CRUD: `create_agent`, `get_agent`, `list_agents`, `complete_agent`
- Todo CRUD: `create_todo`, `get_todo`, `list_todos`, `complete_todo`, `delete_todo`
- Cron CRUD: `create_cron`, `list_crons`, `delete_cron`
- Config: `get_config(key, default='')`, `set_config(key, value)`, `all_config()`
- Mode flags: `get_mode_flag(key)`, `set_mode_flag(key, value)`

State is in-memory only — all stores reset on process exit.

## Session APIs

### `src/transcript.py`

- `TranscriptStore.append/compact/replay/flush`

### `src/session_store.py`

- `StoredSession`
- `save_session(session, directory=None) -> Path`
- `load_session(session_id, directory=None) -> StoredSession`

Default session directory: `.port_sessions/`

## Parity and Context APIs

- `build_port_manifest()` (`src/port_manifest.py`)
- `build_port_context()` and `render_context()` (`src/context.py`)
- `run_parity_audit()` (`src/parity_audit.py`)

## Placeholder Subsystem Metadata Packages

Packages such as `src.assistant`, `src.utils`, `src.bridge` expose:

- `ARCHIVE_NAME`
- `MODULE_COUNT`
- `SAMPLE_FILES`
- `PORTING_NOTE`

These values are loaded from `src/reference_data/subsystems/<name>.json`.

## Runtime Infrastructure APIs

### `src/setup.py`

- `WorkspaceSetup`: python_version, implementation, platform_name, test_command, `startup_steps()`
- `SetupReport`: setup, prefetches, deferred_init, trusted, cwd, `as_markdown()`
- `run_setup(cwd=None, trusted=True) → SetupReport`
- `build_workspace_setup() → WorkspaceSetup`

### `src/prefetch.py`

- `PrefetchResult`: name, started, detail
- `start_mdm_raw_read()`, `start_keychain_prefetch()`, `start_project_scan(root)`

### `src/deferred_init.py`

- `DeferredInitResult`: trusted, plugin_init, skill_init, mcp_prefetch, session_hooks, `as_lines()`
- `run_deferred_init(trusted) → DeferredInitResult`

### `src/history.py`

- `HistoryEvent`: title, detail
- `HistoryLog`: events list, `add(title, detail)`, `as_markdown()`

### `src/remote_runtime.py`

- `RuntimeModeReport`: mode, connected, detail, `as_text()`
- `run_remote_mode(target)`, `run_ssh_mode(target)`, `run_teleport_mode(target)`

### `src/direct_modes.py`

- `DirectModeReport`: mode, target, active, `as_text()`
- `run_direct_connect(target)`, `run_deep_link(target)`

### `src/bootstrap_graph.py`

- `BootstrapGraph`: stages tuple, `as_markdown()`
- `build_bootstrap_graph() → BootstrapGraph`

### `src/command_graph.py`

- `CommandGraph`: builtins, plugin_like, skill_like, `flattened()`, `as_markdown()`
- `build_command_graph() → CommandGraph`

### `src/tool_pool.py`

- `ToolPool`: tools, simple_mode, include_mcp, `as_markdown()`
- `assemble_tool_pool(simple_mode=False, include_mcp=True, permission_context=None) → ToolPool`

### `src/cost_tracker.py` + `src/costHook.py`

- `CostTracker`: total_units, events, `record(label, units)`
- `apply_cost_hook(tracker, label, units) → CostTracker`

### `src/system_init.py`

- `build_system_init_message(trusted=True) → str`

## Root-Level Mirror Files

The following files mirror TypeScript originals from the archive root and are tracked by `parity_audit.py`. They are thin stubs; prefer the full implementations in `query_engine.py`, `tools.py`, etc.

| File | Key export |
|------|-----------|
| `src/QueryEngine.py` | `QueryEngineRuntime(QueryEnginePort)` — adds `route(prompt) → str` |
| `src/Tool.py` | `ToolDefinition`, `DEFAULT_TOOLS` |
| `src/query.py` | `QueryRequest`, `QueryResponse` |
| `src/task.py` | `PortingTask` |
| `src/tasks.py` | `default_tasks() → list[PortingTask]` |
| `src/ink.py` | `render_markdown_panel(text) → str` |
| `src/interactiveHelpers.py` | `bulletize(items) → str` |
| `src/replLauncher.py` | `build_repl_banner() → str` |
| `src/dialogLaunchers.py` | `DialogLauncher`, `DEFAULT_DIALOGS` |
| `src/costHook.py` | `apply_cost_hook(tracker, label, units)` |
| `src/projectOnboardingState.py` | `ProjectOnboardingState` |

## Active Implementation Modules

The following modules go beyond mirroring — they contain real Python logic used at runtime:

| Module | Purpose |
|--------|---------|
| `src/stores.py` | In-memory CRUD store for tasks, teams, agents, todos, crons, config, mode flags |
| `src/tool_implementations/` | Handler package; `TOOL_DISPATCH` dict + `dispatch_tool()` |
| `src/command_implementations/` | Handler package; `COMMAND_DISPATCH` dict + `dispatch_command()` |

---

## Dispatcher Pattern

Tool and command execution follows a three-layer call chain:

```
execute_tool(name, payload)          # src/tools.py
    └── dispatch_tool(name, payload) # src/tool_implementations/__init__.py
            └── handler(payload)     # e.g. src/tool_implementations/bash_tool.py
```

And the equivalent for commands:

```
execute_command(name, prompt)          # src/commands.py
    └── dispatch_command(name, prompt) # src/command_implementations/__init__.py
            └── handler(prompt)        # e.g. src/command_implementations/core_commands.py
```

### Layer responsibilities

**`execute_tool` / `execute_command`** (`src/tools.py`, `src/commands.py`)

Resolves the name against the snapshot registry (`tools_snapshot.json` / `commands_snapshot.json`). Returns a `ToolExecution` / `CommandExecution` dataclass. If the name is unknown, returns `handled=False`. Otherwise calls the dispatcher.

**`dispatch_tool` / `dispatch_command`** (`src/tool_implementations/__init__.py`, `src/command_implementations/__init__.py`)

Performs a dict lookup against `TOOL_DISPATCH` / `COMMAND_DISPATCH`. Returns the handler's string result, or `None` if no handler is registered. A `None` result causes the caller to emit a mirrored-stub placeholder instead of a real response.

**Handler functions** (individual files under `src/tool_implementations/` and `src/command_implementations/`)

Receive a raw `payload: str` (tools) or `prompt: str` (commands) and return a `str`. Handlers parse their own payload (typically JSON) and may call `src/stores.py` CRUD functions to read or write in-memory state.

### Example: adding a real handler

```python
# src/tool_implementations/my_tool.py
from __future__ import annotations
import json
from .. import stores


def handle_my_tool(payload: str) -> str:
    params = json.loads(payload) if payload.strip() else {}
    record = stores.create_task(params.get("name", ""), params.get("description", ""))
    import dataclasses
    return json.dumps(dataclasses.asdict(record), indent=2)
```

Then in `src/tool_implementations/__init__.py`:

```python
from .my_tool import handle_my_tool

TOOL_DISPATCH: dict[str, object] = {
    # existing entries ...
    "MyTool": handle_my_tool,
}
```
