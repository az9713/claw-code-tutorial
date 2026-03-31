# Python API Reference

> **Terminology note**
> - *Mirrored* — a command, tool, or module that exists in the registry as a stub pointing at its original TypeScript source path. The Python shim records the name and origin but does not re-implement the logic.
> - *Archived / archive* — the original TypeScript Claude Code source, which may or may not be present locally at `archive/claude_code_ts_snapshot/src/`.
> - *Porting workspace* — this Python repository as a whole: the active re-implementation effort that maps to the archived surface.

All public symbols are importable from the top-level `src` package:

```python
from src import (
    PortRuntime, RuntimeSession,
    QueryEnginePort, TurnResult,
    PortManifest, build_port_manifest,
    StoredSession, load_session, save_session,
    ParityAuditResult, run_parity_audit,
    PORTED_COMMANDS, PORTED_TOOLS,
    build_command_backlog, build_tool_backlog,
    build_system_init_message,
)
```

---

## `PortRuntime`

*`src/runtime.py`*

The top-level orchestrator. Stateless — create a new instance per invocation or reuse freely.

```python
runtime = PortRuntime()
```

### `route_prompt(prompt, limit=5) → list[RoutedMatch]`

Tokenises `prompt` (splitting on whitespace, `/`, and `-`) and scores it against all commands and tools by substring matching. Returns up to `limit` matches, ensuring at least one command and one tool appear when available.

```python
matches = runtime.route_prompt("review MCP tool", limit=5)
for m in matches:
    print(m.kind, m.name, m.score, m.source_hint)
```

**Parameters**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `prompt` | `str` | — | Free-text prompt to route |
| `limit` | `int` | `5` | Maximum number of matches to return |

**Returns** `list[RoutedMatch]`

---

### `bootstrap_session(prompt, limit=5) → RuntimeSession`

Runs the full 7-stage bootstrap lifecycle and returns a `RuntimeSession` containing context, setup, matched commands/tools, streaming events, the turn result, and the path to the persisted session file.

```python
session = runtime.bootstrap_session("review MCP tool")
print(session.as_markdown())
```

---

### `run_turn_loop(prompt, limit=5, max_turns=3, structured_output=False) → list[TurnResult]`

Runs a stateful multi-turn loop. Each turn submits the original prompt (suffixed with `[turn N]` for subsequent turns). Stops early if `stop_reason != "completed"`.

```python
results = runtime.run_turn_loop("review MCP tool", max_turns=3)
for i, r in enumerate(results, 1):
    print(f"Turn {i}: {r.stop_reason}")
```

---

## `RoutedMatch`

*`src/runtime.py`* — frozen dataclass

| Field | Type | Description |
|-------|------|-------------|
| `kind` | `str` | `"command"` or `"tool"` |
| `name` | `str` | Entry name (e.g. `"review"`, `"MCPTool"`) |
| `source_hint` | `str` | Original TypeScript file path |
| `score` | `int` | Token overlap score (higher = better match) |

---

## `QueryEnginePort`

*`src/query_engine.py`*

The conversation engine. Holds mutable session state (turn history, usage, transcript).

### Factory methods

#### `QueryEnginePort.from_workspace() → QueryEnginePort`

Creates a new engine with a fresh session UUID and a manifest built from the live `src/` directory.

```python
engine = QueryEnginePort.from_workspace()
```

#### `QueryEnginePort.from_saved_session(session_id) → QueryEnginePort`

Restores an engine from a previously saved session.

```python
engine = QueryEnginePort.from_saved_session("a1b2c3d4...")
```

---

### `submit_message(prompt, matched_commands=(), matched_tools=(), denied_tools=()) → TurnResult`

Submits one turn. Enforces `max_turns` and `max_budget_tokens` limits. Appends the prompt to `mutable_messages` and `transcript_store`. Triggers compaction when needed.

```python
result = engine.submit_message(
    "review the auth module",
    matched_commands=("review",),
    matched_tools=(),
    denied_tools=(),
)
print(result.output)
print(result.stop_reason)   # "completed" | "max_turns_reached" | "max_budget_reached"
```

---

### `stream_submit_message(prompt, ...) → Generator[dict, None, None]`

Generator variant of `submit_message`. Yields event dictionaries in order:

1. `{"type": "message_start", "session_id": ..., "prompt": ...}`
2. `{"type": "command_match", "commands": (...)}` *(if commands matched)*
3. `{"type": "tool_match", "tools": (...)}` *(if tools matched)*
4. `{"type": "permission_denial", "denials": [...]}` *(if tools denied)*
5. `{"type": "message_delta", "text": ...}`
6. `{"type": "message_stop", "usage": {"input_tokens": ..., "output_tokens": ...}, "stop_reason": ..., "transcript_size": ...}`

```python
for event in engine.stream_submit_message("review MCP tool"):
    print(event["type"])
```

---

### `persist_session() → str`

Flushes the transcript and writes the session to `.port_sessions/<uuid>.json`. Returns the file path as a string.

```python
path = engine.persist_session()
```

