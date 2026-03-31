# Tool Implementations Reference

This document covers every tool handler that executes real logic in the claw-code Python port.
Tools that are registered in `TOOL_DISPATCH` run actual code; all other tools from the snapshot
inventory fall through to a stub message that describes what the original TypeScript tool would
have done.

---

## How Tools Are Invoked

### Dispatcher Chain

```
execute_tool(name, payload)          # src/tools.py
  -> get_tool(name)                  # looks up name in tools_snapshot.json
  -> dispatch_tool(name, payload)    # src/tool_implementations/__init__.py
       -> TOOL_DISPATCH[name](payload)   # calls the actual handler
```

If `get_tool` returns `None`, `execute_tool` returns a `ToolExecution` with `handled=False`.
If `dispatch_tool` returns `None` (name not in `TOOL_DISPATCH`), `execute_tool` returns a
stub message describing what the original tool would have handled, with `handled=True`.

`ToolExecution` is a frozen dataclass:

```python
@dataclass(frozen=True)
class ToolExecution:
    name: str
    source_hint: str
    payload: str
    handled: bool
    message: str
```

### Payload Parsing

Every handler uses the same three-way parse at the top:

```python
try:
    params = json.loads(payload) if payload.strip() else {}
except json.JSONDecodeError:
    params = {"input": payload}
```

- Empty string or whitespace-only payload -> `{}`
- Valid JSON string -> parsed dict
- Non-JSON string -> `{"input": payload}`

All fields then come from `params.get(...)` with sensible defaults.

---

## Core I/O Tools

### BashTool

Runs a shell command in the current working directory using `subprocess.run` with `shell=True`.

**Payload schema**

| Field     | Type   | Required | Default   | Description                          |
|-----------|--------|----------|-----------|--------------------------------------|
| `command` | string | yes      | —         | The shell command to run             |
| `timeout` | int    | no       | `120000`  | Timeout in milliseconds              |

**Blocked patterns**

The following patterns are rejected before execution:

- `rm -rf /`
- `rm -fr /`
- `mkfs`
- `dd if=/dev/`
- `:(){:|:&};:`

**Output truncation**

Output longer than 100,000 characters is truncated with `\n[output truncated]` appended.

**Return format**

On success: combined stdout + stderr as a plain string (stdout first, then stderr appended).
Empty string if no output was produced.

**Example**

```json
{"command": "echo hello", "timeout": 5000}
```

Returns:
```
hello
```

**Error cases**

| Condition             | Return value                                          |
|-----------------------|-------------------------------------------------------|
| `command` missing     | `Error: command is required`                          |
| Blocked pattern       | `Error: Command blocked for safety reasons (matched pattern: 'rm -rf /')` |
| Timeout               | `Error: Command timed out after 120s`                 |
| Permission denied     | `Error: Permission denied: <detail>`                  |
| OS error              | `Error: <detail>`                                     |

---

### FileReadTool

Reads a file from disk, decodes it as UTF-8, and returns numbered lines.

**Payload schema**

| Field       | Type   | Required | Default | Description                                        |
|-------------|--------|----------|---------|----------------------------------------------------|
| `file_path` | string | yes      | —       | Absolute or relative path to the file              |
| `offset`    | int    | no       | `0`     | Line number to start from (0-based)                |
| `limit`     | int    | no       | `2000`  | Maximum number of lines to return                  |

**Return format**

Lines are returned in `cat -n` style:

```
1	first line content
2	second line content
3	third line content
```

Tab-separated: line number, then line content with trailing newlines stripped.

For binary files (UTF-8 decode fails):

```
Binary file: 4096 bytes
```

**Example**

```json
{"file_path": "/home/user/project/main.py", "offset": 0, "limit": 50}
```

**Error cases**

| Condition         | Return value                              |
|-------------------|-------------------------------------------|
| `file_path` empty | `Error: file_path is required`            |
| File not found    | `Error: File not found: <path>`           |
| Path is directory | `Error: Path is a directory: <path>`      |
| Permission denied | `Error: Permission denied: <path>`        |
| OS error          | `Error reading file: <detail>`            |

---

### FileWriteTool

Writes content to a file, creating parent directories if they do not exist.
Overwrites the file if it already exists.

**Payload schema**

| Field       | Type   | Required | Default | Description                       |
|-------------|--------|----------|---------|-----------------------------------|
| `file_path` | string | yes      | —       | Path to write to                  |
| `content`   | string | no       | `""`    | File content (UTF-8 encoded)      |

