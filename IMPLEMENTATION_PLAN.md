# Implementation Plan: Fill in Missing Tool & Command Implementations

## Context

The claw-code codebase has 184 mirrored tools and 207 mirrored commands that all return placeholder strings. This plan adds real implementations for ~30 tool groups and ~15 commands using only Python stdlib, while preserving full backward compatibility with existing tests.

---

## Architecture: Dispatcher Pattern

**Minimal change to existing code** — only 2 functions modified, 3 lines each:
- `src/tools.py:execute_tool()` (line 81) — import dispatcher, try dispatch, fall through to stub
- `src/commands.py:execute_command()` (line 75) — same pattern

No other existing files touched. The `execution_registry.py`, `runtime.py`, `query_engine.py`, and `main.py` all work unchanged because they call `execute_tool()` / `execute_command()` and receive the same `ToolExecution` / `CommandExecution` return types.

### How the dispatcher works

```
execute_tool("BashTool", '{"command":"echo hello"}')
  │
  ├── get_tool("BashTool") → PortingModule (found in snapshot)
  │
  ├── dispatch_tool("BashTool", payload)
  │     └── TOOL_DISPATCH["BashTool"] → handle_bash_tool(payload)
  │           └── subprocess.run("echo hello") → "hello\n"
  │
  └── return ToolExecution(name="BashTool", handled=True, message="hello\n")

execute_tool("MCPTool", '{"data":"test"}')
  │
  ├── get_tool("MCPTool") → PortingModule (found)
  │
  ├── dispatch_tool("MCPTool", payload) → None (not in dispatcher)
  │
  └── return ToolExecution(handled=True, message="Mirrored tool 'MCPTool'...")  ← existing stub
```

---

## New File Structure

```
src/
  stores.py                              # In-memory state (tasks, teams, agents, todos, config)
  tool_implementations/
    __init__.py                          # TOOL_DISPATCH dict + dispatch_tool()
    bash_tool.py                         # BashTool: subprocess.run with security checks
    file_read_tool.py                    # FileReadTool: read with line numbers, offset, limit
    file_write_tool.py                   # FileWriteTool: write with parent dir creation
    file_edit_tool.py                    # FileEditTool: old_string → new_string replacement
    glob_tool.py                         # GlobTool: pathlib.glob, sorted by mtime
    grep_tool.py                         # GrepTool: re.search, 3 output modes
    task_tools.py                        # TaskCreate/Get/List/Update/Output/Stop (6 handlers)
    team_tools.py                        # TeamCreate/Delete/SendMessage (3 handlers)
    agent_tools.py                       # AgentTool/runAgent/forkSubagent/spawnMultiAgent (4 handlers)
    web_tools.py                         # WebFetchTool (urllib), WebSearchTool (stub)
    user_tools.py                        # AskUserQuestionTool
    todo_tool.py                         # TodoWriteTool
    config_tool.py                       # ConfigTool
    tool_search_tool.py                  # ToolSearchTool (delegates to existing find_tools())
    mode_tools.py                        # EnterPlanMode/ExitPlanMode/Worktree flag toggles
    notebook_tool.py                     # NotebookEditTool (.ipynb JSON editing)
    cron_tools.py                        # CronCreate/Delete/List (in-memory)
  command_implementations/
    __init__.py                          # COMMAND_DISPATCH dict + dispatch_command()
    core_commands.py                     # help, version, clear, compact, status, cost
    session_commands.py                  # model, memory, session, summary, doctor
    config_commands.py                   # config, permissions, hooks, skills, mcp, tasks
tests/
  test_tool_implementations.py           # Unit tests for all tool handlers
  test_command_implementations.py        # Unit tests for command handlers
  test_stores.py                         # CRUD tests for state stores
```

**Total: 24 new files, 2 modified files**

---

## State Management: `src/stores.py`

All in-memory state lives in one file with frozen dataclass records and pure-function accessors:

```python
@dataclass(frozen=True)
class TaskRecord:
    task_id: str        # uuid4().hex[:12]
    name: str
    description: str
    status: str         # "pending" | "in_progress" | "completed" | "stopped"
    output: str

@dataclass(frozen=True)
class TeamRecord:
    team_id: str
    name: str
    member_names: tuple[str, ...]

@dataclass(frozen=True)
class AgentRecord:
    agent_id: str
    prompt: str
    status: str         # "running" | "completed"
    result: str

@dataclass(frozen=True)
class TodoItem:
    todo_id: str
    content: str
    done: bool

@dataclass(frozen=True)
class CronEntry:
    cron_id: str
    schedule: str
    command: str

# Module-level mutable stores (plain dicts):
_tasks: dict[str, TaskRecord] = {}
_teams: dict[str, TeamRecord] = {}
_agents: dict[str, AgentRecord] = {}
_todos: dict[str, TodoItem] = {}
_crons: dict[str, CronEntry] = {}
_config: dict[str, str] = {}
_mode_flags: dict[str, bool] = {"plan_mode": False, "worktree_mode": False}
```

