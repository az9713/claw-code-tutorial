# Architecture

## Architectural Style

The codebase is a metadata-driven simulation architecture:

- Snapshot adapters read frozen command/tool inventories from JSON.
- Runtime orchestration routes prompts against those inventories.
- Session layer tracks usage, transcript compaction, and persistence.
- CLI composes these layers into operator-facing commands.

## Logical Components

1. `Presentation/CLI`
   - `src/main.py`
   - Parses arguments and dispatches subcommands.
2. `Runtime Orchestration`
   - `src/runtime.py`
   - `src/system_init.py`
   - `src/setup.py`
3. `Inventory/Registry`
   - `src/commands.py`
   - `src/tools.py`
   - `src/execution_registry.py`
4. `Session and Conversation`
   - `src/query_engine.py`
   - `src/transcript.py`
   - `src/session_store.py`
5. `Parity and Governance`
   - `src/parity_audit.py`
   - `src/port_manifest.py`
   - `src/context.py`

## High-Level Data Flow

```text
User CLI input
  -> argparse in main.py
  -> runtime/setup/registry/query-engine orchestration
  -> markdown/text output to stdout
  -> optional JSON session write to .port_sessions/
```

## Runtime Boundaries

- Real execution boundary:
  - This project does not execute archived TypeScript logic.
- Persistence boundary:
  - Session JSON only (`session_id`, messages, token counters).
- Security boundary:
  - Tool deny filters exist (`ToolPermissionContext`) but are simple deny-name/prefix checks.

## Subsystem Placeholder Pattern

Multiple packages (`src/assistant`, `src/utils`, etc.) expose archived metadata via `__init__.py` by loading `src/reference_data/subsystems/*.json`.

This gives:

- Stable import paths for parity surface
- Count/sample metadata for introspection
- No runtime behavior parity guarantees

## Evolution Constraints

- New behavior should preserve existing CLI command contracts unless versioned.
- Snapshot schema changes must be backward compatible or accompanied by migration notes.
- Session JSON shape changes must include a compatibility strategy.