---

### `render_summary() → str`

Returns a Markdown string summarising the workspace (manifest, command/tool surface counts, session state).

---

### Instance attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `manifest` | `PortManifest` | Live workspace manifest |
| `config` | `QueryEngineConfig` | Engine configuration (mutable) |
| `session_id` | `str` | Hex UUID for this session |
| `mutable_messages` | `list[str]` | Submitted prompts in turn order |
| `permission_denials` | `list[PermissionDenial]` | Accumulated denials |
| `total_usage` | `UsageSummary` | Cumulative token counts |
| `transcript_store` | `TranscriptStore` | Transcript with compaction support |

---

## `QueryEngineConfig`

*`src/query_engine.py`* — frozen dataclass

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_turns` | `int` | `8` | Maximum turns before `max_turns_reached` |
| `max_budget_tokens` | `int` | `2000` | Token budget (word-count approximation) |
| `compact_after_turns` | `int` | `12` | Trim `mutable_messages` to last N after this many turns |
| `structured_output` | `bool` | `False` | Emit JSON instead of plain text |
| `structured_retry_limit` | `int` | `2` | JSON serialisation retry count |

```python
from src.query_engine import QueryEngineConfig
config = QueryEngineConfig(max_turns=4, structured_output=True)
```

---

## `TurnResult`

*`src/query_engine.py`* — frozen dataclass

| Field | Type | Description |
|-------|------|-------------|
| `prompt` | `str` | The prompt submitted this turn |
| `output` | `str` | Formatted summary output |
| `matched_commands` | `tuple[str, ...]` | Command names matched this turn |
| `matched_tools` | `tuple[str, ...]` | Tool names matched this turn |
| `permission_denials` | `tuple[PermissionDenial, ...]` | Denials this turn |
| `usage` | `UsageSummary` | Cumulative usage after this turn |
| `stop_reason` | `str` | `"completed"` \| `"max_turns_reached"` \| `"max_budget_reached"` |

---

## `RuntimeSession`

*`src/runtime.py`* — dataclass

| Field | Type | Description |
|-------|------|-------------|
| `prompt` | `str` | Original prompt |
| `context` | `PortContext` | File counts and paths |
| `setup` | `WorkspaceSetup` | Python version, platform, test command |
| `setup_report` | `SetupReport` | Full setup report including deferred init |
| `system_init_message` | `str` | System init string (startup step list) |
| `history` | `HistoryLog` | Ordered audit-trail entries |
| `routed_matches` | `list[RoutedMatch]` | Routing results |
| `turn_result` | `TurnResult` | Result of the first query engine turn |
| `command_execution_messages` | `tuple[str, ...]` | Shim outputs for matched commands |
| `tool_execution_messages` | `tuple[str, ...]` | Shim outputs for matched tools |
| `stream_events` | `tuple[dict, ...]` | Captured streaming events |
| `persisted_session_path` | `str` | Path to the written session JSON |

#### `as_markdown() → str`

Returns the full session as a Markdown report.

---

## `PortManifest`

*`src/port_manifest.py`* — frozen dataclass

| Field | Type | Description |
|-------|------|-------------|
| `src_root` | `Path` | Absolute path to `src/` |
| `total_python_files` | `int` | Total `.py` files found recursively |
| `top_level_modules` | `tuple[Subsystem, ...]` | Modules sorted by file count |

#### `to_markdown() → str`

Returns a Markdown listing of top-level modules.

#### `build_port_manifest(src_root=None) → PortManifest`

Factory function. Uses `src/` by default.

---

## `ToolPermissionContext`

*`src/permissions.py`* — frozen dataclass

| Field | Type | Description |
|-------|------|-------------|
| `deny_names` | `frozenset[str]` | Exact names to block (lowercased) |
| `deny_prefixes` | `tuple[str, ...]` | Prefixes to block (lowercased) |

#### `from_iterables(deny_names=None, deny_prefixes=None) → ToolPermissionContext`

Convenience constructor from plain lists.

```python
ctx = ToolPermissionContext.from_iterables(
    deny_names=["BashTool"],
    deny_prefixes=["mcp"],
)
```

#### `blocks(tool_name) → bool`

Returns `True` if `tool_name` matches any deny rule.

---

## Data Models (`src/models.py`)

### `Subsystem` — frozen dataclass

| Field | Type |
|-------|------|
| `name` | `str` |
| `path` | `str` |
| `file_count` | `int` |
| `notes` | `str` |

### `PortingModule` — frozen dataclass

| Field | Type | Default |
|-------|------|---------|
| `name` | `str` | — |
| `responsibility` | `str` | — |
| `source_hint` | `str` | — |
| `status` | `str` | `"planned"` |

### `PermissionDenial` — frozen dataclass

| Field | Type |
|-------|------|
| `tool_name` | `str` |
| `reason` | `str` |

### `UsageSummary` — frozen dataclass

| Field | Type | Default |
|-------|------|---------|
| `input_tokens` | `int` | `0` |
| `output_tokens` | `int` | `0` |

#### `add_turn(prompt, output) → UsageSummary`

Returns a new `UsageSummary` with word-count increments from the given prompt and output strings.

### `PortingBacklog` — dataclass

| Field | Type |
|-------|------|
| `title` | `str` |
| `modules` | `list[PortingModule]` |

#### `summary_lines() → list[str]`

---

## Execution Registry (`src/execution_registry.py`)

### `build_execution_registry() → ExecutionRegistry`

Builds wrappers for all 207 commands and 184 tools.

### `ExecutionRegistry` — frozen dataclass

| Field | Type |
|-------|------|
| `commands` | `tuple[MirroredCommand, ...]` |
| `tools` | `tuple[MirroredTool, ...]` |

#### `command(name) → MirroredCommand | None`
#### `tool(name) → MirroredTool | None`

Case-insensitive lookup. Returns `None` if not found.

### `MirroredCommand` — frozen dataclass

| Field | Type |
|-------|------|
| `name` | `str` |
| `source_hint` | `str` |

#### `execute(prompt) → str`

Returns a placeholder message string.

### `MirroredTool` — frozen dataclass

Same fields and `execute(payload) → str` method as `MirroredCommand`.

---

## Session Store (`src/session_store.py`)

### `StoredSession` — frozen dataclass

| Field | Type |
|-------|------|
| `session_id` | `str` |
| `messages` | `tuple[str, ...]` |
| `input_tokens` | `int` |
| `output_tokens` | `int` |

### `save_session(session, directory=None) → Path`

Writes `<session_id>.json` to `directory` (default: `.port_sessions/`). Creates the directory if needed.

### `load_session(session_id, directory=None) → StoredSession`

Reads `<session_id>.json` from `directory`. Raises `FileNotFoundError` if not present.

---

## Transcript Store (`src/transcript.py`)

Tracks the in-memory turn history separately from `mutable_messages`.

Key behaviours:

- `append(entry)` — adds an entry.
- `compact(keep_last)` — truncates to the last `keep_last` entries in place.
- `flush()` — marks `flushed = True` (called by `persist_session()`).
- `replay() → tuple[str, ...]` — returns all entries as a tuple.

---

## Parity Audit (`src/parity_audit.py`)

### `run_parity_audit() → ParityAuditResult`

Compares the Python workspace against the archived TypeScript surface. When no local archive is present at `archive/claude_code_ts_snapshot/src/`, metrics are still computed using the JSON snapshot counts.

The audit checks two mappings defined at the top of `parity_audit.py`:

- **`ARCHIVE_ROOT_FILES`** — 18 root-level TypeScript files and their Python equivalents (e.g. `QueryEngine.ts` → `QueryEngine.py`). Root file coverage is whether these Python equivalents exist in `src/`.
- **`ARCHIVE_DIR_MAPPINGS`** — 33 top-level directories/files in the archive and their Python counterparts. Directory coverage is whether the Python counterparts exist in `src/`.

### `ParityAuditResult` — frozen dataclass

| Field | Type | Description |
|-------|------|-------------|
| `archive_present` | `bool` | Whether a local TS archive was found at `archive/claude_code_ts_snapshot/src/` |
| `root_file_coverage` | `tuple[int, int]` | `(matched, total)` — how many of the 18 root file targets exist in `src/` |
| `directory_coverage` | `tuple[int, int]` | `(matched, total)` — how many of the 33 directory targets exist in `src/` |
| `total_file_ratio` | `tuple[int, int]` | `(current_python_files, total_ts_like_files)` — total Python vs total archived TS files |
| `command_entry_ratio` | `tuple[int, int]` | `(snapshot_count, archive_count)` — entries in commands_snapshot vs archive |
| `tool_entry_ratio` | `tuple[int, int]` | `(snapshot_count, archive_count)` — entries in tools_snapshot vs archive |
| `missing_root_targets` | `tuple[str, ...]` | Python filenames expected but absent from `src/` |
| `missing_directory_targets` | `tuple[str, ...]` | Directory/file targets expected but absent from `src/` |

#### `to_markdown() → str`

Returns a Markdown report. When `archive_present=False`, outputs a single notice line. When the archive is present, outputs all coverage metrics and lists any missing targets.

---

## Commands API (`src/commands.py`)

### `load_command_snapshot() → tuple[PortingModule, ...]`

Loads `commands_snapshot.json` into a tuple of `PortingModule` objects. Cached with `lru_cache` — the file is read only once per process. All modules have `status='mirrored'`.

### `PORTED_COMMANDS`

Module-level constant: the full tuple of 207 mirrored command entries, loaded at import time.

### `built_in_command_names() → frozenset[str]`

Returns a `frozenset` of all command names. Cached.

### `build_command_backlog() → PortingBacklog`

Returns a `PortingBacklog` titled `'Command surface'` containing all 207 entries.

### `command_names() → list[str]`

Returns a plain list of all command names (not cached).

### `get_command(name) → PortingModule | None`

Case-insensitive lookup by name. Returns `None` if not found.

### `get_commands(cwd=None, include_plugin_commands=True, include_skill_commands=True) → tuple[PortingModule, ...]`

Returns filtered commands. When `include_plugin_commands=False`, excludes entries whose `source_hint` contains `"plugin"`. When `include_skill_commands=False`, excludes entries whose `source_hint` contains `"skills"`. `cwd` is accepted but not currently used.

### `find_commands(query, limit=20) → list[PortingModule]`

Returns up to `limit` commands whose `name` or `source_hint` contains `query` (case-insensitive substring match).

### `execute_command(name, prompt='') → CommandExecution`

Executes the shim for the named command. Returns a `CommandExecution` with `handled=True` and a placeholder message if the command exists; `handled=False` with an error message if not found.

### `render_command_index(limit=20, query=None) → str`

Returns a formatted Markdown-style string listing command entries. If `query` is given, filters using `find_commands()`.

### `CommandExecution` — frozen dataclass

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Command name looked up |
| `source_hint` | `str` | Original TS file path (empty if not found) |
| `prompt` | `str` | The prompt passed to execute |
| `handled` | `bool` | `True` if the command was found and dispatched |
| `message` | `str` | Human-readable result or error |

---

## Tools API (`src/tools.py`)

### `load_tool_snapshot() → tuple[PortingModule, ...]`

Loads `tools_snapshot.json`. Cached with `lru_cache`.

### `PORTED_TOOLS`

Module-level constant: the full tuple of 184 mirrored tool entries.

### `build_tool_backlog() → PortingBacklog`

Returns a `PortingBacklog` titled `'Tool surface'` containing all 184 entries.

### `tool_names() → list[str]`

Returns a plain list of all tool names.

### `get_tool(name) → PortingModule | None`

Case-insensitive lookup by name.

### `filter_tools_by_permission_context(tools, permission_context=None) → tuple[PortingModule, ...]`

Applies a `ToolPermissionContext` deny-list to a tuple of tools. If `permission_context` is `None`, the input is returned unchanged.

### `get_tools(simple_mode=False, include_mcp=True, permission_context=None) → tuple[PortingModule, ...]`

Assembles the filtered tool set. Filter pipeline:
1. If `simple_mode=True`: keep only `BashTool`, `FileReadTool`, `FileEditTool`.
2. If `include_mcp=False`: drop tools with `"mcp"` in name or source_hint (case-insensitive).
3. Apply `permission_context` deny-list.

### `find_tools(query, limit=20) → list[PortingModule]`

Case-insensitive substring search across `name` and `source_hint`.

### `execute_tool(name, payload='') → ToolExecution`

Executes the shim for the named tool.

### `render_tool_index(limit=20, query=None) → str`

Formatted listing of tool entries, with optional query filter.

### `ToolExecution` — frozen dataclass

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Tool name looked up |
| `source_hint` | `str` | Original TS file path (empty if not found) |
| `payload` | `str` | The payload passed to execute |
| `handled` | `bool` | `True` if the tool was found and dispatched |
| `message` | `str` | Human-readable result or error |

---

## Bootstrap Graph (`src/bootstrap_graph.py`)

### `build_bootstrap_graph() → BootstrapGraph`

Returns the 7-stage bootstrap graph.

### `BootstrapGraph` — frozen dataclass

| Field | Type |
|-------|------|
| `stages` | `tuple[str, ...]` |

#### `as_markdown() → str`

Returns a `# Bootstrap Graph` Markdown section listing all stages as bullet points.

