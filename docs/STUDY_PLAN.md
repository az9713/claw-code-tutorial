# Study Plan: Understanding Claw Code Inside Out

A structured, phase-by-phase reading plan for deeply understanding the `claw-code` Python workspace. Designed to build an accurate mental model before touching the code yourself.

---

## Repository at a Glance

| Metric | Value |
|--------|-------|
| Python files | 66 |
| Approximate total lines | ~1,673 |
| Subsystem packages | 30 |
| Mirrored commands | 207 (from JSON snapshot) |
| Mirrored tools | 184 (from JSON snapshot) |
| Test methods | 20+ |
| External dependencies | None (pure stdlib) |

**Largest files by line count:**

| File | Lines | Complexity |
|------|-------|-----------|
| `src/main.py` | 213 | ⭐⭐⭐⭐ |
| `src/query_engine.py` | 193 | ⭐⭐⭐⭐ |
| `src/runtime.py` | 192 | ⭐⭐⭐⭐⭐ |
| `src/parity_audit.py` | 138 | ⭐⭐⭐ |
| `tests/test_porting_workspace.py` | 248 | ⭐⭐⭐ |

---

## Dependency Graph (no circular imports)

```
main.py
├── bootstrap_graph.py
├── command_graph.py
├── commands.py
│   └── models.py
├── context.py
├── direct_modes.py
├── parity_audit.py
├── permissions.py
├── port_manifest.py
├── query_engine.py
│   ├── commands.py
│   ├── models.py
│   ├── permissions.py
│   ├── tools.py
│   └── transcript.py
├── remote_runtime.py
├── runtime.py
│   ├── commands.py
│   ├── cost_tracker.py
│   ├── history.py
│   ├── models.py
│   ├── permissions.py
│   ├── query_engine.py
│   ├── setup.py
│   └── tools.py
├── session_store.py
├── setup.py
│   ├── deferred_init.py
│   └── prefetch.py
├── tool_pool.py
└── tools.py
    ├── models.py
    └── permissions.py
```

---

## Phase 1 — Architecture Foundations (Day 1)

**Goal:** Understand the shape of the system before reading any logic.

### Step 1: Read the docs first

Start with the documentation suite to build a mental frame:

1. [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — System overview, terminology, 7-stage bootstrap, module map
2. [`docs/INDEX.md`](INDEX.md) — Navigation hub; understand what each doc covers
3. [`docs/GLOSSARY.md` (in `docs_by_codex/`)](../docs_by_codex/GLOSSARY.md) — Key terms: mirrored, archived, porting workspace, subsystem, reference data

### Step 2: Data models

Read `src/models.py` first — every other file uses these types:

- `Subsystem` — top-level module metadata
- `PortingModule` — mirrored command/tool entry (name, source_hint, responsibility)
- `PermissionDenial` — denial reason record
- `UsageSummary` — token accounting (word-count approximation)
- `PortingBacklog` — list wrapper with markdown helpers

### Step 3: Port manifest and context

- `src/port_manifest.py` — `build_port_manifest()`: live filesystem introspection; `PortManifest(src_root, total_python_files, top_level_modules)`
- `src/context.py` — `PortContext`: workspace state including `archive_available` flag; `archive_root` hardcoded to `archive/claude_code_ts_snapshot/src`

### Step 4: Skim `src/main.py` for the command surface

Don't read for depth — just skim to see the 22 subcommands and what each dispatches to. This gives you the "map" of the whole CLI.

**Questions to answer after Phase 1:**
- What is a "mirrored" command or tool?
- What is the difference between `docs/` and `docs_by_codex/`?
- What does `PortContext.archive_available` mean?

---

## Phase 2 — Execution Core (Day 2)

**Goal:** Understand how prompts flow through the system.

### Step 5: `src/runtime.py` — the stateless orchestrator

The most important file. Read it top to bottom:

1. `route_prompt(prompt, limit=5)` — token scoring algorithm:
   - Tokenizes both prompt and `module.responsibility`
   - Scores by shared-token count; ties broken by name match
   - Returns `RoutedMatch(kind, name, score, source_hint)` tuples
2. `bootstrap_session(prompt, limit=5)` — runs the full 7-stage lifecycle
3. `run_turn_loop(prompt, max_turns=3)` — stateful multi-turn loop
4. `_infer_permission_denials(matches)` — automatic bash gating (denies `bash` unless a BashTool match is in the top results)

### Step 6: `src/query_engine.py` — the stateful engine

1. `QueryEngineConfig` — `max_turns=8`, `max_budget_tokens=2000`, `compact_after_turns=12`
2. `submit_message(prompt)` — budget enforcement, command/tool matching, permission checks, `TurnResult` output
3. `stream_submit_message(prompt)` — generator yielding 6 event types: `message_start`, `command_match`, `tool_match`, `permission_denial`, `message_delta`, `message_stop`
4. `compact_messages_if_needed()` — triggers `TranscriptStore.compact(keep_last=10)` when turn count ≥ `compact_after_turns`

### Step 7: `src/execution_registry.py`

- `MirroredCommand`, `MirroredTool` — execution wrappers
- `build_execution_registry()` — assembles from both snapshots

**Questions to answer after Phase 2:**
- How does `route_prompt` score a match? What wins ties?
- What causes `stop_reason="max_budget_reached"` vs `"max_turns_reached"`?
- At what point does a streaming `permission_denial` event fire?

---

## Phase 3 — Command and Tool Surface (Day 3)

**Goal:** Understand the inventory system — where 207 commands and 184 tools come from.

### Step 8: Reference data

Browse `src/reference_data/`:

- `commands_snapshot.json` — 207 entries: `name`, `source_hint`, `responsibility`
- `tools_snapshot.json` — 184 entries; note the agent tools (18 AgentTool modules), task tools (18), team tools (12), `spawnMultiAgent`
- `archive_surface_snapshot.json` — `total_ts_like_files: 1902`, entry counts
- `subsystems/` — 30 JSON files describing each package (`archive_name`, `module_count`, `sample_files`, `porting_note`)

### Step 9: `src/commands.py` and `src/tools.py`

- `PORTED_COMMANDS` / `PORTED_TOOLS` — Python-native ported entries (small, current set)
- `load_command_snapshot()` / `load_tool_snapshot()` — `@lru_cache` JSON loading
- `execute_command()` / `execute_tool()` — return placeholder message; no real logic
- `filter_tools_by_permission_context()` — `ToolPermissionContext` filtering

### Step 10: `src/permissions.py`

- `ToolPermissionContext(deny_names: frozenset, deny_prefixes: tuple)` — frozen dataclass
- `from_iterables(deny_names, deny_prefixes)` — constructor
- `blocks(tool_name: str) → bool` — deny-list check

### Step 11: `src/command_graph.py` and `src/tool_pool.py`

- `CommandGraph` — segments by `source_hint` substring into `builtins`, `plugin_like`, `skill_like`
- `ToolPool` — filtered tool set; `assemble_tool_pool(simple_mode, include_mcp, permission_context)`
- **Simple mode**: restricts to `BashTool`, `FileReadTool`, `FileEditTool` only

**Questions to answer after Phase 3:**
- What determines whether a command is "plugin-like" vs "builtin"?
- Why does `execute_command()` return a placeholder?
- What is the difference between `PORTED_TOOLS` and `load_tool_snapshot()`?

---

## Phase 4 — Initialization and Setup (Day 4)

**Goal:** Understand the 7-stage bootstrap lifecycle.

### Step 12: Bootstrap lifecycle

- `src/bootstrap_graph.py` — `BootstrapGraph` with 7 hardcoded stage strings; `build_bootstrap_graph()`
  - Stage 1: prefetch (MDM raw read, keychain, project scan)
  - Stage 2: warning handler registration
  - Stage 3: trust gate (trusted/untrusted path split)
  - Stage 4: setup + parallel snapshot load
  - Stage 5: deferred init (plugin, skill, MCP, hooks)
  - Stage 6: mode routing (SSH, remote, direct connect, deep link)
  - Stage 7: query engine submit loop

### Step 13: `src/setup.py`

- `WorkspaceSetup` — python_version, implementation, platform_name, test_command
- `run_setup(cwd=None, trusted=True) → SetupReport`
- `SetupReport` — aggregates setup + prefetches + deferred_init + trusted flag

### Step 14: `src/prefetch.py`

- `start_mdm_raw_read()` — macOS MDM simulation
- `start_keychain_prefetch()` — credential store simulation
- `start_project_scan(root)` — counts Python files at root

### Step 15: `src/deferred_init.py`

- `DeferredInitResult(trusted, plugin_init, skill_init, mcp_prefetch, session_hooks)` — 5 bool flags
- `run_deferred_init(trusted=True)` — all four subsystems enabled when trusted
- **Note:** `PortRuntime` always calls `run_setup(trusted=True)`, so all flags are always `True` via standard path

**Questions to answer after Phase 4:**
- Which stage gating means untrusted mode skips MCP?
- When would `archive_available` be `True`?
- What is the purpose of `start_mdm_raw_read()`?

---

## Phase 5 — Advanced Features (Day 5)

**Goal:** Understand sessions, transcripts, agents, and parity.

### Step 16: Session persistence

- `src/session_store.py` — `StoredSession(session_id, prompt, timestamp, summary, session_dir)` frozen dataclass
- `save_session(session, directory=None) → Path` — writes to `.port_sessions/<uuid>.json`
- `load_session(session_id, directory=None) → StoredSession` — raises `FileNotFoundError` on miss

### Step 17: `src/transcript.py`

- `TranscriptStore(entries: list, flushed: bool)` — mutable
- `compact(keep_last=10)` — sliding window; discards older entries
- `flush()` — marks flushed=True (persist marker, does not write to disk itself)
- `replay()` — returns copy of entries list

### Step 18: Parity audit

- `src/parity_audit.py` — `ARCHIVE_ROOT_FILES` (18 root mappings) + `ARCHIVE_DIR_MAPPINGS` (33 directory mappings)
- `run_parity_audit() → ParityAuditResult` — checks `src/` top-level only; uses `os.path.exists`
- `ParityAuditResult` — 8 fields: `archive_available`, `total_python_files`, `total_archive_dirs`, `matched_root_files`, `matched_directories`, `total_file_ratio`, `missing_root_targets`, `missing_directory_targets`

### Step 19: Agent architecture

Read [`docs/AGENTS.md`](AGENTS.md) — this is a deep-dive reference. Key concepts:

- **AgentTool subsystem**: 18 TypeScript modules in `src/reference_data/tools_snapshot.json` (entries prefixed `agent_tool/`)
- **5 built-in agent types**: `exploreAgent`, `planAgent`, `generalPurposeAgent`, `claudeCodeGuideAgent`, `verificationAgent`
- **Task management tools**: `TaskCreateTool`, `TaskGetTool`, `TaskListTool`, `TaskUpdateTool`, `TaskOutputTool`, `TaskStopTool`
- **Team tools**: `TeamCreateTool`, `TeamDeleteTool`, `SendMessageTool`
- **`spawnMultiAgent`**: Shared utility for parallel multi-agent execution
- **Coordinator/swarm worker model**: Two-role permission architecture (coordinator has full tool access; workers have constrained access)

**Questions to answer after Phase 5:**
- What happens when `load_session()` is called with an ID that doesn't exist?
- How does compaction protect against infinite transcript growth?
- What is `spawnMultiAgent` used for?

---

## Phase 6 — CLI Deep Dive (Day 6)

**Goal:** Connect every CLI subcommand to its implementation.

### Step 20: Full read of `src/main.py`

Now read it for depth — map each subcommand to:
1. Which `src/*.py` module it calls
2. What it prints
3. What flags it accepts

Use [`docs/CLI_REFERENCE.md`](CLI_REFERENCE.md) alongside the source.

**22 subcommands by category:**

| Category | Commands |
|----------|----------|
| Workspace inspection | `summary`, `manifest`, `subsystems`, `parity-audit`, `setup-report` |
| Structural views | `command-graph`, `tool-pool`, `bootstrap-graph` |
| Inventory browsing | `commands`, `tools`, `show-command`, `show-tool` |
| Prompt routing | `route`, `bootstrap`, `turn-loop` |
| Execution | `exec-command`, `exec-tool` |
| Session management | `flush-transcript`, `load-session` |
| Runtime modes | `remote-mode`, `ssh-mode`, `teleport-mode`, `direct-connect-mode`, `deep-link-mode` |

### Step 21: Mode simulators

- `src/remote_runtime.py` — `RuntimeModeReport(mode, connected, detail)`: `as_text()` → `mode=\nconnected=\ndetail=`
- `src/direct_modes.py` — `DirectModeReport(mode, target, active)`: `as_text()` → `mode=\ntarget=\nactive=`
- **Note:** These are placeholders; no real network connections are made.

**Questions to answer after Phase 6:**
- Which flag limits both commands and tools by keyword?
- Why do `remote-mode` and `direct-connect-mode` output different fields?
- What does `--structured-output` change about `turn-loop` output?

---

## Phase 7 — Reference Data and Subsystems (Day 7)

**Goal:** Understand the full archived surface and placeholder subsystem packages.

### Step 22: Root-level mirror files

These Python files exist specifically to satisfy `ARCHIVE_ROOT_FILES` in `parity_audit.py`:

| Python file | TypeScript original | Key export |
|------------|---------------------|-----------|
| `src/QueryEngine.py` | `QueryEngine.ts` | `QueryEngineRuntime(QueryEnginePort)` |
| `src/Tool.py` | `Tool.ts` | `ToolDefinition`, `DEFAULT_TOOLS` |
| `src/query.py` | `query.ts` | `QueryRequest`, `QueryResponse` |
| `src/task.py` | `task.ts` | `PortingTask` |
| `src/tasks.py` | `tasks.ts` | `default_tasks()` |
| `src/ink.py` | `ink.ts` | `render_markdown_panel()` |
| `src/interactiveHelpers.py` | `interactiveHelpers.ts` | `bulletize()` |
| `src/replLauncher.py` | `replLauncher.ts` | `build_repl_banner()` |
| `src/dialogLaunchers.py` | `dialogLaunchers.ts` | `DialogLauncher`, `DEFAULT_DIALOGS` |
| `src/costHook.py` | `costHook.ts` | `apply_cost_hook()` |
| `src/projectOnboardingState.py` | `projectOnboardingState.ts` | `ProjectOnboardingState` |

### Step 23: 30 subsystem packages (largest first)

Each package has only an `__init__.py` that loads metadata from `src/reference_data/subsystems/<name>.json`:

| Package | TS modules | Role |
|---------|-----------|------|
| `src.utils` | 564 | Utility functions |
| `src.components` | 389 | UI/display components |
| `src.services` | 130 | External service integrations |
| `src.hooks` | 104 | Lifecycle hook implementations |
| `src.bridge` | 31 | TypeScript/Python bridging |
| `src.agent_tool` | 18 | Multi-agent orchestration |
| (24 more…) | varies | Various subsystems |

### Step 24: Run the test suite

```bash
python3 -m unittest discover -s tests -v
```

Read `tests/test_porting_workspace.py` alongside the output. This file covers:
- CLI subcommand integration tests via `subprocess.run`
- API-level unit tests (PortRuntime, QueryEnginePort, session store, transcript, parity audit)
- Permission filtering tests

---

## Verification Checklist

After completing all 7 phases, you should be able to answer:

**Architecture:**
- [ ] Describe the 7 bootstrap stages from memory
- [ ] Explain the difference between `PortRuntime` and `QueryEnginePort`
- [ ] Explain why 207 commands exist but most are stubs

**Data flow:**
- [ ] Trace a prompt from `python3 -m src.main bootstrap "my prompt"` to printed output
- [ ] Explain when `compact_messages_if_needed()` fires and what it does
- [ ] List all 6 streaming event types in order

**Permission model:**
- [ ] Explain how `ToolPermissionContext` blocks a tool
- [ ] Explain when bash is automatically denied
- [ ] Describe what `simple_mode=True` restricts

**Parity audit:**
- [ ] Explain what `ARCHIVE_ROOT_FILES` checks for
- [ ] Explain why `archive_available=False` by default
- [ ] Describe how `total_file_ratio` is computed

**Agents:**
- [ ] Name the 5 built-in agent types
- [ ] Explain the coordinator vs swarm-worker permission difference
- [ ] Describe what `spawnMultiAgent` is for

---

## Recommended Reading Order Summary

```
Day 1: docs/ARCHITECTURE.md → models.py → port_manifest.py → context.py → skim main.py
Day 2: runtime.py → query_engine.py → execution_registry.py
Day 3: reference_data/ (JSON) → commands.py → tools.py → permissions.py → command_graph.py → tool_pool.py
Day 4: bootstrap_graph.py → setup.py → prefetch.py → deferred_init.py
Day 5: session_store.py → transcript.py → parity_audit.py → docs/AGENTS.md
Day 6: main.py (full depth) → remote_runtime.py → direct_modes.py → docs/CLI_REFERENCE.md
Day 7: root-level mirror files → subsystem packages → tests/test_porting_workspace.py
```

---

## Related Documentation

- [Architecture](ARCHITECTURE.md) — System design and module map
- [API Reference](API_REFERENCE.md) — Every public class and method
- [CLI Reference](CLI_REFERENCE.md) — All 22 subcommands
- [Agents](AGENTS.md) — Agent harness deep dive
- [Developer Guide](DEVELOPER_GUIDE.md) — Code conventions and contribution patterns
- [Configuration](CONFIGURATION.md) — All config fields and permission flags
