# Command Implementations Reference

This document covers every command handler that executes real logic in the claw-code Python port.
Commands registered in `COMMAND_DISPATCH` run actual code; all other commands from the snapshot
inventory fall through to a mirrored-command stub message.

---

## How Commands Are Invoked

### Dispatcher Chain

```
execute_command(name, prompt)          # src/commands.py
  -> get_command(name)                 # looks up name in commands_snapshot.json
  -> dispatch_command(name, prompt)    # src/command_implementations/__init__.py
       -> COMMAND_DISPATCH[name](prompt)   # calls the actual handler
```

If `get_command` returns `None`, `execute_command` returns a `CommandExecution` with
`handled=False`. If `dispatch_command` returns `None` (name not in `COMMAND_DISPATCH`),
`execute_command` returns a stub message, with `handled=True`.

`CommandExecution` is a frozen dataclass:

```python
@dataclass(frozen=True)
class CommandExecution:
    name: str
    source_hint: str
    prompt: str
    handled: bool
    message: str
```

### The `prompt` Parameter

Every handler receives a single `prompt: str` argument — the raw text the user typed after the
command name. Handlers may inspect, strip, or split this string however they need. There is no
JSON parsing layer at the command level (unlike tool handlers, which parse JSON payloads).

---

## Session and Context Commands

These commands are implemented in `src/command_implementations/core_commands.py`.

---

### help

Displays available commands or details about a specific command.

**Prompt behaviour**

- Empty prompt: lists all commands from `PORTED_COMMANDS`, grouped by the first path segment of
  each command's `source_hint` (e.g. `commands/`, `skills/`, `plugins/`).
- Non-empty prompt: searches `PORTED_COMMANDS` for one match by name and shows detailed info.

**Example — list all commands**

```
/help
```

Returns:
```
claw-code — 42 commands available

[commands]
  /clear — ...
  /compact — ...
  ...

Use '/help <command>' for details on a specific command.
```

**Example — single command details**

```
/help version
```

Returns:
```
/version
  Responsibility: Command module mirrored from archived TypeScript path commands/version.ts
  Source: commands/version.ts
  Status: mirrored
```

If no matching command is found:
```
No command found matching: <prompt>
```

---

### version

Reports the version of the claw-code port along with Python and platform information.

**Prompt behaviour**

Prompt is ignored.

**Return format**

```
claw-code v0.1.0
Python 3.11.4 (main, ...)
Platform: Windows-11-10.0.26200-SP0
```

---

### clear

Signals that the conversation context should be cleared.

Note: in the port this is a no-op stub that returns a confirmation string. No actual context
state is modified.

**Prompt behaviour**

Prompt is ignored.

**Return format**

```
Conversation cleared. Starting fresh context.
```

---

### compact

Signals that older messages in the conversation should be summarised.

Note: in the port this is a no-op stub. No actual summarisation takes place.

**Prompt behaviour**

Prompt is ignored.

**Return format**

```
Conversation compacted. Older messages summarized.
```

---

### status

Reports live runtime state from the in-process stores.

**Prompt behaviour**

Prompt is ignored.

**Return format**

```
Platform: Windows-11-10.0.26200-SP0
Python: 3.11.4
Plan mode: False
Worktree mode: False
Active tasks: 3
Active agents: 1
```

- `Plan mode` and `Worktree mode` reflect the current values of `stores.get_mode_flag`.
- `Active tasks` is `len(stores.list_tasks())`.
- `Active agents` is `len(stores.list_agents())`.

---

### cost

Reports token usage.

Note: the port does not connect to a real billing API. This command always returns a placeholder.

**Prompt behaviour**

Prompt is ignored.

**Return format**

```
Usage tracking: word-count approximation (no real token billing in port).
No cost data available.
```

---

## Session Management Commands

These commands are implemented in `src/command_implementations/session_commands.py`.

---

### model

Displays the currently configured model name.

**Prompt behaviour**

Prompt is ignored.

**Return format**

```
Current model: claude-opus-4-6
To change: set config model=<model-name>
```

The model name comes from `stores.get_config("model", "claude-opus-4-6")`. If no `model` key
has been set via `ConfigTool` or the `/config` command, the default `claude-opus-4-6` is shown.

---

### memory

Searches for a `CLAUDE.md` file starting from the current working directory and walking up
parent directories.

**Prompt behaviour**

Prompt is ignored.

**Return format — file found**