---

## Command Graph (`src/command_graph.py`)

### `build_command_graph() → CommandGraph`

Classifies all commands into three categories based on `source_hint`:
- Contains `"plugin"` → `plugin_like`
- Contains `"skills"` → `skill_like`
- Neither → `builtins`

### `CommandGraph` — frozen dataclass

| Field | Type |
|-------|------|
| `builtins` | `tuple[PortingModule, ...]` |
| `plugin_like` | `tuple[PortingModule, ...]` |
| `skill_like` | `tuple[PortingModule, ...]` |

#### `flattened() → tuple[PortingModule, ...]`

Returns `builtins + plugin_like + skill_like` as a single tuple.

#### `as_markdown() → str`

Returns a `# Command Graph` section with counts for each category.

---

## Tool Pool (`src/tool_pool.py`)

### `assemble_tool_pool(simple_mode=False, include_mcp=True, permission_context=None) → ToolPool`

Assembles a `ToolPool` by calling `get_tools()` with the given parameters.

### `ToolPool` — frozen dataclass

| Field | Type |
|-------|------|
| `tools` | `tuple[PortingModule, ...]` |
| `simple_mode` | `bool` |
| `include_mcp` | `bool` |

#### `as_markdown() → str`

Returns a `# Tool Pool` section listing simple_mode, include_mcp, tool count, and the first 15 tool names.

