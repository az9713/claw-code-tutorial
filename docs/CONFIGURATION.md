# Configuration Reference

Claw Code has no configuration file. All configuration is expressed in code via dataclasses or CLI flags.

## What Can and Cannot Be Configured via CLI

| Setting | CLI flag | API only |
|---------|----------|----------|
| `max_turns` | `--max-turns` (turn-loop) | — |
| `structured_output` | `--structured-output` (turn-loop) | — |
| `max_budget_tokens` | — | `QueryEngineConfig(max_budget_tokens=N)` |
| `compact_after_turns` | — | `QueryEngineConfig(compact_after_turns=N)` |
| `structured_retry_limit` | — | `QueryEngineConfig(structured_retry_limit=N)` |
| Tool deny by name | `--deny-tool NAME` (tools) | `ToolPermissionContext.from_iterables(deny_names=[...])` |
| Tool deny by prefix | `--deny-prefix PREFIX` (tools) | `ToolPermissionContext.from_iterables(deny_prefixes=[...])` |
| Simple mode | `--simple-mode` (tools) | `get_tools(simple_mode=True)` |
| MCP exclusion | `--no-mcp` (tools) | `get_tools(include_mcp=False)` |
| Trust level | not exposed | `run_setup(trusted=False)` |

---

## Query Engine Configuration

`QueryEngineConfig` (`src/query_engine.py`) controls the conversation engine behaviour. It is a frozen dataclass.

```python
from src.query_engine import QueryEngineConfig

config = QueryEngineConfig(
    max_turns=8,
    max_budget_tokens=2000,
    compact_after_turns=12,
    structured_output=False,
    structured_retry_limit=2,
)
```

To override, assign a new instance to `engine.config`:

```python
engine = QueryEnginePort.from_workspace()
engine.config = QueryEngineConfig(max_turns=4, structured_output=True)
```

Or pass flags to the `turn-loop` CLI subcommand:

```bash
python3 -m src.main turn-loop "my prompt" --max-turns 4 --structured-output
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_turns` | `int` | `8` | Maximum turns. When reached, `submit_message` returns immediately with `stop_reason="max_turns_reached"` without processing the prompt. |
| `max_budget_tokens` | `int` | `2000` | Approximate token budget (word-count based). After a turn causes the cumulative `input_tokens + output_tokens` to exceed this value, `stop_reason` is set to `"max_budget_reached"`. The turn is still processed. |
| `compact_after_turns` | `int` | `12` | When `len(mutable_messages)` exceeds this value, the list is trimmed to its last `compact_after_turns` entries. The transcript store is compacted by the same amount. |
| `structured_output` | `bool` | `False` | When `True`, `submit_message` emits a JSON object `{"summary": [...], "session_id": "..."}` instead of plain text. |
| `structured_retry_limit` | `int` | `2` | Number of JSON serialisation attempts before raising `RuntimeError`. |

---

## Permission Configuration

Permissions are enforced by `ToolPermissionContext` (`src/permissions.py`).

### Via the API

```python
from src.permissions import ToolPermissionContext

ctx = ToolPermissionContext.from_iterables(
    deny_names=["BashTool", "FileEditTool"],
    deny_prefixes=["mcp"],
)
```

All name matching is case-insensitive.

### Via the CLI

The `tools` subcommand accepts permission flags:

```bash
# Deny a specific tool by name
python3 -m src.main tools --deny-tool BashTool

# Deny all tools whose name starts with "mcp" (case-insensitive)
python3 -m src.main tools --deny-prefix mcp

# Both flags are repeatable
python3 -m src.main tools --deny-tool BashTool --deny-tool FileEditTool --deny-prefix mcp
```

### Automatic Bash Gating

`PortRuntime._infer_permission_denials()` automatically generates a `PermissionDenial` for any routed tool whose name contains `"bash"` (case-insensitive).

- Applies during `bootstrap_session()` and `run_turn_loop()` only.
- Does **not** apply when calling `QueryEnginePort.submit_message()` directly without going through `PortRuntime`.
- There is no CLI flag to override this behaviour.
- The denial reason is: `"destructive shell execution remains gated in the Python port"`.

The denial is recorded in `TurnResult.permission_denials` and is visible in session output and Markdown reports. It does not prevent the turn from executing — it marks the tool as denied in the result.

---

## Tool Filtering Modes

### Simple Mode

Restricts the tool inventory to three core tools: `BashTool`, `FileReadTool`, `FileEditTool`.

**CLI:**
```bash
python3 -m src.main tools --simple-mode
```

**API:**
```python
from src.tools import get_tools
tools = get_tools(simple_mode=True)
```

### MCP Exclusion

Excludes any tool whose `name` or `source_hint` contains `"mcp"`.

**CLI:**
```bash
python3 -m src.main tools --no-mcp
```

**API:**
```python
tools = get_tools(include_mcp=False)
```

---

## Command Filtering

Plugin-like and skill-like commands can be excluded from listings.

**CLI:**
```bash
python3 -m src.main commands --no-plugin-commands
python3 -m src.main commands --no-skill-commands
```

**API:**
```python
from src.commands import get_commands
commands = get_commands(
    include_plugin_commands=False,
    include_skill_commands=False,
)
```

Classification is based on `source_hint` strings: entries whose hint contains `"plugin"` are plugin-like; entries whose hint contains `"skill"` are skill-like.

---

## Deferred Initialisation

`run_deferred_init(trusted: bool)` (`src/deferred_init.py`) gates four subsystems on a single `trusted` flag:

| Subsystem | Effect when `trusted=False` | Effect when `trusted=True` |
|-----------|----------------------------|---------------------------|
| `plugin_init` | `False` — plugins not loaded | `True` |
| `skill_init` | `False` — skills not loaded | `True` |
| `mcp_prefetch` | `False` — MCP prefetch skipped | `True` |
| `session_hooks` | `False` — hooks not registered | `True` |

**Important**: `PortRuntime.bootstrap_session()` always calls `run_setup(trusted=True)`, so all four are always `True` via the standard runtime path. The `trusted=False` path is only reachable by calling `run_setup(trusted=False)` directly from the API. There is no CLI flag to set `trusted=False`.

To inspect the deferred init state from the CLI:

```bash
python3 -m src.main setup-report
# Output includes:
#   Deferred init:
#   - plugin_init=True
#   - skill_init=True
#   - mcp_prefetch=True
#   - session_hooks=True
```

---

## Session Directory

Sessions are persisted to `.port_sessions/` relative to the **current working directory** when the CLI or API call is made — not relative to the repository root. The directory is created automatically on first use.

To use a custom directory, pass the `directory` parameter to the API functions:

```python
from pathlib import Path
from src.session_store import save_session, load_session

path = save_session(session, directory=Path("/tmp/my-sessions"))
loaded = load_session(session_id, directory=Path("/tmp/my-sessions"))
```

There is no CLI flag to override the session directory.

`load_session()` raises `FileNotFoundError` if the session JSON file does not exist. There is no recovery path for corrupted session files — delete the file and start a new session.

Sessions accumulate indefinitely in `.port_sessions/`. There is no automatic cleanup. Remove stale files manually when no longer needed.