**Return format**

```
File written: /path/to/file.py (1234 bytes)
```

Byte count is the UTF-8 encoded size of `content`.

**Example**

```json
{"file_path": "/tmp/hello.txt", "content": "Hello, world!\n"}
```

Returns:
```
File written: /tmp/hello.txt (14 bytes)
```

**Error cases**

| Condition         | Return value                           |
|-------------------|----------------------------------------|
| `file_path` empty | `Error: file_path is required`         |
| Permission denied | `Error: Permission denied: <path>`     |
| OS error          | `Error writing file: <detail>`         |

---

### FileEditTool

Performs exact string replacement in an existing file. Does not support regex or line-number
addressing; the old string must appear verbatim.

**Payload schema**

| Field         | Type    | Required | Default | Description                                                |
|---------------|---------|----------|---------|------------------------------------------------------------|
| `file_path`   | string  | yes      | —       | Path to the file to edit                                   |
| `old_string`  | string  | no       | `""`    | Exact text to find and replace                             |
| `new_string`  | string  | no       | `""`    | Replacement text                                           |
| `replace_all` | boolean | no       | `false` | Replace every occurrence; default replaces only the first  |

**Uniqueness enforcement**

When `replace_all` is `false` (the default), the tool checks that `old_string` appears exactly
once. If it appears more than once, an error is returned asking the caller to add more context or
use `replace_all=true`.

**Return format**

```
Edited /path/to/file.py: replaced 1 occurrence(s) of 'def old_func' with 'def new_func'
```

The preview of old/new strings is truncated to 60 characters and newlines are shown as `\n`.

**Example**

```json
{
  "file_path": "/src/app.py",
  "old_string": "def greet():\n    print('hello')",
  "new_string": "def greet():\n    print('hi')"
}
```

**Error cases**

| Condition                               | Return value                                                                 |
|-----------------------------------------|------------------------------------------------------------------------------|
| `file_path` empty                       | `Error: file_path is required`                                               |
| File not found                          | `Error: File not found: <path>`                                              |
| Path is directory                       | `Error: Path is a directory: <path>`                                         |
| Permission denied (read)                | `Error: Permission denied: <path>`                                           |
| `old_string` not found                  | `Error: old_string not found in <path>`                                      |
| `old_string` found N>1 times            | `Error: old_string appears N times in <path>. Use replace_all=true...`       |
| Permission denied (write)               | `Error: Permission denied writing: <path>`                                   |
| OS error                                | `Error writing file: <detail>`                                               |

---

### GlobTool

Finds files matching a glob pattern using Python's `pathlib.Path.glob`.

**Payload schema**

| Field     | Type   | Required | Default  | Description                          |
|-----------|--------|----------|----------|--------------------------------------|
| `pattern` | string | no       | `**/*`   | Glob pattern to match                |
| `path`    | string | no       | `"."`    | Root directory to search from        |

**Return format**

Newline-separated file paths, sorted by modification time descending (most recently modified
first). At most 1000 results are returned.

Empty string if no matches are found.

**Example**

```json
{"pattern": "**/*.py", "path": "/home/user/project"}
```

Returns:
```
/home/user/project/src/main.py
/home/user/project/src/utils.py
/home/user/project/tests/test_main.py
```

**Error cases**

| Condition             | Return value                             |
|-----------------------|------------------------------------------|
| Path does not exist   | `Error: Path does not exist: <path>`     |
| OS error              | `Error: <detail>`                        |
| Invalid pattern       | `Error: Invalid glob pattern: <detail>`  |

---

### GrepTool

Searches file contents using Python's `re` module. Supports three output modes, optional
context lines, case-insensitive matching, and glob file filters.

**Payload schema**

| Field         | Type    | Required | Default              | Description                                           |
|---------------|---------|----------|----------------------|-------------------------------------------------------|
| `pattern`     | string  | yes      | —                    | Regular expression pattern                            |
| `path`        | string  | no       | `"."`                | Directory or file to search                           |
| `glob`        | string  | no       | `null`               | Glob filter applied to filenames (e.g. `"*.py"`)      |
| `output_mode` | string  | no       | `"files_with_matches"` | One of `files_with_matches`, `content`, `count`     |
| `head_limit`  | int     | no       | `250`                | Maximum number of results to return                   |
| `-i`          | boolean | no       | `false`              | Case-insensitive matching                             |
| `-n`          | boolean | no       | `true`               | Include line numbers in `content` mode                |
| `context`     | int     | no       | `0`                  | Lines of context around each match in `content` mode  |