---

## Setup (`src/setup.py`)

### `run_setup(cwd=None, trusted=True) → SetupReport`

Runs the three prefetch operations and deferred init, then returns a complete setup report. `cwd` defaults to the repository root.

### `build_workspace_setup() → WorkspaceSetup`

Returns a `WorkspaceSetup` with live Python version and platform information.

### `WorkspaceSetup` — frozen dataclass

| Field | Type | Description |
|-------|------|-------------|
| `python_version` | `str` | Python version string (e.g. `"3.11.5"`) |
| `implementation` | `str` | Python implementation (e.g. `"CPython"`) |
| `platform_name` | `str` | Full platform string from `platform.platform()` |
| `test_command` | `str` | `"python3 -m unittest discover -s tests -v"` |

#### `startup_steps() → tuple[str, ...]`

Returns the 6 named startup steps as a tuple of strings.

### `SetupReport` — frozen dataclass

| Field | Type | Description |
|-------|------|-------------|
| `setup` | `WorkspaceSetup` | Platform information |
| `prefetches` | `tuple[PrefetchResult, ...]` | Results of the 3 prefetch operations |
| `deferred_init` | `DeferredInitResult` | Trust-gated subsystem init state |
| `trusted` | `bool` | Whether the session was initialised in trusted mode |
| `cwd` | `Path` | Working directory used during setup |

