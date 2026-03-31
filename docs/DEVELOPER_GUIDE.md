# Developer Guide

This guide covers the project structure, code conventions, and the main extension points.

---

## Project Layout

```
claw-code/
├── src/                          # Main Python package
│   ├── __init__.py               # Public API exports
│   ├── main.py                   # CLI entrypoint (argparse)
│   ├── runtime.py                # PortRuntime
│   ├── query_engine.py           # QueryEnginePort
│   ├── models.py                 # Shared dataclasses
│   ├── commands.py               # Command inventory loader
│   ├── tools.py                  # Tool inventory loader
│   ├── permissions.py            # ToolPermissionContext
│   ├── execution_registry.py     # MirroredCommand / MirroredTool
│   ├── session_store.py          # JSON session persistence
│   ├── transcript.py             # TranscriptStore
│   ├── port_manifest.py          # Workspace introspection
│   ├── parity_audit.py           # Python vs. TS surface comparison
│   ├── bootstrap_graph.py        # 7-stage bootstrap model
│   ├── command_graph.py          # Command segmentation
│   ├── tool_pool.py              # Tool pool assembly
│   ├── setup.py                  # WorkspaceSetup / SetupReport
│   ├── deferred_init.py          # Trust-gated initialisation
│   ├── prefetch.py               # Prefetch stubs
│   ├── system_init.py            # System init message builder
│   ├── context.py                # PortContext builder
│   ├── history.py                # HistoryLog
│   ├── cost_tracker.py           # CostTracker stub
│   ├── remote_runtime.py         # SSH / teleport stubs
│   ├── direct_modes.py           # Direct-connect / deep-link stubs
│   ├── reference_data/           # JSON snapshots (read-only reference)
│   │   ├── commands_snapshot.json
│   │   ├── tools_snapshot.json
│   │   ├── archive_surface_snapshot.json
│   │   └── subsystems/           # One JSON file per subsystem (30 total)
│   └── <30 subsystem packages>/  # assistant/, bridge/, utils/, ...
├── tests/
│   └── test_porting_workspace.py # 20 unittest tests
├── docs/                         # Documentation
├── assets/                       # Images for README
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
└── README.md
```

---

## Code Conventions

### Annotations

Every module starts with:

```python
from __future__ import annotations
```

This enables PEP 604-style `X | None` unions and forward references in type hints on Python 3.10+.

### Dataclasses

Value objects use `@dataclass(frozen=True)`. Mutable objects (e.g. `QueryEnginePort`, `PortingBacklog`) use `@dataclass` without `frozen=True`.

```python
@dataclass(frozen=True)
class RoutedMatch:
    kind: str
    name: str
    source_hint: str
    score: int
```

### Snapshot Loading

Functions that load from `reference_data/` JSON files use `functools.lru_cache` so the file is read only once per process:

```python
import json
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=None)
def _load_snapshot() -> list[dict]:
    path = Path(__file__).resolve().parent / 'reference_data' / 'my_snapshot.json'
    return json.loads(path.read_text())
```

The snapshot path should always be resolved relative to `__file__` so it works regardless of the working directory.

### No External Dependencies

The project uses only the Python standard library. Do not introduce `pip` dependencies.

### Return `None` on Not-Found

Lookup functions (`get_command`, `get_tool`, `ExecutionRegistry.command`, `ExecutionRegistry.tool`) return `None` instead of raising on missing entries. Callers are responsible for handling the `None` case.

### Error handling

- JSON snapshot files are expected to be well-formed UTF-8 JSON. Parse errors will raise `json.JSONDecodeError` and propagate uncaught — this is intentional; a corrupt snapshot is a fatal misconfiguration.
- `load_session()` raises `FileNotFoundError` for unknown session IDs.
- `build_port_manifest()` and `build_port_context()` will not raise even if optional directories (e.g. `assets/`, `archive/`) are missing — missing directories yield a count of `0` or `archive_available=False`.

