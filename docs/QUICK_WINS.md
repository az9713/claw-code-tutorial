# Quick Wins: Get Up and Running Fast

Five minutes to your first result. Fifteen minutes to feeling at home.

---

## Setup (Everyone Starts Here)

### 1. Check Python

You need **Python 3.10 or later**. No other dependencies and nothing to install via pip.

```bash
python3 --version
# Must print 3.10.x or higher
```

On Windows, `python` (without the `3`) may work instead:

```bash
python --version
```

If you get `command not found`, install Python from [python.org](https://python.org/downloads) and reopen your terminal.

---

### 2. Clone the Repository

```bash
git clone https://github.com/az9713/claw-code-tutorial.git
cd claw-code-tutorial
```

No virtual environment is required. The project uses only the Python standard library.

---

### 3. Verify Everything Works

```bash
python3 -m src.main summary
```

If this prints a `# Python Porting Workspace Summary` section, your setup is good.

---

### 4. Run the Test Suite (Optional but Reassuring)

```bash
python3 -m unittest discover -s tests -v
```

Expected shape:

```text
----------------------------------------------------------------------
Ran ... tests in ~...s

OK
```

Why this changed: exact test counts and runtime vary over time, and some locked-down environments (especially Windows temp/cache restrictions) may raise `PermissionError` failures unrelated to core logic.

---

### 5. Health Check

```bash
python3 -m src.main exec-command doctor noop
```

Expected shape:

```text
claw-code doctor report

  [PASS] Python >= 3.10: ...
  [PASS] tools_snapshot.json: ...
  [PASS] commands_snapshot.json: ...
  [PASS] stores accessible: ok

Overall: OK
```

Why this changed: `exec-command` requires a non-empty positional `prompt` argument.

---

## Track A - Python Developer / Harness Engineer

### A1. See the Routing Algorithm in Action

```bash
python3 -m src.main route "read a file"
```

Each row is `kind | name | score | source_hint`.

Try more prompts:

```bash
python3 -m src.main route "run a shell command"
python3 -m src.main route "create a task and assign it"
python3 -m src.main route "search for text in files"
```

---

### A2. Stream a Full Session and Inspect Event Types

```python
from src.query_engine import QueryEnginePort

engine = QueryEnginePort.from_workspace()

for event in engine.stream_submit_message(
    "search for python files",
    matched_commands=("files",),
    matched_tools=("GrepTool",),
):
    print(event["type"], "->", str(event)[:90])
```

Typical event sequence:

```text
message_start
command_match
tool_match
message_delta
message_stop
```

Optional event: `permission_denial` appears only when denied tools are supplied.

Why this changed: the original wording said "all six events" even though one event is conditional.

---

### A3. Run a Multi-Turn Loop and Inspect Stop Reasons

CLI:

```bash
python3 -m src.main turn-loop "analyse the codebase" --max-turns 3 --structured-output
```

Why this changed: positional `prompt` must come before options in this parser.

Python:

```python
from src.runtime import PortRuntime

results = PortRuntime().run_turn_loop("analyse the codebase", max_turns=3)
for i, turn in enumerate(results, start=1):
    print(f"Turn {i}: stop_reason={turn.stop_reason}, input_tokens={turn.usage.input_tokens}")
```

---

### A4. Add Your Own Tool Handler in 5 Lines

In `src/tool_implementations/__init__.py`:

```python
def handle_my_tool(payload: str) -> str:
    import json
    params = json.loads(payload) if payload.strip() else {}
    return f"MyTool received: {params}"

TOOL_DISPATCH["MyTool"] = handle_my_tool
```

Run it from Python:

```python
import json
from src.tool_implementations import dispatch_tool

print(dispatch_tool("MyTool", json.dumps({"hello": "world"})))
# -> MyTool received: {'hello': 'world'}
```

Why this changed: `python -m src.main exec-tool MyTool ...` does not work from dispatcher-only registration because CLI tool execution first validates against mirrored tool inventory.

---

### A5. Audit Coverage with Parity Audit

```bash
python3 -m src.main parity-audit
```

Without the local TypeScript archive, expected output includes:

```text
# Parity Audit
Local archive unavailable; parity audit cannot compare against the original snapshot.
```

---

## Track B - Curious Developer

Note: JSON quoting in `exec-tool` CLI calls is shell-sensitive (especially on PowerShell). To make examples reliable across shells, use `python -c` plus `json.dumps(...)`.

### B1. Execute a Real Shell Command

```bash
python -c "from src.tools import execute_tool; import json; print(execute_tool('BashTool', json.dumps({'command':'echo hello world'})).message)"
```

Try more:

```bash
python -c "from src.tools import execute_tool; import json; print(execute_tool('BashTool', json.dumps({'command':'python --version'})).message)"
python -c "from src.tools import execute_tool; import json; print(execute_tool('BashTool', json.dumps({'command':'dir src'})).message)"
python -c "from src.tools import execute_tool; import json; print(execute_tool('BashTool', json.dumps({'command':'git log --oneline -5'})).message)"
```

Blocklist demo:

```bash
python -c "from src.tools import execute_tool; import json; print(execute_tool('BashTool', json.dumps({'command':'rm -rf /'})).message)"
```

---

### B2. Read Any File with Line Numbers

```bash
python -c "from src.tools import execute_tool; import json; print(execute_tool('FileReadTool', json.dumps({'file_path':'README.md','limit':10})).message)"
```

With offset:

```bash
python -c "from src.tools import execute_tool; import json; print(execute_tool('FileReadTool', json.dumps({'file_path':'src/runtime.py','offset':50,'limit':20})).message)"
```

---

### B3. Create and Manage Tasks

Create:

```bash
python -c "from src.tools import execute_tool; import json; print(execute_tool('TaskCreateTool', json.dumps({'name':'my first task','description':'testing quick wins'})).message)"
```

Update / output / stop (replace `<task-id>`):

```bash
python -c "from src.tools import execute_tool; import json; print(execute_tool('TaskUpdateTool', json.dumps({'task_id':'<task-id>','status':'in_progress'})).message)"
python -c "from src.tools import execute_tool; import json; print(execute_tool('TaskOutputTool', json.dumps({'task_id':'<task-id>','output':'Completed analysis.'})).message)"
python -c "from src.tools import execute_tool; import json; print(execute_tool('TaskStopTool', json.dumps({'task_id':'<task-id>'})).message)"
```

Note: tasks are in-memory and reset when process state resets.

---

### B4. Spawn a Team of Agents

```bash
python -c "from src.tools import execute_tool; import json; print(execute_tool('spawnMultiAgent', json.dumps({'agents':[{'prompt':'explore the codebase'},{'prompt':'write a test plan'}]})).message)"
```

---

### B5. Fetch a Live Web Page

```bash
python -c "from src.tools import execute_tool; import json; print(execute_tool('WebFetchTool', json.dumps({'url':'https://example.com'})).message[:500])"
```

---

## Track C - Student / Researcher

### C1. Trace the 7-Stage Bootstrap Lifecycle

```bash
python3 -m src.main bootstrap "search for python files"
python3 -m src.main bootstrap-graph
```

---

### C2. Browse the Full Tool and Command Surface

```bash
python3 -m src.main tools --limit 20
python3 -m src.main tools --query agent
python3 -m src.main tools --query task
python3 -m src.main tools --query mcp
python3 -m src.main commands --query review
python3 -m src.main commands --query session
python3 -m src.main show-tool AgentTool
python3 -m src.main show-tool BashTool
python3 -m src.main show-command compact
```

---

### C3. Study the Command Graph

```bash
python3 -m src.main command-graph
python3 -m src.main tool-pool
```

---

### C4. Read a Session File Directly

Create one:

```bash
python3 -m src.main bootstrap "study the session format"
```

List and read (cross-platform):

```bash
python -c "from pathlib import Path; print('\n'.join(str(p) for p in Path('.port_sessions').glob('*.json')))"
python -c "from pathlib import Path; print(Path('.port_sessions/<session-id>.json').read_text(encoding='utf-8'))"
```

Reload from CLI:

```bash
python3 -m src.main load-session <session-id>
```

---

### C5. Measure Real Parity Against the TypeScript Surface

```bash
python3 -m src.main parity-audit
```

Without the archive, expected output includes:

```text
# Parity Audit
Local archive unavailable; parity audit cannot compare against the original snapshot.
```

---

## What's Next

| If you want to... | Go to... |
|-------------------|----------|
| Understand the full architecture | [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) |
| See every public API | [`docs/API_REFERENCE.md`](API_REFERENCE.md) |
| Add your own tool | [`docs/DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) |
| See tool payload shapes | [`docs/TOOL_IMPLEMENTATIONS.md`](TOOL_IMPLEMENTATIONS.md) |
| Study all CLI subcommands | [`docs/CLI_REFERENCE.md`](CLI_REFERENCE.md) |
| Deep-dive into agent architecture | [`docs/AGENTS.md`](AGENTS.md) |
| Follow a structured learning path | [`docs/STUDY_PLAN.md`](STUDY_PLAN.md) |