#### `as_markdown() → str`

Returns a `# Setup Report` Markdown section.

---

## Prefetch (`src/prefetch.py`)

### `start_mdm_raw_read() → PrefetchResult`
### `start_keychain_prefetch() → PrefetchResult`
### `start_project_scan(root) → PrefetchResult`

### `PrefetchResult` — frozen dataclass

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Identifier (`"mdm_raw_read"`, `"keychain_prefetch"`, `"project_scan"`) |
| `started` | `bool` | Always `True` in the current implementation |
| `detail` | `str` | Human-readable description of what the prefetch simulated |

---

## Deferred Init (`src/deferred_init.py`)

### `run_deferred_init(trusted) → DeferredInitResult`

When `trusted=True`, all four subsystem flags are `True`. When `trusted=False`, all are `False`.

### `DeferredInitResult` — frozen dataclass

| Field | Type | Description |
|-------|------|-------------|
| `trusted` | `bool` | The trust flag passed in |
| `plugin_init` | `bool` | Whether plugins are initialised |
| `skill_init` | `bool` | Whether skills are initialised |
| `mcp_prefetch` | `bool` | Whether MCP server connections are started |
| `session_hooks` | `bool` | Whether lifecycle hooks are registered |

#### `as_lines() → tuple[str, ...]`

Returns 4 formatted bullet strings, e.g. `"- plugin_init=True"`.

---

## Context (`src/context.py`)

### `build_port_context(base=None) → PortContext`

Scans the filesystem relative to `base` (defaults to repository root) and counts files.

### `render_context(context) → str`

Returns a multi-line string representation of the context fields.

### `PortContext` — frozen dataclass

| Field | Type | Description |
|-------|------|-------------|
| `source_root` | `Path` | Absolute path to `src/` |
| `tests_root` | `Path` | Absolute path to `tests/` |
| `assets_root` | `Path` | Absolute path to `assets/` |
| `archive_root` | `Path` | Absolute path to `archive/claude_code_ts_snapshot/src/` |
| `python_file_count` | `int` | Count of `.py` files under `source_root` |
| `test_file_count` | `int` | Count of `.py` files under `tests_root` |
| `asset_file_count` | `int` | Count of all files under `assets_root` |
| `archive_available` | `bool` | Whether `archive_root` exists on disk |

---

## History (`src/history.py`)

### `HistoryLog` — dataclass

Session-scoped ordered audit log.

| Field | Type |
|-------|------|
| `events` | `list[HistoryEvent]` |

#### `add(title, detail) → None`

Appends a `HistoryEvent(title, detail)` to `events`.

#### `as_markdown() → str`

Returns a `# Session History` Markdown section listing all events as `- title: detail` lines.

### `HistoryEvent` — frozen dataclass

| Field | Type |
|-------|------|
| `title` | `str` |
| `detail` | `str` |

---

## Remote Runtime (`src/remote_runtime.py`)

### `run_remote_mode(target) → RuntimeModeReport`
### `run_ssh_mode(target) → RuntimeModeReport`
### `run_teleport_mode(target) → RuntimeModeReport`

### `RuntimeModeReport` — frozen dataclass

| Field | Type | Description |
|-------|------|-------------|
| `mode` | `str` | `"remote"`, `"ssh"`, or `"teleport"` |
| `connected` | `bool` | Always `True` in current implementation |
| `detail` | `str` | Human-readable description |

#### `as_text() → str`

Returns:
```
mode=<mode>
connected=True
detail=<detail>
```

---

## Direct Modes (`src/direct_modes.py`)

### `run_direct_connect(target) → DirectModeReport`
### `run_deep_link(target) → DirectModeReport`

### `DirectModeReport` — frozen dataclass

| Field | Type | Description |
|-------|------|-------------|
| `mode` | `str` | `"direct-connect"` or `"deep-link"` |
| `target` | `str` | The target string passed in |
| `active` | `bool` | Always `True` in current implementation |