### Root-level mirror files

The following files exist in `src/` primarily to satisfy the parity audit (matching `ARCHIVE_ROOT_FILES` in `parity_audit.py`). They are thin — do not add significant logic to them without a corresponding entry in `ARCHIVE_ROOT_FILES`:

`QueryEngine.py`, `Tool.py`, `query.py`, `ink.py`, `replLauncher.py`, `dialogLaunchers.py`, `interactiveHelpers.py`, `projectOnboardingState.py`, `costHook.py`

---

## Adding a Subsystem Package

All 30 subsystem packages follow the same pattern:

**Step 1** — Create `src/<name>/__init__.py`:

```python
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA_FILE = Path(__file__).resolve().parent.parent / 'reference_data' / 'subsystems' / '<name>.json'


@lru_cache(maxsize=None)
def _load() -> dict:
    return json.loads(_DATA_FILE.read_text())


ARCHIVE_NAME: str = property(lambda _: _load()['archive_name'])  # type: ignore[assignment]
MODULE_COUNT: int = _load()['module_count']
SAMPLE_FILES: list[str] = _load()['sample_files']
PORTING_NOTE: str = _load()['porting_note']
```

*(Follow the pattern in existing packages such as `src/utils/__init__.py`.)*

**Step 2** — Create `src/reference_data/subsystems/<name>.json`:

```json
{
  "archive_name": "<name>",
  "module_count": 5,
  "sample_files": ["example.ts", "index.ts"],
  "porting_note": "One-line description of what this subsystem does."
}
```

**Step 3** — Add a test assertion:

```python
def test_subsystem_packages_expose_archive_metadata(self) -> None:
    from src import <name>
    self.assertGreater(<name>.MODULE_COUNT, 0)
```

---

## Adding Commands or Tools

### Command entries

Edit `src/reference_data/commands_snapshot.json`. Each entry:

```json
{
  "name": "my-command",
  "source_hint": "src/commands/myCommand.ts",
  "responsibility": "One sentence describing what this command does."
}
```

### Tool entries

Edit `src/reference_data/tools_snapshot.json`. Same structure:

```json
{
  "name": "MyTool",
  "source_hint": "src/tools/MyTool.ts",
  "responsibility": "One sentence describing what this tool does."
}
```

After editing, run the full test suite to verify the minimum count assertions still pass:

```bash
python3 -m unittest discover -s tests -v
```

The tests assert `len(PORTED_COMMANDS) >= 150` and `len(PORTED_TOOLS) >= 100`.

---

## Adding a New Tool Implementation

The tool dispatcher in `src/tool_implementations/` routes named tools to real Python handlers. Follow these steps to wire up a new handler.

**Step 1** — Create (or locate) a handler file in `src/tool_implementations/`:

```
src/tool_implementations/my_tool.py
```

**Step 2** — Write the handler function with the required signature:

```python
from __future__ import annotations


def handle_mytool(payload: str) -> str:
    """Handle MyTool calls."""
    import json
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    # Implement tool logic here using params
    result = {"status": "ok", "input": params}

    return json.dumps(result, indent=2)
```

The handler receives the raw payload string and must return a string. Parsing defensively (empty payload, non-JSON payload) prevents hard crashes for malformed calls.

**Step 3** — Import the handler in `src/tool_implementations/__init__.py`:

```python
from .my_tool import handle_mytool
```

**Step 4** — Add an entry to `TOOL_DISPATCH` in the same file:

```python
TOOL_DISPATCH: dict[str, object] = {
    # ... existing entries ...
    "MyTool": handle_mytool,
}
```

The key must match the tool's `name` field exactly as it appears in `tools_snapshot.json`.

**Step 5** — Write tests in `tests/test_tool_implementations.py`:

```python
def test_mytool_basic(self) -> None:
    from src.tool_implementations import dispatch_tool
    result = dispatch_tool("MyTool", '{"key": "value"}')
    self.assertIsNotNone(result)
    self.assertIn("ok", result)
```

