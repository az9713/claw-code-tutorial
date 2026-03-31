# Quickstart

## Prerequisites

- Python 3.10+ (validated on Python 3.13.5)
- Local clone of this repository

## First 5 Minutes

1. Verify environment:

```bash
python -V
```

2. Render workspace summary:

```bash
python -m src.main summary
```

3. Inspect startup setup report:

```bash
python -m src.main setup-report
```

4. Run tests:

```bash
python -m unittest discover -s tests -v
```

## Most Common User Flows

### Discover mirrored inventory

```bash
python -m src.main commands --limit 20
python -m src.main tools --limit 20
```

### Search mirrored inventory

```bash
python -m src.main commands --query review --limit 10
python -m src.main tools --query MCP --limit 10
```

### Prompt routing and runtime simulation

```bash
python -m src.main route "review MCP tool" --limit 5
python -m src.main bootstrap "review MCP tool" --limit 5
python -m src.main turn-loop "review MCP tool" --max-turns 2 --structured-output
```

### Session persistence

```bash
python -m src.main flush-transcript "review MCP tool"
python -m src.main load-session <session_id>
```

## Quick Troubleshooting

- `ModuleNotFoundError: src`
  - Run commands from repository root.
- `load-session` cannot find file
  - Confirm `.port_sessions/<session_id>.json` exists.
- `parity-audit` reports archive unavailable
  - Expected unless `archive/claude_code_ts_snapshot/src` exists locally.