**Output modes**

- `files_with_matches`: returns one file path per line (default)
- `content`: returns `filepath:lineno:line` for each matching line
- `count`: returns `filepath: N` for each file with matches

**Example — files mode**

```json
{"pattern": "def handle_", "path": "/src", "glob": "*.py"}
```

Returns:
```
src/tool_implementations/bash_tool.py
src/tool_implementations/glob_tool.py
```

**Example — content mode with context**

```json
{
  "pattern": "import json",
  "path": "/src/tool_implementations/bash_tool.py",
  "output_mode": "content",
  "context": 1
}
```

Returns:
```
src/tool_implementations/bash_tool.py:1:from __future__ import annotations
src/tool_implementations/bash_tool.py:2:
src/tool_implementations/bash_tool.py:3:import json
src/tool_implementations/bash_tool.py:4:import os
```

**Error cases**

| Condition           | Return value                               |
|---------------------|--------------------------------------------|
| `pattern` empty     | `Error: pattern is required`               |
| Invalid regex       | `Error: Invalid regex pattern: <detail>`   |
| Path does not exist | `Error: Path does not exist: <path>`       |

---

## Task Management Tools

Tasks are stored in an in-process dict (see `src/stores.py`). All task IDs are 12-character
hex strings generated from `uuid4`.

### TaskRecord shape

```json
{
  "task_id": "a1b2c3d4e5f6",
  "name": "my task",
  "description": "optional description",
  "status": "pending",
  "output": ""
}
```

Valid status values: `pending`, `in_progress`, `completed`, `stopped`.

---

### TaskCreateTool

Creates a new task with status `pending`.

**Payload schema**

| Field         | Type   | Required | Default | Description              |
|---------------|--------|----------|---------|--------------------------|
| `name`        | string | yes      | —       | Task name                |
| `description` | string | no       | `""`    | Optional description     |

**Return format**

JSON-serialized `TaskRecord` (2-space indent).

**Example**

```json
{"name": "refactor auth module", "description": "split into smaller functions"}
```

Returns:
```json
{
  "task_id": "a1b2c3d4e5f6",
  "name": "refactor auth module",
  "description": "split into smaller functions",
  "status": "pending",
  "output": ""
}
```

**Error cases**

| Condition    | Return value                  |
|--------------|-------------------------------|
| `name` empty | `Error: name is required`     |

---

### TaskGetTool

Retrieves a single task by ID.

**Payload schema**

| Field     | Type   | Required | Description   |
|-----------|--------|----------|---------------|
| `task_id` | string | yes      | Task ID       |

**Return format**

JSON-serialized `TaskRecord` if found.

**Error cases**

| Condition         | Return value                       |
|-------------------|------------------------------------|
| `task_id` empty   | `Error: task_id is required`       |
| Task not found    | `Task not found: <task_id>`        |

---

### TaskListTool

Returns all tasks in the in-process store.

**Payload schema**

No fields required. Payload is ignored.

**Return format**

JSON array of `TaskRecord` objects (2-space indent). Empty array `[]` if no tasks exist.

---

### TaskUpdateTool

Updates the `status` field of an existing task.

**Payload schema**

| Field     | Type   | Required | Description                     |
|-----------|--------|----------|---------------------------------|
| `task_id` | string | yes      | Task ID to update               |
| `status`  | string | yes      | New status string               |

**Return format**

JSON-serialized updated `TaskRecord`.

**Error cases**

| Condition         | Return value                        |
|-------------------|-------------------------------------|
| `task_id` empty   | `Error: task_id is required`        |
| `status` empty    | `Error: status is required`         |
| Task not found    | `Task not found: <task_id>`         |

---

### TaskOutputTool

Records an output string against a task without changing its status.

**Payload schema**

| Field     | Type   | Required | Default | Description           |
|-----------|--------|----------|---------|-----------------------|
| `task_id` | string | yes      | —       | Task ID               |
| `output`  | string | no       | `""`    | Output string to store|

**Return format**

JSON-serialized updated `TaskRecord`.

**Error cases**

| Condition         | Return value                  |
|-------------------|-------------------------------|
| `task_id` empty   | `Error: task_id is required`  |
| Task not found    | `Task not found: <task_id>`   |

---

### TaskStopTool

Sets task status to `stopped`.