Each store has CRUD functions: `create_task()`, `get_task()`, `list_tasks()`, `update_task()`, etc.

---

## Tool Implementation Details

Every handler has the same signature: `def handle_X(payload: str) -> str`

**Payload parsing convention** (consistent across all handlers):
```python
try:
    params = json.loads(payload) if payload.strip() else {}
except json.JSONDecodeError:
    params = {"input": payload}  # treat non-JSON as raw string
```

### Tier 1: Core I/O (highest value — makes the system actually do things)

| Tool | Payload fields | What it does | stdlib used |
|------|---------------|-------------|-------------|
| **BashTool** | `command`, `timeout=120000`, `description` | Run shell commands | `subprocess.run(shell=True, capture_output=True, timeout=)` |
| **FileReadTool** | `file_path`, `offset=0`, `limit=2000` | Read file with line numbers | `open()`, `enumerate()` |
| **FileWriteTool** | `file_path`, `content` | Write/overwrite file | `os.makedirs()`, `open(w)` |
| **FileEditTool** | `file_path`, `old_string`, `new_string` | Find-and-replace (unique match) | `str.count()`, `str.replace()` |
| **GlobTool** | `pattern`, `path="."` | Find files by pattern | `pathlib.Path.glob()` |
| **GrepTool** | `pattern`, `path`, `glob`, `output_mode`, `head_limit=250` | Search file contents | `re.search()`, `os.walk()` |

**BashTool security checks:**
- Reject obviously destructive commands: `rm -rf /`, `mkfs`, `dd if=`
- Path traversal validation
- Configurable timeout (default 120s)
- Output truncation (100KB limit)

### Tier 2: Task Management (6 handlers)

| Handler | Payload | Returns |
|---------|---------|---------|
| `handle_task_create` | `{name, description}` | JSON: `{task_id, name, status: "pending"}` |
| `handle_task_get` | `{task_id}` | JSON task record or "Task not found" |
| `handle_task_list` | (none) | JSON array of all tasks |
| `handle_task_update` | `{task_id, status}` | Updated task JSON |
| `handle_task_output` | `{task_id, output}` | Updated task JSON |
| `handle_task_stop` | `{task_id}` | Task with status="stopped" |

### Tier 3: Team & Agent (7 handlers)

| Handler | Payload | Returns |
|---------|---------|---------|
| `handle_team_create` | `{name, members[]}` | JSON: `{team_id, name, member_names}` |
| `handle_team_delete` | `{team_id}` | Confirmation or "Team not found" |
| `handle_send_message` | `{team_id, member, message}` | Delivery confirmation |
| `handle_agent_tool` | `{prompt}` | JSON: `{agent_id, status: "running"}` |
| `handle_run_agent` | `{prompt}` | Same as agent_tool |
| `handle_fork_subagent` | `{parent_agent_id, prompt}` | JSON: `{agent_id, parent_id}` |
| `handle_spawn_multi_agent` | `{agents: [{prompt}...]}` | JSON array of agent IDs |

Agent tools are "honest stubs" — they record intent in-memory and return IDs, but don't spawn real LLM processes. This is testable and shows the interface works.

### Tier 4: Utility (7 handlers)

| Tool | Behavior |
|------|----------|
| **WebFetchTool** | `urllib.request.urlopen(url)` with 30s timeout, 100KB body limit |
| **WebSearchTool** | Returns "Web search unavailable without API key. Query: {query}" |
| **AskUserQuestionTool** | `input()` if `sys.stdin.isatty()`, else placeholder |
| **TodoWriteTool** | CRUD on in-memory todo store |
| **ConfigTool** | Get/set on in-memory config dict |
| **ToolSearchTool** | Delegates to existing `find_tools()` from `src/tools.py` |

### Tier 5: Mode & Scheduling (6 handlers)

| Tool | Behavior |
|------|----------|
| **EnterPlanModeTool** | Set `stores._mode_flags["plan_mode"] = True` |
| **ExitPlanModeV2Tool** | Set to False |
| **EnterWorktreeTool** | Set `stores._mode_flags["worktree_mode"] = True` |
| **ExitWorktreeTool** | Set to False |
| **NotebookEditTool** | Read .ipynb JSON, modify cell source, write back |
| **CronCreate/Delete/List** | In-memory CronEntry CRUD (no real scheduling) |