#### `as_text() → str`

Returns:
```
mode=<mode>
target=<target>
active=True
```

---

## System Init (`src/system_init.py`)

### `build_system_init_message(trusted=True) → str`

Runs `run_setup(trusted=trusted)`, loads commands and tools, and returns a `# System Init` Markdown string containing: trusted status, built-in command name count, loaded command count, loaded tool count, and the 6 startup steps.

---

## Cost Tracking (`src/cost_tracker.py`, `src/costHook.py`)

### `CostTracker` — dataclass

| Field | Type |
|-------|------|
| `total_units` | `int` (default `0`) |
| `events` | `list[str]` (default `[]`) |

#### `record(label, units) → None`

Appends `f"{label}:{units}"` to `events` and increments `total_units` by `units`.

### `apply_cost_hook(tracker, label, units) → CostTracker`

*`src/costHook.py`*

Calls `tracker.record(label, units)` and returns the tracker. Designed as a hook-compatible wrapper that both mutates and returns the tracker for chaining.

---

## QueryEngineRuntime (`src/QueryEngine.py`)

> **Note**: This module is a root-level mirror of the archived `QueryEngine.ts`. It exists to satisfy the parity audit mapping. Prefer `QueryEnginePort` from `src/query_engine.py` for all new code.

### `QueryEngineRuntime(QueryEnginePort)`

Subclass of `QueryEnginePort` that adds a `route()` method.

#### `route(prompt, limit=5) → str`

Calls `PortRuntime().route_prompt(prompt, limit)` and formats the result as a `# Query Engine Route` Markdown string.

---

## ToolDefinition (`src/Tool.py`)

> **Note**: Root-level mirror of the archived `Tool.ts`. For the full tool registry, use `src/tools.py`.

### `ToolDefinition` — frozen dataclass

| Field | Type |
|-------|------|
| `name` | `str` |
| `purpose` | `str` |

### `DEFAULT_TOOLS`

Tuple of two `ToolDefinition` entries used in porting workspace bootstrap:
- `ToolDefinition('port_manifest', 'Summarize the active Python workspace')`
- `ToolDefinition('query_engine', 'Render a Python-first porting summary')`

---

## Query Types (`src/query.py`)

> **Note**: Root-level mirror of the archived `query.ts`.

### `QueryRequest` — frozen dataclass

| Field | Type |
|-------|------|
| `prompt` | `str` |

### `QueryResponse` — frozen dataclass

| Field | Type |
|-------|------|
| `text` | `str` |

---

## Task (`src/task.py`)

### `PortingTask` — frozen dataclass

| Field | Type |
|-------|------|
| `name` | `str` |
| `description` | `str` |

### `default_tasks() → list[PortingTask]`

*`src/tasks.py`*

Returns three predefined porting tasks:
1. `root-module-parity` — Mirror the root module surface
2. `directory-parity` — Mirror top-level subsystem names as Python packages
3. `parity-audit` — Continuously measure parity against the local archive

---

## UI Utilities

### `render_markdown_panel(text) → str`

*`src/ink.py`* — Root-level mirror of the archived `ink.ts`.

Wraps `text` in a `===...===` border (40 `=` characters per line). Used for terminal Markdown rendering.

### `bulletize(items) → str`

*`src/interactiveHelpers.py`*

Converts a list of strings to a `\n`-joined bullet list (`- item`).

### `build_repl_banner() → str`

*`src/replLauncher.py`*

Returns a placeholder string directing users to `python3 -m src.main summary`. The interactive REPL is not yet implemented.

---

## Dialog Launchers (`src/dialogLaunchers.py`)

### `DialogLauncher` — frozen dataclass

| Field | Type |
|-------|------|
| `name` | `str` |
| `description` | `str` |

### `DEFAULT_DIALOGS`

Tuple of two `DialogLauncher` entries:
- `DialogLauncher('summary', 'Launch the Markdown summary view')`
- `DialogLauncher('parity_audit', 'Launch the parity audit view')`

---

## Project Onboarding (`src/projectOnboardingState.py`)

### `ProjectOnboardingState` — dataclass

| Field | Type | Default |
|-------|------|---------|
| `has_readme` | `bool` | — |
| `has_tests` | `bool` | — |
| `python_first` | `bool` | `True` |

Tracks the onboarding completion state for a new project workspace. Not frozen — fields are expected to be updated as onboarding progresses.

---

## Subsystem Packages

Each of the 30 subsystem packages in `src/` (`assistant`, `bootstrap`, `bridge`, ...) exposes four module-level constants loaded from its corresponding `src/reference_data/subsystems/<name>.json` file:

| Export | Type | Description |
|--------|------|-------------|
| `ARCHIVE_NAME` | `str` | Name of the subsystem in the original TypeScript archive |
| `MODULE_COUNT` | `int` | Number of TypeScript modules in the archived subsystem |
| `SAMPLE_FILES` | `list[str]` | Representative file names from the archived subsystem |
| `PORTING_NOTE` | `str` | One-line description of what the subsystem does |