**Payload schema**

| Field     | Type   | Required | Description   |
|-----------|--------|----------|---------------|
| `task_id` | string | yes      | Task ID       |

**Return format**

JSON-serialized updated `TaskRecord` with `"status": "stopped"`.

**Error cases**

| Condition         | Return value                  |
|-------------------|-------------------------------|
| `task_id` empty   | `Error: task_id is required`  |
| Task not found    | `Task not found: <task_id>`   |

---

## Team Tools

Teams are stored in an in-process dict alongside tasks. A `TeamRecord` holds a name and a
tuple of member name strings.

### TeamRecord shape

```json
{
  "team_id": "b2c3d4e5f6a1",
  "name": "backend",
  "member_names": ["alice", "bob"]
}
```

---

### TeamCreateTool

Creates a new team.

**Payload schema**

| Field     | Type             | Required | Default | Description             |
|-----------|------------------|----------|---------|-------------------------|
| `name`    | string           | yes      | —       | Team name               |
| `members` | array of strings | no       | `[]`    | Initial member names    |

**Return format**

JSON object (not the full dataclass — keys are `team_id`, `name`, `member_names`).

**Example**

```json
{"name": "backend", "members": ["alice", "bob"]}
```

Returns:
```json
{"team_id": "b2c3d4e5f6a1", "name": "backend", "member_names": ["alice", "bob"]}
```

**Error cases**

| Condition              | Return value                        |
|------------------------|-------------------------------------|
| `name` empty           | `Error: name is required`           |
| `members` not a list   | `Error: members must be a list`     |

---

### TeamDeleteTool

Deletes a team by ID.

**Payload schema**

| Field     | Type   | Required | Description   |
|-----------|--------|----------|---------------|
| `team_id` | string | yes      | Team ID       |

**Return format**

```
Team <team_id> deleted.
```

**Error cases**

| Condition         | Return value                    |
|-------------------|---------------------------------|
| `team_id` empty   | `Error: team_id is required`    |
| Team not found    | `Team not found: <team_id>`     |

---

### SendMessageTool

Sends a message to a named member of a team. Internally this records the message as a new
`AgentRecord` in the agent store (a design simplification in the port).

**Payload schema**

| Field     | Type   | Required | Description                          |
|-----------|--------|----------|--------------------------------------|
| `team_id` | string | yes      | Target team                          |
| `member`  | string | yes      | Member name within the team          |
| `message` | string | yes      | Message body                         |

**Return format**

```
Message delivered to alice in team b2c3d4e5f6a1.
```

**Error cases**

| Condition         | Return value                           |
|-------------------|----------------------------------------|
| `team_id` empty   | `Error: team_id is required`           |
| `member` empty    | `Error: member is required`            |
| `message` empty   | `Error: message is required`           |
| Team not found    | `Error: Team not found: <team_id>`     |

---

## Agent Tools

All four agent handlers write to the in-process agent store. Agents are not actually executed
against a model; the store records prompt, status, and result strings only.

### AgentRecord shape

```json
{
  "agent_id": "c3d4e5f6a1b2",
  "prompt": "summarise the codebase",
  "status": "running",
  "result": "",
  "parent_id": ""
}
```

Valid status values: `running`, `completed`.

---

### AgentTool

Creates an agent record with status `running`. Does not execute the prompt.

**Payload schema**

| Field    | Type   | Required | Description            |
|----------|--------|----------|------------------------|
| `prompt` | string | yes      | Prompt for the agent   |

**Return format**

```json
{"agent_id": "c3d4e5f6a1b2", "status": "running", "prompt": "summarise the codebase"}
```

**Error cases**

| Condition      | Return value                  |
|----------------|-------------------------------|
| `prompt` empty | `Error: prompt is required`   |

---

### runAgent

Creates an agent record and immediately marks it `completed` with a synthetic result. Simulates
synchronous agent execution.

**Payload schema**

| Field    | Type   | Required | Description            |
|----------|--------|----------|------------------------|
| `prompt` | string | yes      | Prompt for the agent   |

**Return format**

```json
{
  "agent_id": "c3d4e5f6a1b2",
  "status": "completed",
  "prompt": "summarise the codebase",
  "result": "Agent completed: summarise the codebase"
}
```

The `result` field is always the string `"Agent completed: "` followed by the first 50 characters
of the prompt.

**Error cases**

| Condition      | Return value                  |
|----------------|-------------------------------|
| `prompt` empty | `Error: prompt is required`   |

