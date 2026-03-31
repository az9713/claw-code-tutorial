# Troubleshooting

---

## "No mirrored command/tool matches found."

**Symptom:** `python3 -m src.main route "my prompt"` prints nothing useful.

**Cause:** The token-scoring algorithm matches tokens against command/tool `name`, `source_hint`, and `responsibility`. If none of these contain any of the words in your prompt, no match is found.

**Fix:**
- Use more specific vocabulary from the command/tool registry. For example, `review` matches the `review` command; `MCP` matches `MCPTool`.
- Use `python3 -m src.main commands` or `python3 -m src.main tools` to see what names exist.
- Use `--query` to search: `python3 -m src.main commands --query bash`.

---

## "Unknown mirrored command: X" / "Unknown mirrored tool: X"

**Symptom:** `exec-command` or `exec-tool` prints an error and exits with code 1.

**Cause:** The name is not in the snapshot.

**Fix:** Use `show-command` / `show-tool` to confirm the exact name (case-insensitive lookup):
```bash
python3 -m src.main show-command review
python3 -m src.main show-tool MCPTool
```

---

## "Command not found: X" / "Tool not found: X"

**Symptom:** `show-command` or `show-tool` exits with code 1.

**Cause:** Same as above — the name is not registered.

**Fix:** List available entries and verify spelling:
```bash
python3 -m src.main commands --limit 50
python3 -m src.main tools --limit 50
```

---

## Session not persisting

**Symptom:** A session file is not appearing in `.port_sessions/`.

**Cause candidates:**
1. `persist_session()` was not called. `run_turn_loop()` does NOT persist automatically — call `engine.persist_session()` or use `bootstrap` / `flush-transcript` which do persist.
2. The working directory changed between runs. `.port_sessions/` is created relative to the CWD at the time of the call.

**Fix:**
- Use `flush-transcript` to both submit and persist: `python3 -m src.main flush-transcript "my prompt"`
- Use `bootstrap` to get a full session with automatic persistence: `python3 -m src.main bootstrap "my prompt"`

---

## `load-session` raises / prints nothing

**Symptom:** `python3 -m src.main load-session <id>` fails.

**Cause:** The session file does not exist at `.port_sessions/<id>.json` relative to the current working directory.

**Fix:**
1. Confirm you are running from the same directory as when the session was saved.
2. Confirm the session ID is the filename stem (without `.json`), not the full path.
3. List session files: `ls .port_sessions/` (Linux/macOS) or `dir .port_sessions` (Windows).

---

## `max_turns_reached` stops the loop immediately

**Symptom:** `turn-loop` exits after the first turn with `stop_reason=max_turns_reached`.

**Cause:** The engine already has `max_turns` messages in `mutable_messages` before the new prompt is submitted. This can happen if you reuse an engine instance across multiple calls.

**Fix:** Either increase `--max-turns` or ensure you are using a fresh engine per loop. `run_turn_loop()` creates a new engine internally, so this should not occur via the CLI unless `max_turns` is set to `0` or `1`.

---

## `max_budget_reached` stops the loop early

**Symptom:** The loop stops after the first or second turn with `stop_reason=max_budget_reached`.

**Cause:** The default `max_budget_tokens=2000` is a word-count approximation. Long prompts or large tool inventories can exceed this quickly.

**Fix:** Set a higher budget via the API:
```python
from src.runtime import PortRuntime
from src.query_engine import QueryEngineConfig

engine = PortRuntime()
# use run_turn_loop which creates its own engine, or use QueryEnginePort directly:
from src.query_engine import QueryEnginePort
engine = QueryEnginePort.from_workspace()
engine.config = QueryEngineConfig(max_budget_tokens=10000)
result = engine.submit_message("my long prompt")
```

There is no CLI flag for `max_budget_tokens`.

---

## Python version error

**Symptom:** `SyntaxError` or `TypeError` on startup.

**Cause:** Python 3.9 or earlier. The codebase uses `X | None` union syntax that requires Python 3.10+.

**Fix:** Upgrade to Python 3.10 or later:
```bash
python3 --version   # must be 3.10+
```

---

## Import errors when running tests

**Symptom:** `ModuleNotFoundError: No module named 'src'`

**Cause:** Tests must be run from the repository root, not from inside `src/` or `tests/`.

**Fix:**
```bash
cd /path/to/claw-code   # the repo root, containing src/ and tests/
python3 -m unittest discover -s tests -v
```

---

## Parity audit shows 0 root file coverage

**Symptom:** `parity-audit` reports `root_file_coverage: 0/18`.

**Cause:** The parity audit is run from a different working directory, or `src/` does not have the expected root mirror files.

**Fix:**
1. Run from the repository root.
2. Verify that files like `QueryEngine.py`, `Tool.py`, `query.py` exist in `src/`.
3. If they are missing, check git status — they may have been accidentally deleted.

---

## Tools subcommand shows 0 tools with `--simple-mode --no-mcp`

**Symptom:** Tool count is 3 with `--simple-mode`, but drops to 0 with `--no-mcp` added.

**Cause:** `BashTool`, `FileReadTool`, `FileEditTool` do not contain `"mcp"` in their names, so `--no-mcp` should have no effect. If you are seeing 0 results, check whether additional `--deny-prefix` or `--deny-tool` flags are being passed.

**Fix:** Run without deny filters to confirm:
```bash
python3 -m src.main tools --simple-mode
```

---

## "structured output rendering failed" RuntimeError

**Symptom:** `run_turn_loop` with `--structured-output` raises `RuntimeError`.

**Cause:** JSON serialisation of the turn payload failed twice (the `structured_retry_limit=2` was exhausted). This should not happen with the current implementation since the payload only contains strings, but would occur if `session_id` or `summary` lines were somehow non-serialisable.

**Fix:** This indicates a bug. File an issue with the full traceback.

---

## Debugging the bootstrap process

To inspect each stage of bootstrap without running a full session:

```bash
# What stages does bootstrap run?
python3 -m src.main bootstrap-graph

# What does setup report?
python3 -m src.main setup-report

# What commands and tools are loaded?
python3 -m src.main commands --limit 20
python3 -m src.main tools --limit 20

# How does the prompt get routed?
python3 -m src.main route "your prompt here"

# Full bootstrap trace for a prompt
python3 -m src.main bootstrap "your prompt here"
```

The `bootstrap` output includes: context, setup, startup steps, system init, routed matches, execution results, stream events, turn result, and session history — giving you a complete picture of what happened.