**Step 6** — Verify end-to-end via the CLI:

```bash
python -m src.main exec-tool MyTool '{"key": "value"}'
```

A `handled=True` response confirms the dispatcher reached your handler.

---

## Adding a New Command Implementation

The command dispatcher in `src/command_implementations/` routes slash-command names to real Python handlers. The process mirrors the tool pattern above.

**Step 1** — Create (or locate) a handler file in `src/command_implementations/`:

```
src/command_implementations/my_commands.py
```

**Step 2** — Write the handler function:

```python
from __future__ import annotations


def handle_my_command(prompt: str) -> str:
    """Handle the /my-command slash command."""
    return f"my-command received: {prompt!r}"
```

The handler receives the remainder of the slash-command line as `prompt` and returns a string displayed to the user.

**Step 3** — Import in `src/command_implementations/__init__.py`:

```python
from .my_commands import handle_my_command
```

**Step 4** — Add to `COMMAND_DISPATCH`:

```python
COMMAND_DISPATCH: dict[str, object] = {
    # ... existing entries ...
    "my-command": handle_my_command,
}
```

The key must match the command `name` in `commands_snapshot.json`.

**Step 5** — Write tests:

```python
def test_my_command(self) -> None:
    from src.command_implementations import dispatch_command
    result = dispatch_command("my-command", "some input")
    self.assertIsNotNone(result)
```

**Step 6** — Verify:

```bash
python -m src.main exec-command my-command "some input"
```

---

## Using the State Store

`src/stores.py` provides an in-memory store for tools that need to persist state across calls within a single process run. Use it when a tool needs to create, retrieve, or update records that other tools can later access.

### When to use it

- A tool creates a resource (task, agent, team, todo, cron entry) that a second tool needs to look up by ID.
- A tool reads or writes configuration values shared across multiple calls.
- A tool toggles a mode flag (`plan_mode`, `worktree_mode`) that other components observe.

Do **not** use the store as a persistence layer — all state is lost on process restart. For durable storage, write to the filesystem or a session JSON file.

### Importing

```python
from .. import stores
```

From inside a handler file under `src/tool_implementations/` or `src/command_implementations/`, the two-dot relative import resolves to `src/stores.py`.

### Typical handler pattern

```python
from __future__ import annotations

import dataclasses
import json

from .. import stores


def handle_task_create(payload: str) -> str:
    try:
        params = json.loads(payload) if payload.strip() else {}
    except json.JSONDecodeError:
        params = {"input": payload}

    name = params.get("name", "unnamed")
    description = params.get("description", "")

    record = stores.create_task(name, description)
    return json.dumps(dataclasses.asdict(record), indent=2)
```

Key points:

- Call the appropriate CRUD function (`create_task`, `get_task`, `list_tasks`, etc.).
- Serialise the returned dataclass with `dataclasses.asdict()` before passing to `json.dumps()`.
- All store functions return `None` on a not-found lookup — handle that case before serialising.

### Available stores

| Store | Key functions |
|-------|--------------|
| Tasks | `create_task`, `get_task`, `list_tasks`, `update_task`, `record_task_output`, `stop_task` |
| Teams | `create_team`, `get_team`, `list_teams`, `delete_team` |
| Agents | `create_agent`, `get_agent`, `list_agents`, `complete_agent` |
| Todos | `create_todo`, `get_todo`, `list_todos`, `complete_todo`, `delete_todo` |
| Crons | `create_cron`, `list_crons`, `delete_cron` |
| Config | `get_config`, `set_config`, `all_config` |
| Mode flags | `get_mode_flag`, `set_mode_flag` |

See `docs/API_REFERENCE.md` — "State Store" section — for full signatures and field descriptions.

---

## Writing Tests

Tests live in `tests/test_porting_workspace.py` and use Python's built-in `unittest`.

### Unit test pattern