---

### forkSubagent

Creates a child agent that records its parent's ID.

**Payload schema**

| Field             | Type   | Required | Default | Description                     |
|-------------------|--------|----------|---------|---------------------------------|
| `prompt`          | string | yes      | —       | Prompt for the child agent      |
| `parent_agent_id` | string | no       | `""`    | ID of the spawning parent agent |

**Return format**

```json
{"agent_id": "d4e5f6a1b2c3", "parent_id": "c3d4e5f6a1b2", "status": "running"}
```

**Error cases**

| Condition      | Return value                  |
|----------------|-------------------------------|
| `prompt` empty | `Error: prompt is required`   |

---

### spawnMultiAgent

Creates multiple agents in a single call.

**Payload schema**

| Field    | Type            | Required | Description                               |
|----------|-----------------|----------|-------------------------------------------|
| `agents` | array of objects| yes      | Each object must have a `prompt` string   |

Objects in the `agents` list without a `prompt` key (or with an empty prompt) are silently skipped.

**Return format**

```json
{
  "spawned": 2,
  "agent_ids": ["d4e5f6a1b2c3", "e5f6a1b2c3d4"],
  "agents": [
    {"agent_id": "d4e5f6a1b2c3", "prompt": "task one", "status": "running"},
    {"agent_id": "e5f6a1b2c3d4", "prompt": "task two", "status": "running"}
  ]
}
```

**Error cases**

| Condition              | Return value                     |
|------------------------|----------------------------------|
| `agents` not a list    | `Error: agents must be a list`   |

---

## Web and Interaction Tools

### WebFetchTool

Fetches a URL using Python's stdlib `urllib.request`. Returns raw response body decoded as
UTF-8. Reads at most 100,000 bytes.

**Payload schema**

| Field | Type   | Required | Description    |
|-------|--------|----------|----------------|
| `url` | string | yes      | URL to fetch   |

**Return format**

Raw response body as a string (HTML, JSON, plain text, etc.).

**Example**

```json
{"url": "https://example.com/api/data.json"}
```

**Error cases**

| Condition         | Return value                                           |
|-------------------|--------------------------------------------------------|
| `url` empty       | `Error: url is required`                               |
| HTTP error        | `Error: HTTP 404 Not Found for URL: <url>`             |
| URL error         | `Error: URL error for <url>: <reason>`                 |
| Invalid URL       | `Error: Invalid URL '<url>': <detail>`                 |
| OS/network error  | `Error fetching <url>: <detail>`                       |

---

### WebSearchTool

Stub: web search requires an external API key that is not configured in this port.

**Payload schema**

| Field   | Type   | Required | Description        |
|---------|--------|----------|--------------------|
| `query` | string | no       | Search query       |

**Return format**

```
Web search is not available without an external API key.
Query: <query>

To enable web search, configure a search API key in config.
```

---

### AskUserQuestionTool

Prompts the user for input when stdin is a TTY. Falls back to a non-interactive message
when stdin is not a terminal (e.g., in scripts or pipelines).

**Payload schema**

| Field      | Type            | Required | Default | Description                         |
|------------|-----------------|----------|---------|-------------------------------------|
| `question` | string          | no       | `""`    | Question to display                 |
| `options`  | array of strings| no       | `[]`    | Numbered options to display         |

If `question` is absent, the handler falls back to the `input` key (non-JSON payload path).

**Return format**

- TTY mode: whatever the user typed at the prompt (a single line)
- Non-TTY mode: `[Non-interactive mode] Question: <question>`
- TTY with EOF: `[No input received]`

**Example**

```json
{"question": "Which approach do you prefer?", "options": ["refactor", "rewrite"]}
```

TTY output shown to user:
```
Which approach do you prefer?
  1. refactor
  2. rewrite
```

---

## Data Management Tools

### TodoWriteTool

Manages a todo list in the in-process store. Supports single creation, batch creation,
completion, deletion, and listing through a single tool entry point.

**Payload schema (action=list or default)**

| Field    | Type   | Default  | Description        |
|----------|--------|----------|--------------------|
| `action` | string | `""`     | `"list"` to list   |

Returns JSON array of all `TodoItem` objects.

**Payload schema (action=complete)**

| Field     | Type   | Required | Description       |
|-----------|--------|----------|-------------------|
| `action`  | string | yes      | `"complete"`      |
| `todo_id` | string | yes      | ID to complete    |

