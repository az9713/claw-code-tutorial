# Agentic Harness: Complete Implementation Documentation

Last updated: March 31, 2026

## Scope

This document covers every code path that contributes to agent-like behavior in the Python workspace:

- Agent creation primitives
- Prompt routing/orchestration
- Command/tool execution shims
- Turn loop and stop conditions
- Session and transcript lifecycle
- Permission and trust gates
- Remote/direct mode branches
- Parity with archived agent surface (snapshot-backed)

## Executive Summary

The current harness is a **metadata-driven agentic runtime scaffold**:

- It can create runtime sessions, route prompts to mirrored command/tool entries, execute shim handlers, emit stream events, and persist session state.
- It does **not** yet execute real archived agent implementations.
- Agent behavior is currently represented by:
  - runtime orchestration code in `src/runtime.py` and `src/query_engine.py`
  - mirrored inventory metadata in `src/reference_data/*.json`
  - execution wrappers in `src/execution_registry.py`

## Agentic Surface Inventory

### Implemented Python Harness Surfaces

- `src/main.py`
  - CLI orchestration entrypoint (`route`, `bootstrap`, `turn-loop`, mode commands).
- `src/runtime.py`
  - `PortRuntime`: routing, bootstrap session composition, iterative turn loop.
- `src/query_engine.py`
  - `QueryEnginePort`: per-turn processing, usage accounting, transcript/session management.
- `src/execution_registry.py`
  - `ExecutionRegistry`: name-to-shim lookup for mirrored command/tool handlers.
- `src/commands.py` and `src/tools.py`
  - snapshot loading + searchable inventories + shim execution methods.
- `src/setup.py`, `src/prefetch.py`, `src/deferred_init.py`, `src/system_init.py`
  - startup lifecycle, trust-gated init toggles, init message synthesis.
- `src/permissions.py`
  - tool deny-name/deny-prefix filtering.
- `src/session_store.py`, `src/transcript.py`, `src/history.py`
  - state persistence and operational history capture.

### Mirrored Agent Metadata (Snapshot-Based)

From `src/reference_data/tools_snapshot.json`:

- Total mirrored tools: `184`
- Agent-related entries (name/source contains `agent`): `21`
- Includes:
  - `AgentTool`
  - `runAgent`
  - `resumeAgent`
  - `forkSubagent`
  - `spawnMultiAgent`
  - `planAgent`
  - `verificationAgent`
  - `generalPurposeAgent`
  - `exploreAgent`
  - `claudeCodeGuideAgent`
  - and related support entries

From `src/reference_data/commands_snapshot.json`:

- Total mirrored commands: `207`
- Agent-related command entries: `2` (`agents` variants)

Important: these are mirrored metadata entries, not native Python implementations of those tools/commands.

## Harness Architecture

```text
User prompt / CLI command
  -> argparse dispatch (src/main.py)
  -> runtime orchestration (PortRuntime)
  -> inventory matching (PORTED_COMMANDS + PORTED_TOOLS)
  -> execution registry lookup (MirroredCommand/MirroredTool)
  -> query engine turn processing (QueryEnginePort)
  -> stream events + turn result
  -> session persistence (.port_sessions/*.json)
```

### Design Pattern

- **Inventory-first orchestration**: behaviors are selected from mirrored inventory metadata.
- **Shim execution**: command/tool execution currently returns explanatory messages.
- **Stateful turns**: turn history, usage, and stop reasons are tracked per session.
- **Trust/policy hooks**: prefetch/deferred-init and deny filters establish future hardening points.

## Agent Creation and Session Bootstrap

### Creation Path

Primary creation path: `PortRuntime.bootstrap_session(prompt, limit=5)` in `src/runtime.py`.

Sequence:

1. Build context (`build_port_context()`).
2. Run setup in trusted mode (`run_setup(trusted=True)`).
3. Create runtime history (`HistoryLog`).
4. Instantiate engine (`QueryEnginePort.from_workspace()`).
5. Route prompt (`route_prompt`).
6. Build execution registry (`build_execution_registry()`).
7. Execute command/tool shims for routed matches.
8. Infer permission denials (bash-name gating).
9. Stream-submit and submit message.
10. Persist session (`engine.persist_session()`).
11. Return `RuntimeSession` object.

`RuntimeSession` is the complete bootstrapped harness artifact and includes:

- context
- setup report
- system init message
- routed matches
- command/tool execution messages
- stream events
- final turn result
- persisted session path
- history timeline

## Orchestration and Routing

### Routing Strategy (`route_prompt`)

Routing is lexical and score-based:

1. Prompt tokens are normalized (lowercase, split on spaces plus `/` and `-` replacement).
2. `_collect_matches` scores each module when token appears in:
   - `module.name`
   - `module.source_hint`
   - `module.responsibility`
3. Selection policy:
   - pick top command match (if any)
   - pick top tool match (if any)
   - fill remaining slots by global score ordering
4. Truncate to `limit`.

This yields balanced initial command/tool representation rather than only one category.

### Matching Tradeoffs

- Fast and deterministic.
- No semantic embeddings/model ranking.
- Token-substring match can over-select generic names.
- Duplicate command names from snapshot variants are possible by design.

## Execution Model

### Execution Registry

`ExecutionRegistry` maps names to wrappers:

- `MirroredCommand.execute(prompt)`
- `MirroredTool.execute(payload)`

These delegate to:

- `execute_command(...)` in `src/commands.py`
- `execute_tool(...)` in `src/tools.py`

Current behavior:

- Returns declarative message:
  - `"Mirrored command '<name>' from <source_hint> would handle prompt ..."`
  - `"Mirrored tool '<name>' from <source_hint> would handle payload ..."`

No side-effecting tool/command runtime is invoked yet.

## Turn Engine Internals

### Core Processing (`QueryEnginePort.submit_message`)

For each turn:

1. Enforce max turns (`QueryEngineConfig.max_turns`).
2. Build output summary containing prompt, matched commands/tools, denial count.
3. Compute usage delta via word-count approximation (`UsageSummary.add_turn`).
4. Enforce max budget (`max_budget_tokens`) -> `stop_reason='max_budget_reached'`.
5. Append prompt to mutable history and transcript.
6. Persist denial records in engine state.
7. Compact messages/transcript if above `compact_after_turns`.
8. Return `TurnResult`.

### Streaming Path (`stream_submit_message`)

Event sequence:

1. `message_start`
2. optional `command_match`
3. optional `tool_match`
4. optional `permission_denial`
5. `message_delta` (full output payload)
6. `message_stop` (usage, stop reason, transcript size)

### Structured Output Mode

When enabled:

- Output is JSON (summary + session_id).
- Retries up to `structured_retry_limit` if serialization fails.

## Multi-Turn Agent Loop

`PortRuntime.run_turn_loop(prompt, limit=5, max_turns=3, structured_output=False)`:

1. Creates fresh `QueryEnginePort`.
2. Applies config overrides (`max_turns`, structured mode).
3. Routes once and reuses matched command/tool names across loop.
4. Submits turn prompts:
   - turn 1: original prompt
   - turn N: `"<prompt> [turn N]"`
5. Stops early if stop reason is not `completed`.

This is the current core “agentic loop” abstraction in Python.

## Permission and Trust Controls

### Tool-Level Filtering

`ToolPermissionContext` (`src/permissions.py`) supports:

- exact deny list (`deny_names`)
- prefix deny list (`deny_prefixes`)

Consumed by:

- CLI `tools` command (`--deny-tool`, `--deny-prefix`)
- `get_tools(..., permission_context=...)`

### Runtime Denial Inference

`PortRuntime._infer_permission_denials` auto-denies routed tools containing `bash` in name and records reason:

- `destructive shell execution remains gated in the Python port`

### Trusted Deferred Init

`run_deferred_init(trusted)` toggles:

- `plugin_init`
- `skill_init`
- `mcp_prefetch`
- `session_hooks`

Current implementation is simulated but defines intended policy boundary.

## Session, Memory, and Persistence

### In-Memory State

- `mutable_messages`: active conversation window
- `TranscriptStore.entries`: replayable transcript
- `permission_denials`: tracked denials over session life
- `total_usage`: aggregate in/out counters

### Compaction

- `compact_messages_if_needed` trims both mutable messages and transcript to `compact_after_turns`.

### Persistence

`persist_session()` writes `.port_sessions/<session_id>.json` via `save_session` with:

- `session_id`
- `messages`
- `input_tokens`
- `output_tokens`

### Reload

`QueryEnginePort.from_saved_session(session_id)` reconstructs engine with previous messages and usage.

## Startup and Mode Branching

### Setup + Prefetch

`run_setup()` composes:

- `start_mdm_raw_read()`
- `start_keychain_prefetch()`
- `start_project_scan(root)`
- deferred init result

`build_system_init_message()` reports startup summary and loaded inventory counts.

### Mode Branches

CLI-exposed mode handlers:

- `remote-mode`
- `ssh-mode`
- `teleport-mode`
- `direct-connect-mode`
- `deep-link-mode`

All currently return structured placeholder reports and are safe simulation stubs.

## Test Coverage for Harness Behavior

`tests/test_porting_workspace.py` validates:

- bootstrap and turn-loop execution
- execution registry behavior
- setup/deferred-init reporting
- permission filtering
- remote/direct mode command behavior
- session persistence and load
- command/tool routing and lookup

## Current Gaps vs Full Agent Runtime

1. No native implementation for mirrored agent tools (`runAgent`, `forkSubagent`, etc.).
2. No real subprocess/network transport in mode branches.
3. No semantic planner/executor split; orchestration is lexical-routing plus shim reporting.
4. No persistent long-term memory beyond session JSON.
5. No advanced policy engine (RBAC, capabilities, signed tool manifests).

## Recommended Evolution Plan

1. Introduce execution capability flags per mirrored entry.
2. Implement real tool adapters for a small allowlisted subset.
3. Split orchestration into explicit planner/executor/verifier interfaces.
4. Add durable typed memory store with schema versioning.
5. Replace substring routing with weighted + semantic ranking.
6. Add structured audit logs for tool calls, denials, and state transitions.

## Practical Guidance for Contributors

- When adding agentic features, maintain these invariants:
  - CLI contract stability
  - deterministic stop reasons
  - explicit permission decisions
  - test coverage for new runtime branch
  - synchronized docs updates in `docs_by_codex/`
- Treat snapshot metadata as inventory hints, not executable guarantees.
