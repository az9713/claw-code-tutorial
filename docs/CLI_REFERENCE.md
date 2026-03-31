# CLI Reference

All commands are invoked as:

```bash
python3 -m src.main <subcommand> [options]
```

---

## Workspace Inspection

### `summary`

Renders the full Python porting workspace summary as Markdown.

```bash
python3 -m src.main summary
```

Output includes: port root, total file count, top-level modules, command/tool surface counts, session stats, and configuration defaults.

---

### `manifest`

Prints the workspace manifest: source root path, total Python file count, and a list of top-level modules with their file counts.

```bash
python3 -m src.main manifest
```

---

### `subsystems`

Lists top-level Python modules from the manifest.

```bash
python3 -m src.main subsystems [--limit N]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--limit N` | `32` | Maximum entries to print |

Output format: `<name>\t<file_count>\t<notes>`

---

### `parity-audit`

Compares the Python workspace coverage against the archived TypeScript surface. Reports root-file coverage, directory coverage, and command/tool entry ratios.

```bash
python3 -m src.main parity-audit
```

If a local TypeScript archive is not present at `archive/`, the command still runs using snapshot-derived metrics.

---

### `setup-report`

Renders the startup and prefetch setup report: Python version, platform, test command, startup steps, and deferred init status.

```bash
python3 -m src.main setup-report
```

---

## Inventory Browsing

### `commands`

Lists mirrored command entries from the archived snapshot.

```bash
python3 -m src.main commands [--limit N] [--query TEXT]
                              [--no-plugin-commands] [--no-skill-commands]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--limit N` | `20` | Maximum entries to print |
| `--query TEXT` | — | Substring filter; uses `render_command_index()` |
| `--no-plugin-commands` | off | Exclude plugin-like commands |
| `--no-skill-commands` | off | Exclude skill-like commands |

**Examples**

```bash
python3 -m src.main commands --limit 10
python3 -m src.main commands --query review
python3 -m src.main commands --no-plugin-commands --no-skill-commands --limit 20
```

---

### `tools`

Lists mirrored tool entries from the archived snapshot.

```bash
python3 -m src.main tools [--limit N] [--query TEXT]
                           [--simple-mode] [--no-mcp]
                           [--deny-tool NAME]... [--deny-prefix PREFIX]...
```

| Flag | Default | Description |
|------|---------|-------------|
| `--limit N` | `20` | Maximum entries to print |
| `--query TEXT` | — | Substring filter |
| `--simple-mode` | off | Restrict to BashTool, FileReadTool, FileEditTool |
| `--no-mcp` | off | Exclude tools whose name or source contains `"mcp"` |
| `--deny-tool NAME` | — | Deny a specific tool by exact name (repeatable) |
| `--deny-prefix PREFIX` | — | Deny tools whose name starts with prefix (repeatable) |

**Examples**

```bash
python3 -m src.main tools --limit 10
python3 -m src.main tools --simple-mode
python3 -m src.main tools --no-mcp
python3 -m src.main tools --deny-prefix mcp --deny-tool BashTool
```

---

### `show-command`

Shows a single command entry by exact name.

```bash
python3 -m src.main show-command <name>
```

Output: `name`, `source_hint`, and `responsibility` on separate lines. Exit code `1` if not found.

```bash
python3 -m src.main show-command review
```

---

### `show-tool`

Shows a single tool entry by exact name.

```bash
python3 -m src.main show-tool <name>
```

Exit code `1` if not found.

```bash
python3 -m src.main show-tool MCPTool
```

---

## Prompt Routing

### `route`

Routes a free-text prompt across the command and tool inventories using token scoring.

```bash
python3 -m src.main route <prompt> [--limit N]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--limit N` | `5` | Maximum matches to return |

Output format: `<kind>\t<name>\t<score>\t<source_hint>`

```bash
python3 -m src.main route "review MCP tool" --limit 5
```

