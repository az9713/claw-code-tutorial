# System Overview

## Purpose

`claw-code` is a Python porting workspace that mirrors and interrogates an archived TypeScript harness surface. It is not a full runtime reimplementation; it is a parity-aware, introspection-capable scaffold with:

- Snapshot-backed command and tool inventories
- CLI workflows for routing, bootstrap simulation, and session persistence
- Parity audit support against a local archive when present

## Current Scope (from code, March 31, 2026)

- Python files in `src/`: 66
- Mirrored command entries: 207 (`src/reference_data/commands_snapshot.json`)
- Mirrored tool entries: 184 (`src/reference_data/tools_snapshot.json`)
- CLI subcommands: 24 (`src/main.py`)
- Tool handlers with real implementations: 33 (`src/tool_implementations/`, `TOOL_DISPATCH`)
- Command handlers with real implementations: 17 (`src/command_implementations/`, `COMMAND_DISPATCH`)

## What It Does Well

- Provides stable metadata surfaces (`PORTED_COMMANDS`, `PORTED_TOOLS`)
- Simulates runtime routing and turn flow (`PortRuntime`, `QueryEnginePort`)
- Persists simple session state in JSON (`.port_sessions/`)
- Gives fast visibility into parity posture (`parity-audit`)
- Executes real file I/O — `FileReadTool`, `FileWriteTool`, `FileEditTool`, `GlobTool`, `GrepTool`, and `BashTool` perform actual filesystem and shell operations
- Manages tasks, teams, agents, todos, crons, and config in an in-memory store (`src/stores.py`)
- Fetches real web content via `WebFetchTool` and `WebSearchTool`
- Routes 17 session and admin commands (`help`, `version`, `status`, `model`, `session`, `config`, and more) to real handlers

## What It Does Not Yet Do

**This is a partial port — routing, sessions, and 33 tool / 17 command handlers are real; 151 tools and 190 commands remain as stubs.**

- **Execute logic for 151 remaining tools and 190 remaining commands** — anything not listed in `TOOL_DISPATCH` or `COMMAND_DISPATCH` still returns a placeholder string when called.
- **Run real agents** — the agent tool handlers (`runAgent`, `forkSubagent`, `spawnMultiAgent`) record entries in the in-memory store but do not spawn real subprocesses or LLM calls. `resumeAgent` and `loadAgentsDir` remain inventory entries only.
- **Implement subsystem logic** — all 30 packages (`utils`, `components`, `services`, `hooks`, etc.) load only JSON metadata; none contain ported code.
- **Include the TypeScript archive** — the original source is expected at `archive/claude_code_ts_snapshot/src/` but is not present. `PortContext.archive_available` will be `False` on a fresh clone.
- **Provide real remote/SSH/teleport connectivity** — mode simulators return placeholder reports only.
- **Enforce advanced authn/authz, tenancy, or encrypted persistence.**

The parity ratio (`python3 -m src.main parity-audit`) quantifies coverage: the Python port covers scaffolding and routing only against the 1,902-file TypeScript surface.

## Repository Structure

```text
src/
  main.py                  CLI command router
  runtime.py               Runtime composition and bootstrap session
  query_engine.py          Turn engine, usage tracking, transcript/session
  commands.py              Mirrored command snapshot loader + shims
  tools.py                 Mirrored tool snapshot loader + shims
  parity_audit.py          Coverage and parity calculations
  setup.py                 Setup report + prefetch/deferred-init composition
  reference_data/          Snapshot JSON artifacts
  <subsystem>/__init__.py  Placeholder package metadata mirrors
tests/
  test_porting_workspace.py
```

## Audience-Specific Paths

- Users: [Quickstart](./QUICKSTART.md), [CLI Reference](./CLI_REFERENCE.md), [Operations Runbook](./OPERATIONS_RUNBOOK.md)
- Developers: [Python API Reference](./PYTHON_API_REFERENCE.md), [Testing and Quality](./TESTING_AND_QUALITY.md), [Extension Guide](./EXTENSION_AND_PORTING_GUIDE.md)
- Architects: [Architecture](./ARCHITECTURE.md), [Runtime Lifecycle](./RUNTIME_LIFECYCLE.md), [Roadmap and ADR Backlog](./ROADMAP_AND_ADR_BACKLOG.md)