```python
from src import assistant, bridge, utils

print(assistant.MODULE_COUNT)   # 1
print(utils.MODULE_COUNT)       # 564
print(bridge.SAMPLE_FILES)      # ['bridgeApi.ts', 'bridgeMain.ts', ...]
```

---

## State Store (`src/stores.py`)

In-memory runtime state for tasks, teams, agents, todos, cron entries, config values, and mode flags. All state is process-local and is reset when the process exits — nothing is written to disk.

### Dataclasses

All store records are `@dataclass(frozen=True)`. Use `dataclasses.replace()` to produce updated copies (the store functions do this internally).

#### `TaskRecord`

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | `str` | 12-character hex UUID |
| `name` | `str` | Short display name |
| `description` | `str` | Longer task description |
| `status` | `str` | `"pending"` \| `"in_progress"` \| `"completed"` \| `"stopped"` |
| `output` | `str` | Captured task output (default `''`) |

#### `TeamRecord`

| Field | Type | Description |
|-------|------|-------------|
| `team_id` | `str` | 12-character hex UUID |
| `name` | `str` | Team display name |
| `member_names` | `tuple[str, ...]` | Ordered member names |

#### `AgentRecord`

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | `str` | 12-character hex UUID |
| `prompt` | `str` | Prompt the agent was spawned with |
| `status` | `str` | `"running"` \| `"completed"` |
| `result` | `str` | Agent output once complete (default `''`) |
| `parent_id` | `str` | ID of spawning agent, or `''` for root agents |

#### `TodoItem`

| Field | Type | Description |
|-------|------|-------------|
| `todo_id` | `str` | 12-character hex UUID |
| `content` | `str` | Todo description text |
| `done` | `bool` | Completion flag (default `False`) |

#### `CronEntry`

| Field | Type | Description |
|-------|------|-------------|
| `cron_id` | `str` | 12-character hex UUID |
| `schedule` | `str` | Cron schedule expression (e.g. `"0 * * * *"`) |
| `command` | `str` | Command string to run on schedule |

---

### Module-Level Stores

The following module-level dicts hold live state. They are intentionally private (prefixed `_`); all access should go through the public CRUD functions below.

| Variable | Type | Initial value |
|----------|------|---------------|
| `_tasks` | `dict[str, TaskRecord]` | `{}` |
| `_teams` | `dict[str, TeamRecord]` | `{}` |
| `_agents` | `dict[str, AgentRecord]` | `{}` |
| `_todos` | `dict[str, TodoItem]` | `{}` |
| `_crons` | `dict[str, CronEntry]` | `{}` |
| `_config` | `dict[str, str]` | `{}` |
| `_mode_flags` | `dict[str, bool]` | `{"plan_mode": False, "worktree_mode": False}` |

State is **not persisted**. Restarting the process clears all stores.

---

### Task CRUD

#### `create_task(name: str, description: str) -> TaskRecord`

Creates a new task with `status='pending'` and an auto-generated `task_id`. Stores and returns the record.

#### `get_task(task_id: str) -> TaskRecord | None`

Returns the task for the given ID, or `None` if not found.

#### `list_tasks() -> tuple[TaskRecord, ...]`

Returns a snapshot of all tasks as an immutable tuple.

#### `update_task(task_id: str, status: str) -> TaskRecord | None`

Updates the `status` field. Returns the updated record, or `None` if the task does not exist.

#### `record_task_output(task_id: str, output: str) -> TaskRecord | None`

Stores output text against a task. Returns the updated record, or `None` if not found.

#### `stop_task(task_id: str) -> TaskRecord | None`

Convenience wrapper — calls `update_task(task_id, 'stopped')`.

---

### Team CRUD

#### `create_team(name: str, members: list[str]) -> TeamRecord`

Creates a team. `members` is stored as a `tuple[str, ...]`.

#### `get_team(team_id: str) -> TeamRecord | None`

Lookup by ID. Returns `None` if not found.

#### `list_teams() -> tuple[TeamRecord, ...]`

Returns all teams as a tuple.

#### `delete_team(team_id: str) -> bool`

Removes the team. Returns `True` if found and deleted, `False` if not found.

---

### Agent CRUD

#### `create_agent(prompt: str, parent_id: str = '') -> AgentRecord`

Spawns an agent record with `status='running'`. Optionally links to a parent agent via `parent_id`.

#### `get_agent(agent_id: str) -> AgentRecord | None`

Lookup by ID.

#### `list_agents() -> tuple[AgentRecord, ...]`

Returns all agent records.

#### `complete_agent(agent_id: str, result: str) -> AgentRecord | None`

Marks the agent `status='completed'` and records the `result`. Returns the updated record, or `None` if not found.

---

### Todo CRUD

#### `create_todo(content: str) -> TodoItem`

Creates a todo with `done=False`.

#### `get_todo(todo_id: str) -> TodoItem | None`

Lookup by ID.

#### `list_todos() -> tuple[TodoItem, ...]`

