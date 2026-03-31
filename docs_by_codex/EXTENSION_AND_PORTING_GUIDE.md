# Extension and Porting Guide

## Development Principles

1. Preserve external CLI contracts unless intentionally versioning.
2. Keep parity metadata accurate even when runtime behavior is still a shim.
3. Prefer additive, test-backed changes.
4. Update docs and tests in same PR as behavior changes.

## Adding a New CLI Command

1. Add parser entry in `src/main.py`.
2. Implement behavior in a focused module (avoid bloating `main.py`).
3. Add tests in `tests/test_porting_workspace.py`.
4. Document command in [CLI Reference](./CLI_REFERENCE.md).

## Extending Command/Tool Inventory Logic

If snapshot schema remains unchanged:

- Update `commands.py`/`tools.py` filter and selection logic as needed.

If snapshot schema changes:

1. Update loader fields in `load_command_snapshot()` / `load_tool_snapshot()`.
2. Add compatibility handling for older schema if needed.
3. Update tests and docs.

## Replacing Placeholder Runtime Modes

Current mode functions are stubs:

- `run_remote_mode`
- `run_ssh_mode`
- `run_teleport_mode`
- `run_direct_connect`
- `run_deep_link`

Replacement strategy:

1. Preserve return shape first (`as_text()` contract).
2. Add transport adapters behind explicit interfaces.
3. Add failure modes and error contracts.
4. Add integration tests for each mode.

## Porting Toward Real Execution

Current `execute_command` / `execute_tool` emit mirror messages only.

Incremental path:

1. Introduce capability registry with explicit `supports_execute` flag.
2. Keep mirror mode as fallback for entries without implementation.
3. Add deterministic adapter tests per implemented command/tool.
4. Gate destructive actions with explicit permission policy.

## Documentation Debt Prevention Rules

- Every new top-level module must have one paragraph in docs.
- Every new persisted field must be documented before merge.
- Every removed CLI option must include migration note.
- Every architecture-relevant decision should create/update an ADR in [Roadmap and ADR Backlog](./ROADMAP_AND_ADR_BACKLOG.md).