---

## Command Implementation Details

Every handler: `def handle_X(prompt: str) -> str`

### `core_commands.py`

| Command | Behavior |
|---------|----------|
| `help` | List available commands from `PORTED_COMMANDS`, grouped by category |
| `version` | Return `"claw-code v0.1.0 (Python {sys.version})"` |
| `clear` | Return `"Conversation cleared."` |
| `compact` | Return `"Conversation compacted."` |
| `status` | Return platform info + session stats |
| `cost` | Return formatted usage summary |

### `session_commands.py`

| Command | Behavior |
|---------|----------|
| `model` | Return current model name from config store |
| `memory` | Read CLAUDE.md if it exists, else "No memory file found" |
| `session` | Return session ID and message count |
| `summary` | Delegate to `QueryEnginePort.from_workspace().render_summary()` |
| `doctor` | Run diagnostics: Python version, platform, snapshot files exist, stores initialized |

### `config_commands.py`

| Command | Behavior |
|---------|----------|
| `config` | Get/set config from stores |
| `permissions` | Return current ToolPermissionContext state |
| `hooks` | Return "No hooks configured" or list hooks |
| `skills` | List commands with "skills" in source_hint |
| `mcp` | Return "MCP requires external protocol support" |
| `tasks` | Delegate to `stores.list_tasks()` |

---

## What Remains as Stubs (42 entries)

| Tool group | Entries | Reason |
|------------|---------|--------|
| LSPTool | 6 | Needs language server client |
| MCPTool + McpAuthTool | 5 | Needs MCP protocol |
| ListMcpResourcesTool + ReadMcpResourceTool | 6 | Needs MCP protocol |
| PowerShellTool | 14 | Complex, platform-specific |
| BriefTool | 5 | Needs upload infrastructure |
| SyntheticOutputTool | 1 | Internal testing only |
| REPLTool | 2 | Needs interactive REPL |
| RemoteTriggerTool | 3 | Needs remote execution |

---

## Implementation Phases

| Phase | What | Files |
|-------|------|-------|
| **1. Foundation** | stores.py + empty dispatchers + modify execute_tool/execute_command | 4 files |
| **2. Core I/O** | BashTool, FileRead, FileWrite, FileEdit, Glob, Grep | 6 files |
| **3. Task management** | 6 task tool handlers | 1 file |
| **4. Team & Agent** | Team + agent handlers | 2 files |
| **5. Utilities** | Web, user, todo, config, search, mode, notebook, cron | 8 files |
| **6. Commands** | 15 slash commands | 3 files |
| **7. Tests** | All new code tested | 3 files |

---

## Backward Compatibility

The existing 18 tests assert on `"Mirrored command 'review'"` and `"Mirrored tool 'MCPTool'"`. Neither `review` nor `MCPTool` is in the new dispatchers, so they fall through to the existing stub path. **Zero test regressions guaranteed.**

---

## Verification

After implementation, verify with:

```bash
# All existing tests still pass
python -m unittest discover -s tests -v

# Core I/O tools work
python -m src.main exec-tool BashTool '{"command": "echo hello"}'
python -m src.main exec-tool FileReadTool '{"file_path": "README.md"}'
python -m src.main exec-tool FileEditTool '{"file_path": "test.txt", "old_string": "foo", "new_string": "bar"}'
python -m src.main exec-tool GlobTool '{"pattern": "**/*.py"}'
python -m src.main exec-tool GrepTool '{"pattern": "def execute", "path": "src"}'

# Task management works
python -m src.main exec-tool TaskCreateTool '{"name": "test", "description": "demo task"}'
python -m src.main exec-tool TaskListTool ''

# Team creation works
python -m src.main exec-tool TeamCreateTool '{"name": "alpha", "members": ["agent1", "agent2"]}'

# Agent spawning works
python -m src.main exec-tool spawnMultiAgent '{"agents": [{"prompt": "explore codebase"}, {"prompt": "write tests"}]}'

# Commands work
python -m src.main exec-command help ''
python -m src.main exec-command version ''
python -m src.main exec-command doctor ''

# Unimplemented tools still return stubs
python -m src.main exec-tool MCPTool 'test'
# → "Mirrored tool 'MCPTool' from tools/MCPTool/MCPTool.ts would handle payload 'test'."
```
