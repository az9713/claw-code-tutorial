# Quick Wins: Get Up and Running Fast

Five minutes to your first result. Fifteen minutes to feeling at home.

---

## Setup (Everyone Starts Here)

### 1. Check Python

You need **Python 3.10 or later**. No other dependencies — nothing to install via pip.

```bash
python3 --version
# Must print 3.10.x or higher
```

On Windows, `python` (without the `3`) may work instead:

```bash
python --version
```

If you get `command not found`, download Python from [python.org](https://python.org/downloads) and re-open your terminal.

---

### 2. Clone the Repository

```bash
git clone https://github.com/az9713/claw-code-tutorial.git
cd claw-code-tutorial
```

No virtual environment needed. No `pip install`. The project uses only the Python standard library.

---

### 3. Verify Everything Works

Run the workspace summary:

```bash
python3 -m src.main summary
```

You should see:

```
# Python Porting Workspace Summary

Port root: .../src
Total Python files: 89

Command surface: 207 mirrored entries
Tool surface: 184 mirrored entries
...
```

If you see this, you're ready. If you see a `ModuleNotFoundError`, make sure you're running the command from inside the `claw-code-tutorial/` directory.

---

### 4. Run the Test Suite (Optional but Reassuring)

```bash
python3 -m unittest discover -s tests -v
```

Expected output ends with:

```
----------------------------------------------------------------------
Ran 134 tests in ~6s

OK
```

All 134 tests should pass. If any fail, open an issue on GitHub.

---

### 5. Health Check

```bash
python3 -m src.main exec-command doctor ''
```

Expected:

```
claw-code doctor report

  [PASS] Python >= 3.10: 3.13.5
  [PASS] tools_snapshot.json: .../src/reference_data/tools_snapshot.json
  [PASS] commands_snapshot.json: .../src/reference_data/commands_snapshot.json
  [PASS] stores accessible: ok

Overall: OK
```

All four checks green? You're fully set up. Pick your track below.

---

## Track A — Python Developer / Harness Engineer

*"I want to understand the internals."*

These five wins walk you through the core runtime layer — routing, streaming, multi-turn loops, extending the system, and measuring coverage.

---

### A1. See the Routing Algorithm in Action

The runtime scores every prompt against 207 commands and 184 tools using token overlap. Try it:

```bash
python3 -m src.main route "read a file"
```

Output:

```
command    files        2    commands/files/files.ts
tool       FileReadTool 3    tools/FileReadTool/FileReadTool.ts
tool       UI           3    tools/FileReadTool/UI.tsx
...
```

Each row is `kind | name | score | source_hint`. The score is the number of shared tokens between your prompt and the module's name + responsibility. Change the prompt and see the rankings shift:

```bash
python3 -m src.main route "run a shell command"
python3 -m src.main route "create a task and assign it"
python3 -m src.main route "search for text in files"
```

The routing logic lives in `src/runtime.py` → `route_prompt()`. Read it — it's 30 lines of pure Python.

---

### A2. Stream a Full Session and Handle All 6 Events

The streaming API yields events one at a time. Try it in Python:

```python
from src.query_engine import QueryEnginePort

engine = QueryEnginePort.from_workspace()

for event in engine.stream_submit_message(
    "search for python files",
    matched_commands=("files",),
    matched_tools=("GrepTool",),
):
    print(event["type"], "→", str(event)[:80])
```

You'll see all six event types in sequence:

```
message_start   → {'type': 'message_start', 'session_id': '...', 'prompt': '...'}
command_match   → {'type': 'command_match', 'commands': ('files',)}
tool_match      → {'type': 'tool_match', 'tools': ('GrepTool',)}
message_delta   → {'type': 'message_delta', 'text': '...'}
message_stop    → {'type': 'message_stop', 'usage': {...}, 'stop_reason': 'completed'}
```

The full streaming implementation is in `src/query_engine.py` → `stream_submit_message()`.

---

### A3. Run a Multi-Turn Loop and Inspect Stop Reasons

The turn loop runs multiple rounds on the same engine until budget or turn limit is hit:

```bash
python3 -m src.main turn-loop --max-turns 3 --structured-output "analyse the codebase"
```

Or from Python:

```python
from src.runtime import PortRuntime

results = PortRuntime().run_turn_loop("analyse the codebase", max_turns=3)

for i, turn in enumerate(results):
    print(f"Turn {i+1}: stop_reason={turn.stop_reason}, tokens={turn.usage.input_tokens}")
```

Each `TurnResult` has: `prompt`, `output`, `matched_commands`, `matched_tools`, `usage`, and `stop_reason` — one of `completed`, `max_turns_reached`, or `max_budget_reached`.

Experiment: lower the budget to force early termination:

```python
from src.query_engine import QueryEnginePort, QueryEngineConfig

engine = QueryEnginePort.from_workspace()
engine.config = QueryEngineConfig(max_budget_tokens=10)  # tiny budget
result = engine.submit_message("do something complex")
print(result.stop_reason)  # → max_budget_reached
```

---

### A4. Add Your Own Tool Handler in 5 Lines

The entire dispatcher is a plain dict. Open `src/tool_implementations/__init__.py` and add your handler:

```python
# In src/tool_implementations/__init__.py

def handle_my_tool(payload: str) -> str:
    import json
    params = json.loads(payload) if payload.strip() else {}
    return f"MyTool received: {params}"

TOOL_DISPATCH["MyTool"] = handle_my_tool
```

Now call it:

```bash
python3 -m src.main exec-tool MyTool '{"hello": "world"}'
# → MyTool received: {'hello': 'world'}
```

That's the entire extension model. For a proper implementation, create a new file in `src/tool_implementations/`, write your handler there, and import it into `__init__.py`. See `docs/DEVELOPER_GUIDE.md` for the full pattern.

---

### A5. Audit Coverage with Parity Audit

The parity audit compares what's ported against the full 1,902-file TypeScript surface:

```bash
python3 -m src.main parity-audit
```

Output (without the archive):

```
# Parity Audit
Local archive unavailable; parity audit cannot compare against the original snapshot.
```

The archive is the original TypeScript source — it's not included in the repo. Without it, the audit reports that no comparison can be made. The audit logic is in `src/parity_audit.py`, and the mappings it would check are in `ARCHIVE_ROOT_FILES` (18 entries) and `ARCHIVE_DIR_MAPPINGS` (33 entries). These lists show exactly which Python modules mirror which TypeScript directories — useful even without the archive present.

---

## Track B — Curious Developer

*"Show me something cool in under 5 minutes."*

These five wins each take under 60 seconds and produce immediate, tangible output.

---

### B1. Execute a Real Shell Command

```bash
python3 -m src.main exec-tool BashTool '{"command": "echo hello world"}'
```

Output:

```
hello world
```

Try something more interesting:

```bash
python3 -m src.main exec-tool BashTool '{"command": "python3 --version"}'
python3 -m src.main exec-tool BashTool '{"command": "ls src/"}'
python3 -m src.main exec-tool BashTool '{"command": "git log --oneline -5"}'
```

The tool runs real subprocesses via `subprocess.run`. It has a built-in security blocklist — try this to see it in action:

```bash
python3 -m src.main exec-tool BashTool '{"command": "rm -rf /"}'
# → Security warning: command blocked
```

---

### B2. Read Any File with Line Numbers

```bash
python3 -m src.main exec-tool FileReadTool '{"file_path": "README.md", "limit": 10}'
```

Output:

```
1	# Rewriting Project Claw Code
2
3	...
```

Every line is prefixed with its line number (tab-separated, like `cat -n`). Use `offset` to jump into large files:

```bash
python3 -m src.main exec-tool FileReadTool '{"file_path": "src/runtime.py", "offset": 50, "limit": 20}'
```

---

### B3. Create and Manage Tasks

Create a task:

```bash
python3 -m src.main exec-tool TaskCreateTool '{"name": "my first task", "description": "testing quick wins"}'
```

Output:

```json
{
  "task_id": "235fe59361ab",
  "name": "my first task",
  "description": "testing quick wins",
  "status": "pending",
  "output": ""
}
```

Update its status, record output, then stop it:

```bash
python3 -m src.main exec-tool TaskUpdateTool '{"task_id": "235fe59361ab", "status": "in_progress"}'
python3 -m src.main exec-tool TaskOutputTool '{"task_id": "235fe59361ab", "output": "Completed analysis."}'
python3 -m src.main exec-tool TaskStopTool '{"task_id": "235fe59361ab"}'
```

> **Note:** Tasks live in-memory. They reset when the process exits. To use tasks across multiple CLI calls, use the Python API in a single script.

---

### B4. Spawn a Team of Agents

```bash
python3 -m src.main exec-tool spawnMultiAgent '{"agents": [{"prompt": "explore the codebase"}, {"prompt": "write a test plan"}]}'
```

Output:

```json
{
  "spawned": 2,
  "agent_ids": ["ae5af4212595", "b0f221dd788d"],
  "agents": [
    {"agent_id": "ae5af4212595", "prompt": "explore the codebase", "status": "running"},
    {"agent_id": "b0f221dd788d", "prompt": "write a test plan", "status": "running"}
  ]
}
```

Each agent gets a unique ID. Spin up as many as you like. (In this port, agents record intent in-memory — they don't make real LLM calls yet. Extending them to do so is a natural next contribution.)

---

### B5. Fetch a Live Web Page

```bash
python3 -m src.main exec-tool WebFetchTool '{"url": "https://example.com"}'
```

Returns the raw HTML of the page (truncated to 100KB). The tool uses Python's built-in `urllib` — no external HTTP libraries needed.

---

## Track C — Student / Researcher

*"I'm studying how Claude Code works."*

These five wins give you direct insight into Claude Code's architecture — its command surface, bootstrap lifecycle, session model, and parity with the TypeScript original.

---

### C1. Trace the 7-Stage Bootstrap Lifecycle

Every Claude Code session goes through seven stages: prefetch → warning handler → trust gate → setup + parallel load → deferred init → mode routing → query engine loop.

Watch it happen:

```bash
python3 -m src.main bootstrap "search for python files"
```

The output shows every stage result, routed matches, tool execution messages, session ID, and turn result. Cross-reference this with `src/bootstrap_graph.py` (the stage definitions) and `src/runtime.py` → `bootstrap_session()` (the orchestrator).

For a structured view of the stages alone:

```bash
python3 -m src.main bootstrap-graph
```

---

### C2. Browse the Full Tool and Command Surface

Claude Code exposes 207 commands and 184 tools. Browse them:

```bash
# All tools, 20 at a time
python3 -m src.main tools --limit 20

# Search by keyword
python3 -m src.main tools --query agent
python3 -m src.main tools --query task
python3 -m src.main tools --query mcp

# Commands
python3 -m src.main commands --query review
python3 -m src.main commands --query session
```

Each entry shows its TypeScript `source_hint` — the original file path in the Claude Code repo. This is the map of the entire system.

Inspect a specific tool:

```bash
python3 -m src.main show-tool AgentTool
python3 -m src.main show-tool BashTool
python3 -m src.main show-command compact
```

---

### C3. Study the Command Graph

Claude Code's 207 commands are categorised into builtins, plugin-like, and skill-like groups:

```bash
python3 -m src.main command-graph
```

Output:

```
# Command Graph

Builtins: 185
Plugin-like commands: 20
Skill-like commands: 2
```

The categorisation is based on `source_hint` substrings — commands whose path contains `plugin` are plugin-like; those containing `skills` are skill-like; everything else is a builtin. See `src/command_graph.py` → `build_command_graph()`.

Compare with the tool pool:

```bash
python3 -m src.main tool-pool
```

This shows all 184 tools with their TypeScript `source_hint` paths.

---

### C4. Read a Session File Directly

Run a bootstrap to create a session:

```bash
python3 -m src.main bootstrap "study the session format"
```

The session ID is printed in the output. Then look at the raw JSON:

```bash
ls .port_sessions/
cat .port_sessions/<session-id>.json
```

The file contains: `session_id`, `messages`, `input_tokens`, `output_tokens`. This is `StoredSession` — defined in `src/session_store.py`. Reload it via CLI:

```bash
python3 -m src.main load-session <session-id>
```

Or from Python:

```python
from src.session_store import load_session
session = load_session("<session-id>")
print(session.messages)
```

---

### C5. Measure Real Parity Against the TypeScript Surface

The parity audit tells you exactly how much of the original Claude Code has been ported:

```bash
python3 -m src.main parity-audit
```

Without the TypeScript archive present, you'll see:

```
# Parity Audit
Local archive unavailable; parity audit cannot compare against the original snapshot.
```

The archive (original TypeScript Claude Code) is not included in the repo. The audit requires it to perform a file-by-file comparison. Even without it, you can study `src/parity_audit.py` directly:

- `ARCHIVE_ROOT_FILES` — 18 mappings from TypeScript root-level files to Python mirrors
- `ARCHIVE_DIR_MAPPINGS` — 33 mappings from TypeScript subsystem directories to Python packages

These lists are the definitive map of what was ported and what remains. Read them to understand the scope of the original system and where the gaps are.

---

## What's Next

| If you want to… | Go to… |
|----------------|--------|
| Understand the full architecture | [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) |
| See every public API | [`docs/API_REFERENCE.md`](API_REFERENCE.md) |
| Add your own tool | [`docs/DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) |
| See what each tool's payload looks like | [`docs/TOOL_IMPLEMENTATIONS.md`](TOOL_IMPLEMENTATIONS.md) |
| Study all 22 CLI subcommands | [`docs/CLI_REFERENCE.md`](CLI_REFERENCE.md) |
| Deep-dive into agent architecture | [`docs/AGENTS.md`](AGENTS.md) |
| Follow a structured learning path | [`docs/STUDY_PLAN.md`](STUDY_PLAN.md) |