Returns all todo items.

#### `complete_todo(todo_id: str) -> TodoItem | None`

Sets `done=True`. Returns the updated item, or `None` if not found.

#### `delete_todo(todo_id: str) -> bool`

Removes the todo. Returns `True` on success, `False` if not found.

---

### Cron CRUD

#### `create_cron(schedule: str, command: str) -> CronEntry`

Registers a cron entry.

#### `list_crons() -> tuple[CronEntry, ...]`

Returns all cron entries.

#### `delete_cron(cron_id: str) -> bool`

Removes a cron entry. Returns `True` on success, `False` if not found.

---

### Config

#### `get_config(key: str, default: str = '') -> str`

Returns the config value for `key`, or `default` if not set.

#### `set_config(key: str, value: str) -> None`

Stores or overwrites a config value.

#### `all_config() -> dict[str, str]`

Returns a shallow copy of the entire config dict.

---

### Mode Flags

Pre-seeded with `"plan_mode"` and `"worktree_mode"`, both defaulting to `False`.

#### `get_mode_flag(key: str) -> bool`

Returns the flag value, or `False` if the key has never been set.

#### `set_mode_flag(key: str, value: bool) -> None`

Sets a boolean mode flag.

---

## Tool Dispatcher (`src/tool_implementations/`)

### `TOOL_DISPATCH: dict[str, Callable[[str], str]]`

Maps tool names to handler callables. Each handler has the signature `(payload: str) -> str`. The dict is populated at import time by explicit assignments in `src/tool_implementations/__init__.py`.

Registered tools (as of the current implementation):

`BashTool`, `FileReadTool`, `FileWriteTool`, `FileEditTool`, `GlobTool`, `GrepTool`, `TaskCreateTool`, `TaskGetTool`, `TaskListTool`, `TaskUpdateTool`, `TaskOutputTool`, `TaskStopTool`, `TeamCreateTool`, `TeamDeleteTool`, `SendMessageTool`, `AgentTool`, `runAgent`, `forkSubagent`, `spawnMultiAgent`, `WebFetchTool`, `WebSearchTool`, `AskUserQuestionTool`, `TodoWriteTool`, `ConfigTool`, `ToolSearchTool`, `EnterPlanModeTool`, `ExitPlanModeV2Tool`, `EnterWorktreeTool`, `ExitWorktreeTool`, `NotebookEditTool`, `CronCreateTool`, `CronDeleteTool`, `CronListTool`

### `dispatch_tool(name: str, payload: str) -> str | None`

Looks up `name` in `TOOL_DISPATCH` and calls the registered handler with `payload`. Returns the handler's return value (a `str`), or `None` if no handler is registered for `name`.

```python
from src.tool_implementations import dispatch_tool

result = dispatch_tool("BashTool", '{"command": "echo hello"}')
# Returns the handler output string, or None if not registered
```

### Handler registration

To add a handler, import it in `src/tool_implementations/__init__.py` and add an entry to `TOOL_DISPATCH`:

```python
from .my_tool import handle_my_tool

TOOL_DISPATCH: dict[str, object] = {
    # ... existing entries ...
    "MyTool": handle_my_tool,
}
```

### Relationship to `execute_tool()`

`execute_tool()` in `src/tools.py` calls `dispatch_tool()` after resolving the tool name through the snapshot registry. If `dispatch_tool()` returns a non-`None` result, `execute_tool()` returns a `ToolExecution` with `handled=True` and that result as `message`. If `dispatch_tool()` returns `None` (no handler registered), `execute_tool()` falls back to a mirrored-tool placeholder message.

---

## Command Dispatcher (`src/command_implementations/`)

### `COMMAND_DISPATCH: dict[str, Callable[[str], str]]`

Maps slash-command names to handler callables. Each handler has the signature `(prompt: str) -> str`. Populated at import time in `src/command_implementations/__init__.py`.

Registered commands (as of the current implementation):

`help`, `version`, `clear`, `compact`, `status`, `cost`, `model`, `memory`, `session`, `summary`, `doctor`, `config`, `permissions`, `hooks`, `skills`, `mcp`, `tasks`

### `dispatch_command(name: str, prompt: str) -> str | None`

Looks up `name` in `COMMAND_DISPATCH` and calls the handler with `prompt`. Returns the handler's return value, or `None` if no handler is registered.

```python
from src.command_implementations import dispatch_command

result = dispatch_command("help", "")
# Returns the handler output string, or None if not registered
```

### Handler registration

Import and add to `COMMAND_DISPATCH` in `src/command_implementations/__init__.py`:

```python
from .my_commands import handle_my_command

COMMAND_DISPATCH: dict[str, object] = {
    # ... existing entries ...
    "my-command": handle_my_command,
}
```

### Relationship to `execute_command()`

`execute_command()` in `src/commands.py` calls `dispatch_command()` after resolving the command through the snapshot registry. A non-`None` result produces a `CommandExecution` with `handled=True`. A `None` result falls back to a mirrored-command placeholder message.
