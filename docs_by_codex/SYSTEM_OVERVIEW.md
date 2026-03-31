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

## What It Does Well

- Provides stable metadata surfaces (`PORTED_COMMANDS`, `PORTED_TOOLS`)
- Simulates runtime routing and turn flow (`PortRuntime`, `QueryEnginePort`)
- Persists simple session state in JSON (`.port_sessions/`)
- Gives fast visibility into parity posture (`parity-audit`)

## What It Does Not Yet Do

- Execute real command/tool implementations from archived source
- Provide real remote/SSH/teleport connectivity (currently placeholders)
- Enforce advanced authn/authz, tenancy, or encrypted persistence

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