```python
def test_my_feature(self) -> None:
    from src.my_module import my_function
    result = my_function("input")
    self.assertEqual(result.field, "expected")
```

### CLI integration test pattern

```python
def test_my_cli_command(self) -> None:
    result = subprocess.run(
        [sys.executable, '-m', 'src.main', 'my-command', 'arg'],
        check=True,
        capture_output=True,
        text=True,
    )
    self.assertIn('expected text', result.stdout)
```

`check=True` causes the test to fail if the subprocess exits with a non-zero code.

### Conditional test pattern (for optional local resources)

```python
def test_local_archive_feature(self) -> None:
    audit = run_parity_audit()
    if audit.archive_present:
        self.assertEqual(audit.root_file_coverage[0], audit.root_file_coverage[1])
```

---

## Parity Audit Workflow

The parity audit (`src/parity_audit.py`) compares what the Python workspace covers against the archived TypeScript surface using two hardcoded mapping tables:

- **`ARCHIVE_ROOT_FILES`** (18 entries) — maps TypeScript root files to their Python equivalents.
- **`ARCHIVE_DIR_MAPPINGS`** (33 entries) — maps TypeScript top-level directories to Python package names or module files.

The audit checks whether each target exists in `src/` by iterating `CURRENT_ROOT.iterdir()` (top-level only). It does **not** recurse into subdirectories for coverage counting.

To run the audit:

```bash
python3 -m src.main parity-audit
```

If you have the original TypeScript source locally, place it under `archive/` (which is `.gitignore`d) and rerun. The audit sets `archive_present=True` and reports `total_file_ratio` comparing live Python file count against the archived TS file count.

Target parity metrics (from `tests/test_porting_workspace.py`):

- `root_file_coverage[0] == root_file_coverage[1]` (all 18 root file targets present)
- `directory_coverage[0] >= 28` (at least 28 of 33 directory targets present)
- `command_entry_ratio[0] >= 150` (at least 150 commands in snapshot)
- `tool_entry_ratio[0] >= 100` (at least 100 tools in snapshot)

### Adding a new root-level mirror file

1. Create the Python file in `src/`.
2. Add the mapping to `ARCHIVE_ROOT_FILES` in `parity_audit.py`.
3. Run `python3 -m src.main parity-audit` to verify the new file is counted.

### Reference data JSON schemas

**`commands_snapshot.json` and `tools_snapshot.json`** — array of objects:
```json
[
  {
    "name": "ExampleName",
    "source_hint": "path/to/original.ts",
    "responsibility": "One-sentence description."
  }
]
```
All three fields are required strings. File encoding: UTF-8.

**`archive_surface_snapshot.json`** — single object:
```json
{
  "archive_root": "archive/claude_code_ts_snapshot/src",
  "total_ts_like_files": 1902,
  "command_entry_count": 207,
  "tool_entry_count": 184
}
```

**`subsystems/<name>.json`** — single object:
```json
{
  "archive_name": "<name>",
  "module_count": 5,
  "sample_files": ["file1.ts", "file2.ts"],
  "porting_note": "One-line description."
}
```

---

## Session Persistence

Sessions are written as JSON to `.port_sessions/` in the current working directory:

```
.port_sessions/
  a1b2c3d4e5f6...hex32chars.json
  b2c3d4e5f6a1...hex32chars.json
```

Each file:

```json
{
  "session_id": "a1b2c3d4...",
  "messages": ["first prompt", "second prompt"],
  "input_tokens": 18,
  "output_tokens": 42
}
```

The `session_id` is the filename stem — pass it to `load-session` or `QueryEnginePort.from_saved_session()` to restore.

Sessions are never automatically cleaned up. Remove stale files manually or add a cleanup step to your workflow.

---

## Rust Port

A Rust reimplementation is in progress on the `dev/rust` branch. It targets the same architectural abstractions (PortRuntime, QueryEnginePort, inventory loading) with native performance and memory safety. Refer to that branch's README for build instructions.
