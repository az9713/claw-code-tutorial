# Operations Runbook

## Operational Baseline

Run from repo root.

Health checks:

```bash
python -m src.main summary
python -m src.main setup-report
python -m unittest discover -s tests -v
```

## Common Procedures

### 1) Validate mirrored inventory availability

```bash
python -m src.main commands --limit 5
python -m src.main tools --limit 5
```

### 2) Validate routing behavior for a scenario

```bash
python -m src.main route "review MCP tool" --limit 5
```

### 3) Produce runtime report artifact

```bash
python -m src.main bootstrap "review MCP tool" --limit 5
```

### 4) Persist and reload a session

```bash
python -m src.main flush-transcript "review MCP tool"
python -m src.main load-session <session_id>
```

### 5) Run parity check when archive exists

```bash
python -m src.main parity-audit
```

## Incident Handling

### Symptom: command/tool entries unexpectedly drop

Checklist:

1. Inspect `src/reference_data/commands_snapshot.json` and `tools_snapshot.json`.
2. Confirm JSON validity.
3. Run `summary` and compare counts against expected baseline (207/184 as of 2026-03-31).
4. Run tests.

### Symptom: session files fail to load

Checklist:

1. Confirm file exists in `.port_sessions/`.
2. Validate JSON shape:
   - `session_id` string
   - `messages` array
   - `input_tokens` int
   - `output_tokens` int
3. Check for breaking code changes in `StoredSession` or loader.

### Symptom: parity audit always says archive unavailable

Checklist:

1. Ensure local path exists: `archive/claude_code_ts_snapshot/src`.
2. Confirm process CWD is repo root.
3. Re-run `python -m src.main parity-audit`.

## Operational SLO Suggestions

Recommended internal SLOs:

- CLI smoke command success rate: `>= 99.9%`
- Test suite pass rate on main branch: `100%`
- Documentation lag for behavior-changing PRs: `0 days` (same PR)