**Payload schema (action=delete)**

| Field     | Type   | Required | Description       |
|-----------|--------|----------|-------------------|
| `action`  | string | yes      | `"delete"`        |
| `todo_id` | string | yes      | ID to delete      |

**Payload schema (batch create)**

| Field   | Type                         | Required | Description                                           |
|---------|------------------------------|----------|-------------------------------------------------------|
| `todos` | array of `{content, done?}`  | yes      | Each item needs `content`; `done: true` pre-completes |

**Payload schema (single create)**

| Field     | Type    | Required | Default | Description                       |
|-----------|---------|----------|---------|-----------------------------------|
| `content` | string  | yes      | —       | Todo text                         |
| `done`    | boolean | no       | `false` | If true, mark completed on create |

**TodoItem shape**

```json
{"todo_id": "f6a1b2c3d4e5", "content": "write tests", "done": false}
```

**Example — batch create**

```json
{
  "todos": [
    {"content": "write tests"},
    {"content": "update docs", "done": true}
  ]
}
```

**Error cases**

| Condition                              | Return value                                           |
|----------------------------------------|--------------------------------------------------------|
| `action=complete` without `todo_id`    | `Error: todo_id is required for action=complete`       |
| `action=delete` without `todo_id`      | `Error: todo_id is required for action=delete`         |
| `action=complete` unknown ID           | `Error: Todo not found: <todo_id>`                     |
| `action=delete` unknown ID             | `Error: Todo not found: <todo_id>`                     |
| `todos` key present but not a list     | `Error: todos must be a list`                          |

---

### ConfigTool

Reads and writes key-value pairs in the in-process config store. The config store is a plain
`dict[str, str]`; values are always strings.

**Payload schema**

| Field    | Type   | Required | Default  | Description             |
|----------|--------|----------|----------|-------------------------|
| `action` | string | no       | `"list"` | `"list"`, `"get"`, `"set"` |
| `key`    | string | conditional | —    | Required for get/set    |
| `value`  | string | conditional | `""` | Required (or empty) for set |

**Return format**

- `action=list`: JSON object of all config keys and values (2-space indent)
- `action=get`: raw string value, or empty string if key is not set
- `action=set`: `Set <key> = <value>`

**Example**

```json
{"action": "set", "key": "model", "value": "claude-opus-4-6"}
```

Returns:
```
Set model = claude-opus-4-6
```

**Error cases**

| Condition                  | Return value                             |
|----------------------------|------------------------------------------|
| `action=get` without `key` | `Error: key is required for action=get`  |
| `action=set` without `key` | `Error: key is required for action=set`  |

---

### ToolSearchTool

Searches the tool inventory (loaded from `tools_snapshot.json`) by name or source hint.

**Payload schema**

| Field         | Type   | Required | Default | Description                       |
|---------------|--------|----------|---------|-----------------------------------|
| `query`       | string | yes      | —       | Substring to search for           |
| `max_results` | int    | no       | `5`     | Maximum number of results         |

The search is case-insensitive substring match against `name` and `source_hint` fields.

**Return format**

```
Found 2 tools:
- BashTool: Tool module mirrored from archived TypeScript path tools/BashTool/BashTool.tsx
  source: tools/BashTool/BashTool.tsx
- WebFetchTool: Tool module mirrored from archived TypeScript path tools/WebFetchTool/WebFetchTool.tsx
  source: tools/WebFetchTool/WebFetchTool.tsx
```

**Error cases**

| Condition      | Return value                             |
|----------------|------------------------------------------|
| `query` empty  | `Error: query is required`               |
| No matches     | `No tools found matching: <query>`       |

---

## Mode Tools

Mode flags are stored in the in-process `_mode_flags` dict in `stores.py`. The two flags are
`plan_mode` and `worktree_mode`, both defaulting to `False`.

### EnterPlanModeTool

Sets `plan_mode` to `True`.

**Payload schema**

No fields. Payload is ignored.

**Return format**

```
Plan mode activated. All tool calls will be planned before execution.
```

---

### ExitPlanModeV2Tool

Sets `plan_mode` to `False`.

**Payload schema**

No fields. Payload is ignored.

**Return format**

```
Plan mode deactivated.
```

---

### EnterWorktreeTool

Sets `worktree_mode` to `True`. Accepts optional `path` and `branch` fields in the payload
but does not act on them in this port.

**Payload schema**