```
Memory file: /home/user/project/CLAUDE.md

<full contents of CLAUDE.md>
```

**Return format — file not found**

```
No CLAUDE.md memory file found in current directory or any parent directory.
Create a CLAUDE.md file in your project root to store persistent instructions.
```

**Error cases**

If the file is found but cannot be read:
```
Error reading memory file /path/to/CLAUDE.md: <detail>
```

---

### session

Shows the current session ID from the config store.

**Prompt behaviour**

Prompt is ignored.

**Return format**

```
Session ID: abc123def456
Use 'python -m src.main load-session <id>' to restore a session.
```

The session ID comes from `stores.get_config("session_id", "(no active session)")`. If no
session has been started, the placeholder `(no active session)` is shown.

---

### summary

Renders a Markdown summary of the Python porting workspace by delegating to
`QueryEnginePort.from_workspace().render_summary()`.

**Prompt behaviour**

Prompt is ignored.

**Return format**

A multi-section Markdown report covering porting progress, module counts, and tool/command
inventory statistics. Exact content depends on the current state of the workspace.

---

### doctor

Runs a self-check on the claw-code installation and reports pass/fail for each check.

**Prompt behaviour**

Prompt is ignored.

**Checks performed**

| Check                      | Pass condition                                           |
|----------------------------|----------------------------------------------------------|
| Python >= 3.10             | `sys.version_info >= (3, 10)`                            |
| `tools_snapshot.json`      | File exists at `src/reference_data/tools_snapshot.json`  |
| `commands_snapshot.json`   | File exists at `src/reference_data/commands_snapshot.json`|
| stores accessible          | `stores.list_tasks()` does not raise an exception        |

**Return format**

```
claw-code doctor report

  [PASS] Python >= 3.10: 3.11.4
  [PASS] tools_snapshot.json: /abs/path/to/tools_snapshot.json
  [PASS] commands_snapshot.json: /abs/path/to/commands_snapshot.json
  [PASS] stores accessible: ok

Overall: OK
```

If any check fails, the status shows `[FAIL]` for that line and the final line reads
`Overall: ISSUES FOUND`.

---

## Configuration Commands

These commands are implemented in `src/command_implementations/config_commands.py`.

---

### config

Reads or writes the in-process config store. This command is a thin wrapper around
`ConfigTool`'s `handle_config` function, adapting the prompt string into a JSON payload.

**Prompt parsing rules**

| Prompt form           | Action performed                    | Example               |
|-----------------------|-------------------------------------|-----------------------|
| Empty string          | List all config as JSON             | `/config`             |
| `key=value`           | Set `key` to `value`                | `/config model=claude-opus-4-6` |
| Any other string      | Get value for that key              | `/config model`       |

**Return format — list**

```json
{
  "model": "claude-opus-4-6",
  "session_id": "abc123"
}
```

**Return format — get**

```
claude-opus-4-6
```

(Raw string; empty string if key not found.)

**Return format — set**

```
Set model = claude-opus-4-6
```

---

### permissions

Describes the permission model used by claw-code.

**Prompt behaviour**

Prompt is ignored.

**Return format**

```
Permission model: deny-list based (ToolPermissionContext).
Configure via: --deny-tool <name> --deny-prefix <prefix>
Bash is automatically gated unless explicitly routed.
```

---

### hooks

Reports the current hook configuration.

**Prompt behaviour**

Prompt is ignored.

**Return format**

```
No hooks configured.
Hooks can be configured in CLAUDE.md or via session setup.
```

---

### skills

Lists any commands in `PORTED_COMMANDS` whose `source_hint` contains the substring `skills`.

**Prompt behaviour**

Prompt is ignored.

**Return format — skills found**

```
Available skills:
  /my-skill — description
```

**Return format — none found**

```
No skills registered.
```

---

### mcp

Describes the MCP (Model Context Protocol) integration status.

**Prompt behaviour**

Prompt is ignored.

**Return format**

```
MCP (Model Context Protocol) server management.
This port does not include a live MCP client.
MCP tool stubs are available in the tool inventory.
```

---

### tasks

Lists all tasks currently in the in-process task store.

**Prompt behaviour**

Prompt is ignored.

**Return format — tasks exist**

JSON array of `TaskRecord` objects (2-space indent):

```json
[
  {
    "task_id": "a1b2c3d4e5f6",
    "name": "my task",
    "description": "details",
    "status": "pending",
    "output": ""
  }
]
```

**Return format — no tasks**