---

### `bootstrap`

Runs the full runtime bootstrap for a prompt and prints the `RuntimeSession` as Markdown.

```bash
python3 -m src.main bootstrap <prompt> [--limit N]
```

Output sections: Runtime Session, Context, Setup, Startup Steps, System Init, Routed Matches, Command Execution, Tool Execution, Stream Events, Turn Result, History Log.

```bash
python3 -m src.main bootstrap "review MCP tool"
```

---

### `turn-loop`

Runs a stateful multi-turn loop for a prompt.

```bash
python3 -m src.main turn-loop <prompt> [--limit N] [--max-turns N] [--structured-output]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--limit N` | `5` | Routing match limit |
| `--max-turns N` | `3` | Maximum turns to run |
| `--structured-output` | off | Emit JSON-formatted output per turn |

Output: one `## Turn N` section per turn, each with the turn output and `stop_reason=`.

```bash
python3 -m src.main turn-loop "review MCP tool" --max-turns 2 --structured-output
```

---

## Execution

### `exec-command`

Executes a command shim by exact name against a prompt.

```bash
python3 -m src.main exec-command <name> <prompt>
```

Exit code `0` if `handled=True`, `1` if not. The shim currently returns a placeholder message.

```bash
python3 -m src.main exec-command review "inspect security review"
```

---

### `exec-tool`

Executes a tool shim by exact name against a payload string.

```bash
python3 -m src.main exec-tool <name> <payload>
```

```bash
python3 -m src.main exec-tool MCPTool "fetch resource list"
```

---

## Session Management

### `flush-transcript`

Submits a prompt through a fresh engine, then persists and flushes the session transcript. Prints the session file path and `flushed=True`.

```bash
python3 -m src.main flush-transcript <prompt>
```

```bash
python3 -m src.main flush-transcript "review MCP tool"
```

---

### `load-session`

Loads a previously persisted session by its UUID (the stem of the `.json` filename in `.port_sessions/`).

```bash
python3 -m src.main load-session <session_id>
```

Output: `<session_id>`, message count, and token totals.

```bash
python3 -m src.main load-session a1b2c3d4e5f6...
```

---

## Structural Views

### `command-graph`

Shows the command graph segmentation: builtins, plugin-like, and skill-like commands with counts.

```bash
python3 -m src.main command-graph
```

---

### `tool-pool`

Shows the assembled tool pool with default settings (all tools, MCP included, no deny-list).

```bash
python3 -m src.main tool-pool
```

---

### `bootstrap-graph`

Prints the 7-stage bootstrap/runtime graph.

```bash
python3 -m src.main bootstrap-graph
```

---

## Runtime Modes

Each mode command simulates a runtime branching path. All accept a `<target>` argument (workspace name or address) and print a mode report.

### `remote-mode`

```bash
python3 -m src.main remote-mode <target>
```

### `ssh-mode`

```bash
python3 -m src.main ssh-mode <target>
```

### `teleport-mode`

```bash
python3 -m src.main teleport-mode <target>
```

### `direct-connect-mode`

```bash
python3 -m src.main direct-connect-mode <target>
```

### `deep-link-mode`

```bash
python3 -m src.main deep-link-mode <target>
```

**Output format — remote, ssh, teleport** (`RuntimeModeReport`):
```
mode=<mode>
connected=True
detail=<description>
```

**Output format — direct-connect, deep-link** (`DirectModeReport`):
```
mode=<mode>
target=<target>
active=True
```

Note: `remote-mode`, `ssh-mode`, and `teleport-mode` use `RuntimeModeReport` (fields: `mode`, `connected`, `detail`). `direct-connect-mode` and `deep-link-mode` use `DirectModeReport` (fields: `mode`, `target`, `active`).

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Entry not found (`show-command`, `show-tool`) or shim not handled (`exec-command`, `exec-tool`) |
| `2` | Unknown command (argparse error) |