| Field    | Type   | Required | Description                              |
|----------|--------|----------|------------------------------------------|
| `path`   | string | no       | Worktree path (accepted, not used)       |
| `branch` | string | no       | Branch name (accepted, not used)         |

**Return format**

```
Worktree mode activated.
```

---

### ExitWorktreeTool

Sets `worktree_mode` to `False`.

**Payload schema**

No fields. Payload is ignored.

**Return format**

```
Worktree mode deactivated.
```

---

## Notebook and Scheduling Tools

### NotebookEditTool

Edits a single cell in a Jupyter notebook (`.ipynb` file). Preserves the notebook's existing
line-list or plain-string source format.

**Payload schema**

| Field           | Type    | Required | Default  | Description                                        |
|-----------------|---------|----------|----------|----------------------------------------------------|
| `notebook_path` | string  | yes      | —        | Path to the `.ipynb` file                          |
| `cell_index`    | int     | yes      | —        | 0-based index of the cell to edit                  |
| `new_source`    | string  | no       | `""`     | New source content for the cell                    |
| `cell_type`     | string  | no       | `"code"` | Cell type (`"code"`, `"markdown"`, `"raw"`)        |

**Return format**

```
Notebook /path/to/notebook.ipynb: cell 2 updated (128 chars)
```

Character count is `len(new_source)`.

**Source format handling**

If the existing cell stores `source` as a list of strings (the standard ipynb format), the new
source is split on lines with `splitlines(keepends=True)` before writing. If `source` is a
plain string, it is written directly.

**Example**

```json
{
  "notebook_path": "/notebooks/analysis.ipynb",
  "cell_index": 0,
  "new_source": "import pandas as pd\nimport numpy as np",
  "cell_type": "code"
}
```

**Error cases**

| Condition                        | Return value                                                      |
|----------------------------------|-------------------------------------------------------------------|
| `notebook_path` empty            | `Error: notebook_path is required`                               |
| `cell_index` absent              | `Error: cell_index is required`                                  |
| `cell_index` not an integer      | `Error: cell_index must be an integer`                           |
| File not found                   | `Error: Notebook not found: <path>`                              |
| Invalid JSON                     | `Error: Not a valid notebook (JSON parse error): <detail>`       |
| OS read error                    | `Error reading notebook: <detail>`                               |
| Missing `cells` key              | `Error: Not a valid notebook (missing 'cells' key): <path>`      |
| Cell index out of range          | `Error: Cell index N out of range (notebook has M cells): <path>`|
| Permission denied (write)        | `Error: Permission denied writing: <path>`                       |
| OS write error                   | `Error writing notebook: <detail>`                               |

---

### CronCreateTool

Registers a cron-style scheduled command in the in-process cron store.

Note: this port records the entry in memory only. No actual scheduler is started.

**Payload schema**

| Field      | Type   | Required | Description                               |
|------------|--------|----------|-------------------------------------------|
| `schedule` | string | yes      | Cron expression (e.g. `"0 * * * *"`)      |
| `command`  | string | yes      | Shell command to schedule                 |

**Return format**

```json
{"cron_id": "a1b2c3d4e5f6", "schedule": "0 * * * *", "command": "python sync.py"}
```

**Error cases**

| Condition          | Return value                     |
|--------------------|----------------------------------|
| `schedule` empty   | `Error: schedule is required`    |
| `command` empty    | `Error: command is required`     |

---

### CronDeleteTool

Removes a cron entry by ID.

**Payload schema**

| Field     | Type   | Required | Description    |
|-----------|--------|----------|----------------|
| `cron_id` | string | yes      | Cron entry ID  |

**Return format**

```
Cron <cron_id> deleted.
```

**Error cases**

| Condition         | Return value                    |
|-------------------|---------------------------------|
| `cron_id` empty   | `Error: cron_id is required`    |
| Not found         | `Cron not found: <cron_id>`     |

---

### CronListTool

Returns all registered cron entries.

**Payload schema**

No fields. Payload is ignored.

**Return format**

JSON array of `CronEntry` objects (2-space indent):

```json
[
  {
    "cron_id": "a1b2c3d4e5f6",
    "schedule": "0 * * * *",
    "command": "python sync.py"
  }
]
```

Empty array `[]` if no entries exist.

---

## Unimplemented Tools (Stubs)

The following tools appear in `tools_snapshot.json` (and are therefore visible in the tool
inventory and can be routed to) but have no entry in `TOOL_DISPATCH`. Calling
`execute_tool` on any of these returns a stub message describing what the original TypeScript
tool would have handled, with `handled=True` and `message` set to the mirrored-tool description.

