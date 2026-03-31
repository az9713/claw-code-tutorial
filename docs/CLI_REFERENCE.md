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

Executes a command handler by exact name against a prompt.

```bash
python3 -m src.main exec-command <name> <prompt>
```

Exit code `0` if `handled=True`, `1` if not.

**17 commands now execute real logic** via `COMMAND_DISPATCH` in `src/command_implementations/`:

| Command | Status | Notes |
|---------|--------|-------|
| `help` | Implemented | Prints available commands |
| `version` | Implemented | Prints version string |
| `clear` | Implemented | Clears session state |
| `compact` | Implemented | Compacts transcript |
| `status` | Implemented | Shows mode flags and store counts |
| `cost` | Implemented | Reports token usage |
| `model` | Implemented | Gets/sets model from config store |
| `memory` | Implemented | Reports memory state |
| `session` | Implemented | Shows current session info |
| `summary` | Implemented | Summarises session |
| `doctor` | Implemented | Runs environment diagnostics |
| `config` | Implemented | Gets/sets in-memory config keys |
| `permissions` | Implemented | Reports permission context |
| `hooks` | Implemented | Lists registered hooks |
| `skills` | Implemented | Lists loaded skills |
| `mcp` | Implemented | Reports MCP server status |
| `tasks` | Implemented | Lists porting tasks |
| *(all others)* | Stub | Returns a fallthrough placeholder message |

Commands with no registered handler return a stub message and exit with code `1`.

**Examples**

```bash
# Implemented command — real output
python3 -m src.main exec-command help ""
# Output: lists all registered commands

python3 -m src.main exec-command version ""
# Output: claw-code 0.1.0 (Python port)

python3 -m src.main exec-command doctor ""
# Output: Python version, platform, and environment checks

# Unimplemented command — stub fallthrough
python3 -m src.main exec-command review "inspect security review"
# Output: [stub] Command 'review' received prompt: inspect security review
# Exit code: 1
```

---

### `exec-tool`

Executes a tool handler by exact name against a payload string.

```bash
python3 -m src.main exec-tool <name> <payload>
```

**33 tools now execute real logic** via `TOOL_DISPATCH` in `src/tool_implementations/`. All others return a stub message.

#### Implemented tools

| Tool | Category | Notes |
|------|----------|-------|
| `BashTool` | Shell | Runs command via subprocess; security blocklist applied |
| `FileReadTool` | File I/O | Returns file content with line numbers |
| `FileWriteTool` | File I/O | Writes content to file |
| `FileEditTool` | File I/O | Exact-match string replacement; uniqueness enforced |
| `GlobTool` | File I/O | Pattern-based file search |
| `GrepTool` | File I/O | Regex content search |
| `TaskCreateTool` | Tasks | Creates TaskRecord in in-memory store |
| `TaskGetTool` | Tasks | Retrieves task by ID |
| `TaskListTool` | Tasks | Lists all tasks in store |
| `TaskUpdateTool` | Tasks | Updates task fields |
| `TaskOutputTool` | Tasks | Returns task output |
| `TaskStopTool` | Tasks | Marks task stopped |
| `TeamCreateTool` | Teams | Creates TeamRecord in store |
| `TeamDeleteTool` | Teams | Removes TeamRecord from store |
| `SendMessageTool` | Teams | Logs message against a team |
| `AgentTool` | Agents | Creates AgentRecord; returns agent_id |
| `runAgent` | Agents | Creates AgentRecord and marks completed |
| `forkSubagent` | Agents | Creates child AgentRecord with parent_id |
| `spawnMultiAgent` | Agents | Creates multiple AgentRecords in parallel |
| `WebFetchTool` | Web | Fetches URL content; 30s timeout |
| `WebSearchTool` | Web | Performs web search |
| `AskUserQuestionTool` | User | Prompts for user input |
| `TodoWriteTool` | Todos | Writes todo list to store |
| `ConfigTool` | Config | Gets/sets in-memory config keys |
| `ToolSearchTool` | Registry | Searches tool inventory |
| `EnterPlanModeTool` | Modes | Sets plan_mode=True in store |
| `ExitPlanModeV2Tool` | Modes | Sets plan_mode=False in store |
| `EnterWorktreeTool` | Modes | Sets worktree_mode=True in store |
| `ExitWorktreeTool` | Modes | Sets worktree_mode=False in store |
| `NotebookEditTool` | Notebooks | Edits Jupyter notebook cells |
| `CronCreateTool` | Cron | Creates CronRecord in store |
| `CronDeleteTool` | Cron | Removes CronRecord from store |
| `CronListTool` | Cron | Lists all cron records |

#### Payload format

The payload argument is parsed as follows:
1. **JSON string** — if the payload parses as a JSON object, keys are extracted as named parameters.
2. **Empty string** — treated as an empty params dict `{}`.
3. **Non-JSON fallback** — the raw string is passed as `{"input": payload}`.

#### Examples

```bash
# BashTool — returns actual command output
python3 -m src.main exec-tool BashTool '{"command": "echo hello"}'
# Output: hello

# FileReadTool — returns file content with line numbers
python3 -m src.main exec-tool FileReadTool '{"file_path": "src/main.py"}'
# Output:     1  import argparse
#             2  import sys
#             ...

# TaskCreateTool — returns JSON task record
python3 -m src.main exec-tool TaskCreateTool '{"title": "Fix bug", "description": "Investigate crash"}'
# Output: {"task_id": "t-a1b2c3", "title": "Fix bug", "status": "pending", ...}

# Unregistered tool — stub fallthrough
python3 -m src.main exec-tool MCPTool "fetch resource list"
# Output: [stub] Tool 'MCPTool' received payload: fetch resource list
# Exit code: 1
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