```
No tasks.
```

---

## Unimplemented Commands (Stubs)

The following commands appear in `commands_snapshot.json` and are therefore visible in the
command inventory, but have no entry in `COMMAND_DISPATCH`. Calling `execute_command` on any
of these returns a mirrored-command stub message with `handled=True`.

| Command name         | Source hint                                  | Notes                                           |
|----------------------|----------------------------------------------|-------------------------------------------------|
| `add-dir`            | `commands/add-dir/add-dir.tsx`               | Adds a directory to context                     |
| `advisor`            | `commands/advisor.ts`                        | AI advisor feature                              |
| `agents`             | `commands/agents/agents.tsx`                 | Agent management UI                             |
| `ant-trace`          | `commands/ant-trace/index.js`                | Internal tracing tool                           |
| `autofix-pr`         | `commands/autofix-pr/index.js`               | PR auto-fix workflow                            |
| `backfill-sessions`  | `commands/backfill-sessions/index.js`        | Session history backfill                        |
| `branch`             | `commands/branch/branch.ts`                  | Git branch management                           |
| `break-cache`        | `commands/break-cache/index.js`              | Cache-busting utility                           |
| `bridge`             | `commands/bridge/bridge.tsx`                 | Bridge runtime integration                      |
| `bridge-kick`        | `commands/bridge-kick.ts`                    | Bridge session kick                             |
| `brief`              | `commands/brief.ts`                          | File/image attachment (BriefTool dependency)    |
| `commit`             | `commands/commit/...`                        | Git commit workflow                             |
| `review`             | `commands/review/...`                        | Code review workflow                            |
| `pr`                 | `commands/pr/...`                            | Pull request workflow                           |
| `release`            | `commands/release/...`                       | Release workflow                                |
| `vim`                | `commands/vim/...`                           | Vim keybinding mode                             |

This list is a representative subset. The full snapshot contains many additional commands
across plugin and skill namespaces.

---

## CLI Usage Examples

Commands are invoked with the `exec-command` subcommand:

```bash
python -m src.main exec-command <command-name> '<prompt-text>'
```

**Show help for all commands**

```bash
python -m src.main exec-command help ''
```

**Show help for a specific command**

```bash
python -m src.main exec-command help 'version'
```

**Show version info**

```bash
python -m src.main exec-command version ''
```

**Run the doctor check**

```bash
python -m src.main exec-command doctor ''
```

**Show runtime status**

```bash
python -m src.main exec-command status ''
```

**List all config values**

```bash
python -m src.main exec-command config ''
```

**Get a config value**

```bash
python -m src.main exec-command config 'model'
```

**Set a config value**

```bash
python -m src.main exec-command config 'model=claude-opus-4-6'
```

**Show current model**

```bash
python -m src.main exec-command model ''
```

**Read the memory file**

```bash
python -m src.main exec-command memory ''
```

**Show session ID**

```bash
python -m src.main exec-command session ''
```

**List all tasks**

```bash
python -m src.main exec-command tasks ''
```

**Show MCP status**

```bash
python -m src.main exec-command mcp ''
```

**Show permissions model**

```bash
python -m src.main exec-command permissions ''
```

You can also use the higher-level `commands` subcommand to search and list the full inventory
without executing:

```bash
# List all commands (up to 20)
python -m src.main commands

# Search by name
python -m src.main commands --query version

# Show details for one command
python -m src.main show-command help
```

---

## Adding New Command Implementations

1. Create a handler function in an appropriate file under `src/command_implementations/`.
   The signature must be:

   ```python
   def handle_my_command(prompt: str) -> str:
       ...
   ```

   The `prompt` parameter is the raw string typed after the command name. Strip and parse it
   however the command requires.

2. Import the handler in `src/command_implementations/__init__.py` and add it to
   `COMMAND_DISPATCH`:

   ```python
   from .my_module import handle_my_command

   COMMAND_DISPATCH: dict[str, object] = {
       ...
       "my-command": handle_my_command,
   }
   ```

3. Verify that the command name exists in `src/reference_data/commands_snapshot.json`. If it
   does not, add an entry so `get_command` can locate it:

   ```json
   {"name": "my-command", "source_hint": "commands/my-command/index.ts",
    "responsibility": "..."}
   ```

4. Test with:

   ```bash
   python -m src.main exec-command my-command 'some prompt text'
   ```

The handler is now live and will be called whenever `exec-command my-command` is run.
