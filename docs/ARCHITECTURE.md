# Architecture Overview

## Terminology

| Term | Meaning |
|------|---------|
| **Porting workspace** | This Python repository — an active reimplementation of the Claude Code agent harness |
| **Archived / archive** | The original TypeScript Claude Code source, which may or may not be present locally at `archive/claude_code_ts_snapshot/src/` |
| **Mirrored** | A command, tool, or module that has a stub entry in the Python registry pointing at its original TypeScript `source_hint`. The Python shim records the name and origin but executes a placeholder rather than reimplementing the logic. |
| **Subsystem** | One of the 30 top-level packages in `src/` that correspond to directories in the original TypeScript codebase |
| **Reference data** | The JSON files in `src/reference_data/` that describe the archived surface — used by the parity audit and loaded as the command/tool inventories |

---

Claw Code is a clean-room Python rewrite of the Claude Code agent harness. It mirrors the architectural structure of the original TypeScript system — its subsystem organisation, command and tool inventories, session lifecycle, and runtime bootstrap sequence — without reproducing proprietary source code.

---

## High-Level Structure

```
┌────────────────────────────────────────────────────────┐
│                        CLI (main.py)                   │
│                     argparse dispatcher                │
└────────────────────┬───────────────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │     PortRuntime     │  runtime.py
          │  route_prompt()     │
          │  bootstrap_session()│
          │  run_turn_loop()    │
          └──────────┬──────────┘
                     │
     ┌───────────────▼───────────────┐
     │        QueryEnginePort        │  query_engine.py
     │  submit_message()             │
     │  stream_submit_message()      │
     │  persist_session()            │
     └──────┬──────────────┬─────────┘
            │              │
    ┌───────▼──────┐  ┌────▼──────────┐
    │  Commands    │  │    Tools      │
    │  commands.py │  │  tools.py     │
    │  207 entries │  │  184 entries  │
    └──────────────┘  └───────────────┘
            │
    ┌───────▼──────────────────────┐
    │  reference_data/ (JSON)      │
    │  commands_snapshot.json      │
    │  tools_snapshot.json         │
    │  subsystems/*.json (30)      │
    └──────────────────────────────┘
```

---

## Bootstrap Lifecycle

When `PortRuntime.bootstrap_session()` is called, the runtime executes the following seven stages (defined in `bootstrap_graph.py`):

| Stage | Description |
|-------|-------------|
| 1 | Top-level prefetch side effects (MDM read, keychain prefetch, project scan) |
| 2 | Warning handler and environment guards |
| 3 | CLI parser and pre-action trust gate |
| 4 | `setup()` + commands/agents parallel load |
| 5 | Deferred init after trust |
| 6 | Mode routing: local / remote / SSH / teleport / direct-connect / deep-link |
| 7 | Query engine submit loop |

The trust gate at stage 3 controls whether `plugin_init`, `skill_init`, `mcp_prefetch`, and `session_hooks` are enabled (see `deferred_init.py`).

---

## Core Abstractions

### `PortRuntime` (`src/runtime.py`)

The top-level orchestrator. Provides three entry points:

- **`route_prompt(prompt, limit)`** — tokenises the prompt and scores it against all registered commands and tools (207 and 184 respectively at the time of the initial snapshot; the actual count reflects the current snapshot files) using substring matching. Returns a ranked list of `RoutedMatch` objects.
- **`bootstrap_session(prompt, limit)`** — runs the full 7-stage lifecycle and returns a `RuntimeSession`.
- **`run_turn_loop(prompt, ...)`** — drives a multi-turn loop up to `max_turns`, stopping early on non-`completed` stop reasons.

### `QueryEnginePort` (`src/query_engine.py`)

The conversation engine. Manages:

- Turn-bounded message submission with token budget enforcement
- Streaming event emission
- Automatic message compaction after `compact_after_turns` turns
- Session persistence to `.port_sessions/`

### `PortManifest` (`src/port_manifest.py`)

Introspects the live `src/` directory, counting Python files and enumerating top-level modules. Used by `QueryEnginePort.render_summary()`.

### `RuntimeSession` (`src/runtime.py`)

Immutable record of a single bootstrapped session. Contains the context, setup report, system init message, routing matches, execution results, streaming events, turn result, and persisted session path.

---

## Data Flow

```
User prompt
    │
    ▼
PortRuntime.route_prompt()
    │  tokenise → score against PORTED_COMMANDS + PORTED_TOOLS
    ▼
list[RoutedMatch]  (kind, name, source_hint, score)
    │
    ▼
PortRuntime.bootstrap_session()
    │  build context, setup, history
    │  run execution registry shims
    │  infer permission denials (bash-named tools are gated)
    ▼
QueryEnginePort.stream_submit_message()  →  yields stream events
QueryEnginePort.submit_message()         →  returns TurnResult
    │
    ▼
TurnResult (prompt, output, matched_commands, matched_tools,
            permission_denials, usage, stop_reason)
    │
    ▼
save_session()  →  .port_sessions/<uuid>.json
```

---

## Reference Data System

All command and tool inventory data lives in `src/reference_data/`:

| File | Contents |
|------|----------|
| `commands_snapshot.json` | 207 command entries — each with `name`, `source_hint`, `responsibility` |
| `tools_snapshot.json` | 184 tool entries — each with `name`, `source_hint`, `responsibility` |
| `archive_surface_snapshot.json` | Metadata about the archived original surface: `total_ts_like_files`, `command_entry_count`, `tool_entry_count` |
| `subsystems/*.json` | 30 subsystem files — each with `archive_name`, `module_count`, `sample_files`, `porting_note` |