| Tool name              | Source hint                              | Why it remains a stub                          |
|------------------------|------------------------------------------|------------------------------------------------|
| `MCPTool`              | `tools/MCPTool/MCPTool.tsx`              | Requires a live MCP client/server; not ported  |
| `LSPTool`              | `tools/LSPTool/LSPTool.tsx`              | Requires a Language Server Process connection  |
| `PowerShellTool`       | `tools/PowerShellTool/PowerShellTool.tsx`| Windows-specific; deferred                    |
| `BriefTool`            | `tools/BriefTool/BriefTool.tsx`          | Requires image/file upload pipeline            |
| `ListMcpResourcesTool` | `tools/ListMcpResourcesTool/...`         | Part of MCP client; not ported                 |
| `ReadMcpResourceTool`  | `tools/ReadMcpResourceTool/...`          | Part of MCP client; not ported                 |
| `McpAuthTool`          | `tools/McpAuthTool/...`                  | Part of MCP auth flow; not ported              |
| `RemoteTriggerTool`    | `tools/RemoteTriggerTool/...`            | Requires remote runtime; not ported            |
| `SkillTool`            | `tools/SkillTool/...`                    | Skills subsystem not implemented               |
| `SyntheticOutputTool`  | `tools/SyntheticOutputTool/...`          | Internal output-simulation tool; not needed    |
| `TestingPermissionTool`| `tools/TestingPermissionTool/...`        | Test-only tool in original                     |

---

## CLI Usage Examples

Tools are invoked with the `exec-tool` subcommand:

```bash
python -m src.main exec-tool <ToolName> '<json-payload>'
```

**Run a shell command**

```bash
python -m src.main exec-tool BashTool '{"command": "git status"}'
```

**Read lines 100-150 of a file**

```bash
python -m src.main exec-tool FileReadTool '{"file_path": "src/tools.py", "offset": 99, "limit": 50}'
```

**Write a file**

```bash
python -m src.main exec-tool FileWriteTool '{"file_path": "/tmp/out.txt", "content": "hello\n"}'
```

**Edit a file**

```bash
python -m src.main exec-tool FileEditTool \
  '{"file_path": "src/app.py", "old_string": "v1.0", "new_string": "v1.1"}'
```

**Glob for Python files**

```bash
python -m src.main exec-tool GlobTool '{"pattern": "**/*.py", "path": "src"}'
```

**Grep for a pattern**

```bash
python -m src.main exec-tool GrepTool \
  '{"pattern": "def handle_", "path": "src", "glob": "*.py", "output_mode": "content"}'
```

**Create a task**

```bash
python -m src.main exec-tool TaskCreateTool '{"name": "my task", "description": "details"}'
```

**List all tasks**

```bash
python -m src.main exec-tool TaskListTool ''
```

**Create a cron entry**

```bash
python -m src.main exec-tool CronCreateTool '{"schedule": "0 * * * *", "command": "python sync.py"}'
```

**Enter plan mode**

```bash
python -m src.main exec-tool EnterPlanModeTool ''
```

**Search tool inventory**

```bash
python -m src.main exec-tool ToolSearchTool '{"query": "bash", "max_results": 3}'
```

---

## Adding New Tool Implementations

1. Create a new file in `src/tool_implementations/`, e.g. `my_tool.py`.

2. Define a handler function with the signature:

   ```python
   def handle_my_tool(payload: str) -> str:
       ...
   ```

3. Parse the payload using the standard three-way parse at the top of the function:

   ```python
   try:
       params = json.loads(payload) if payload.strip() else {}
   except json.JSONDecodeError:
       params = {"input": payload}
   ```

4. Import the handler in `src/tool_implementations/__init__.py` and add it to `TOOL_DISPATCH`:

   ```python
   from .my_tool import handle_my_tool

   TOOL_DISPATCH: dict[str, object] = {
       ...
       "MyNewTool": handle_my_tool,
   }
   ```

5. Ensure the tool name exists in `src/reference_data/tools_snapshot.json`. If it does not, add
   an entry so `get_tool` can find it:

   ```json
   {"name": "MyNewTool", "source_hint": "tools/MyNewTool/MyNewTool.tsx",
    "responsibility": "..."}
   ```

The handler will now be called by `execute_tool` whenever `exec-tool MyNewTool <payload>` is run.
