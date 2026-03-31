# Testing and Quality Gates

## Test Suite

Primary suite: `tests/test_porting_workspace.py`

Coverage themes:

- CLI smoke and behavior checks
- Snapshot count sanity
- Runtime/bootstrap execution flow
- Session persistence/load
- Permission filtering
- Graph/report command outputs

## Run Tests

```bash
python -m unittest discover -s tests -v
```

## Expected Invariants

The suite asserts:

- Manifest and summary generation works.
- Command snapshot count is nontrivial (`>= 150`).
- Tool snapshot count is nontrivial (`>= 100`).
- Core CLI commands return expected marker text.
- Runtime bootstrap and turn-loop execute successfully.

If local archive exists:

- Root file parity coverage must be complete.
- Directory parity coverage must meet threshold.

## Quality Gate Policy for PRs

Minimum gate:

1. `python -m unittest discover -s tests -v` passes.
2. Any new CLI subcommand includes:
   - help text
   - at least one integration test assertion
3. Any change to session format updates:
   - docs in `docs_by_codex/`
   - compatibility test coverage
4. Any change to snapshot schema updates:
   - loader logic
   - tests
   - docs

## Suggested Additional Tests

1. Fuzz tests for `route_prompt` scoring/tokenization.
2. Property tests for transcript compaction boundaries.
3. Snapshot schema validation tests with explicit JSON schema.
4. Backward compatibility tests for old `.port_sessions` payload versions.
