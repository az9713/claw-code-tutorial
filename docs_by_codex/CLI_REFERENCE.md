# CLI Reference

Entry point:

```bash
python -m src.main <command> [options]
```

## Inventory and Reporting

### `summary`

- Description: Render markdown summary of workspace, command/tool counts, and session defaults.
- Args: none

### `manifest`

- Description: Print current Python workspace manifest.
- Args: none

### `parity-audit`

- Description: Compare current workspace against local archive (if present).
- Args: none

### `setup-report`

- Description: Print startup setup, prefetch, and deferred-init report.
- Args: none

### `command-graph`

- Description: Segment commands into builtins, plugin-like, skill-like.
- Args: none

### `tool-pool`

- Description: Show assembled tool pool (default settings).
- Args: none

### `bootstrap-graph`

- Description: Print canonical bootstrap stages.
- Args: none

### `subsystems`

- Description: List top-level Python modules from manifest.
- Options:
  - `--limit <int>` (default: `32`)

## Command and Tool Inventory

### `commands`

- Description: List/search mirrored command entries.
- Options:
  - `--limit <int>` (default: `20`)
  - `--query <str>`
  - `--no-plugin-commands`
  - `--no-skill-commands`

### `tools`

- Description: List/search mirrored tool entries.
- Options:
  - `--limit <int>` (default: `20`)
  - `--query <str>`
  - `--simple-mode`
  - `--no-mcp`
  - `--deny-tool <name>` (repeatable)
  - `--deny-prefix <prefix>` (repeatable)

### `show-command <name>`

- Description: Show exact command entry metadata.

### `show-tool <name>`

- Description: Show exact tool entry metadata.

### `exec-command <name> <prompt>`

- Description: Execute mirrored command shim.

### `exec-tool <name> <payload>`

- Description: Execute mirrored tool shim.

## Routing and Runtime

### `route <prompt>`

- Description: Route prompt across mirrored command/tool inventory.
- Options:
  - `--limit <int>` (default: `5`)

### `bootstrap <prompt>`

- Description: Build runtime-style session report from mirrored inventories.
- Options:
  - `--limit <int>` (default: `5`)

### `turn-loop <prompt>`

- Description: Run small stateful turn loop.
- Options:
  - `--limit <int>` (default: `5`)
  - `--max-turns <int>` (default: `3`)
  - `--structured-output`

### `flush-transcript <prompt>`

- Description: Submit one prompt, persist, and flush transcript state.

### `load-session <session_id>`

- Description: Load persisted session metadata.

## Runtime Mode Simulators

- `remote-mode <target>`
- `ssh-mode <target>`
- `teleport-mode <target>`
- `direct-connect-mode <target>`
- `deep-link-mode <target>`

Each currently returns a mode report placeholder and does not open external network connections.

Output format differs by mode type:

**`remote-mode`, `ssh-mode`, `teleport-mode`** → `RuntimeModeReport`:
```
mode=<mode>
connected=True
detail=<description>
```

**`direct-connect-mode`, `deep-link-mode`** → `DirectModeReport`:
```
mode=<mode>
target=<target>
active=True
```