These JSON files are loaded once via `functools.lru_cache` and are the authoritative source for command/tool names, origin file paths, and descriptions. No live TypeScript source is required.

### Root-level mirror files

`parity_audit.py` maintains an explicit mapping of 18 root-level TypeScript files to their Python equivalents. These files exist in `src/` specifically to satisfy the parity audit:

| TypeScript original | Python mirror | Role |
|--------------------|---------------|------|
| `QueryEngine.ts` | `QueryEngine.py` | Subclass of `QueryEnginePort` adding `route()` |
| `Task.ts` | `task.py` | `PortingTask` dataclass |
| `Tool.ts` | `Tool.py` | `ToolDefinition` dataclass and `DEFAULT_TOOLS` |
| `commands.ts` | `commands.py` | Command registry |
| `context.ts` | `context.py` | `PortContext` builder |
| `cost-tracker.ts` | `cost_tracker.py` | `CostTracker` |
| `costHook.ts` | `costHook.py` | `apply_cost_hook()` |
| `dialogLaunchers.tsx` | `dialogLaunchers.py` | `DialogLauncher` dataclass |
| `history.ts` | `history.py` | `HistoryLog` |
| `ink.ts` | `ink.py` | `render_markdown_panel()` |
| `interactiveHelpers.tsx` | `interactiveHelpers.py` | `bulletize()` |
| `main.tsx` | `main.py` | CLI entrypoint |
| `projectOnboardingState.ts` | `projectOnboardingState.py` | `ProjectOnboardingState` |
| `query.ts` | `query.py` | `QueryRequest`, `QueryResponse` |
| `replLauncher.tsx` | `replLauncher.py` | `build_repl_banner()` placeholder |
| `setup.ts` | `setup.py` | `WorkspaceSetup`, `SetupReport` |
| `tasks.ts` | `tasks.py` | `default_tasks()` |
| `tools.ts` | `tools.py` | Tool registry |

---

## Subsystem Packages

The `src/` directory contains 30 placeholder subpackages, each mirroring a subsystem from the original TypeScript architecture:

| Package | Original role |
|---------|---------------|
| `assistant` | Core assistant loop |
| `bootstrap` | Application startup |
| `bridge` | Cross-process communication bridge |
| `buddy` | Inline assistance features |
| `cli` | Command-line interface layer |
| `components` | UI component library |
| `constants` | Shared constants |
| `coordinator` | Task coordination |
| `entrypoints` | Application entry points |
| `hooks` | Lifecycle hook system |
| `keybindings` | Keyboard shortcut handling |
| `memdir` | Memory directory management |
| `migrations` | Data migration tooling |
| `moreright` | Extended right-panel features |
| `native_ts` | Native TypeScript bridges |
| `outputStyles` | Output formatting styles |
| `plugins` | Plugin system |
| `remote` | Remote execution support |
| `schemas` | Data schema definitions |
| `screens` | Screen/view management |
| `server` | Local server layer |
| `services` | Background service management |
| `skills` | Skill system |
| `state` | Application state management |
| `types` | Shared TypeScript/Python types |
| `upstreamproxy` | Upstream proxy integration |
| `utils` | General utilities (100+ modules) |
| `vim` | Vim-mode support |
| `voice` | Voice interface support |

Each package's `__init__.py` exposes: `ARCHIVE_NAME`, `MODULE_COUNT`, `SAMPLE_FILES`, `PORTING_NOTE`.

---

## Permission Model

Tool permissions are controlled by `ToolPermissionContext` (`src/permissions.py`):

- **`deny_names`** — exact tool names to block (case-insensitive `frozenset`)
- **`deny_prefixes`** — name prefixes to block (case-insensitive `tuple`)

Permission denials are represented as `PermissionDenial(tool_name, reason)` and are tracked across the session in `QueryEnginePort.permission_denials`.

Additionally, `PortRuntime._infer_permission_denials()` automatically gates any tool whose name contains `"bash"`, returning a denial with reason `"destructive shell execution remains gated in the Python port"`.

---

## Session Lifecycle

```
QueryEnginePort.from_workspace()   ← new session, fresh UUID
        │
        ▼
submit_message() × N turns
        │  each turn: append to mutable_messages + transcript_store
        │  compact when len(messages) > compact_after_turns
        ▼
persist_session()
        │  flush_transcript() → TranscriptStore.flushed = True
        │  save_session() → .port_sessions/<uuid>.json
        ▼
load_session(session_id)
        │
        ▼
QueryEnginePort.from_saved_session(session_id)  ← resume
```

Session files are JSON documents stored in `.port_sessions/` relative to the working directory. The format is:

```json
{
  "session_id": "<hex uuid>",
  "messages": ["<prompt 1>", "..."],
  "input_tokens": 42,
  "output_tokens": 17
}
```

---

## Streaming Events

`QueryEnginePort.stream_submit_message()` yields these event dictionaries in order:

| Event type | Fields | Condition |
|------------|--------|-----------|
| `message_start` | `session_id`, `prompt` | Always |
| `command_match` | `commands: tuple[str]` | If any commands matched |
| `tool_match` | `tools: tuple[str]` | If any tools matched |
| `permission_denial` | `denials: list[str]` | If any tools were denied |
| `message_delta` | `text` | Always |
| `message_stop` | `usage`, `stop_reason`, `transcript_size` | Always |

---

## No External Dependencies

The entire project uses only the Python standard library:

`dataclasses` · `argparse` · `json` · `pathlib` · `subprocess` · `platform` · `functools` · `uuid` · `textwrap` · `unittest`

No `pip install` step is required.
