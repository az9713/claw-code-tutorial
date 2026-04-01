# Host Claims Verification Report

Date: 2026-03-31  
Repository verified: `claw-code-main`

## Critical Verification Boundary

This verification is against the **`instructkr/claw-code` repository** (the clean-room Python port that mirrors TypeScript architecture metadata), **not** against the original leaked TypeScript source tree.

All verdicts in this report are scoped to what is implemented or mirrored in this clean-room port repository.

## Scope

This report verifies claims from:

- Matt Berman transcript: `../claude_code_leak_matt_berman/transcript.txt`
- Matt-folder X posts:
  - `../claude_code_leak_matt_berman/alfredversa_X.txt`
  - `../claude_code_leak_matt_berman/mal_shaikX.txt`
- Nate Herk transcript: `../claude_code_leak_nate_herk/transcript.txt`
- Onchain transcript: `../claude_code_leak_onchain/transcript.txt`
- Ray Amjad transcript: `../claude_code_leak_ray_amjad/transcrpt.txt`

## Verification Method

Each claim was checked against:

1. Active Python implementation under `src/`
2. Tests under `tests/`
3. Mirrored archive metadata under `src/reference_data/`

Verdicts:

- **Substantiated**: directly implemented in this repository.
- **Partially substantiated**: present as metadata/placeholder or only partially implemented.
- **Not substantiated**: not present in implementation/metadata evidence sufficient for claim.

## Baseline Context (Important)

This repository is a clean-room Python port/skeleton, not the original leaked TypeScript runtime:

- CLI description: `src/main.py:22`
- Archive root expected at `archive/claude_code_ts_snapshot/src`: `src/context.py:24`
- Archive presence is optional and currently missing in this workspace: `src/context.py:33`
- Mirror snapshot counts: `src/reference_data/archive_surface_snapshot.json`
- Many command/tool entries are mirrored inventory entries, not full implementations:
  - `src/commands.py`
  - `src/tools.py`
  - `src/execution_registry.py`

No personal absolute filesystem paths are intentionally included in this report; file references are repository-relative.

## Matt Folder X Posts: Detailed Verification

## A) `alfredversa_X.txt`

### Claim A1: “Over 2,300 original files are public.”
- Verdict: **Partially substantiated**
- Evidence:
  - This repo’s mirror snapshot reports `total_ts_like_files: 1902`, not 2300.
  - Source: `src/reference_data/archive_surface_snapshot.json`

### Claim A2: “Complete recipe is out: commands, safety checks, system prompts, approvals, hidden features (Undercover, voice, special modes).”
- Verdict: **Partially substantiated**
- What is substantiated:
  - Large command/tool inventory is mirrored:
    - `src/commands.py` (207 entries)
    - `src/tools.py` (184 entries)
  - Hidden-feature *references* exist in snapshots:
    - `voice` subsystem: `src/reference_data/subsystems/voice.json`
    - `coordinator` subsystem: `src/reference_data/subsystems/coordinator.json`
    - `buddy` subsystem: `src/reference_data/subsystems/buddy.json`
- What is not substantiated:
  - No implemented “Undercover Mode” logic found in active Python code.
  - No active full prompt stack/system-prompt execution from leaked TS in this repo.

### Claim A3: “It can be recreated locally and run as a forked local version.”
- Verdict: **Substantiated** (for this repo’s local clean-room port)
- Evidence:
  - Runnable local CLI exists: `src/main.py`
  - Local command/tool shims execute: `src/command_implementations/`, `src/tool_implementations/`
  - Tests validate local execution paths: `tests/test_porting_workspace.py`, `tests/test_tool_implementations.py`

### Claim A4: “Competitors can copy prompts/agent setup/permissions/subagents.”
- Verdict: **Partially substantiated**
- Evidence:
  - Mirrored architecture inventories are present and inspectable.
  - Subagent-related handlers exist in this port:
    - `src/tool_implementations/agent_tools.py`
  - Permission gating exists, but only a simplified deny-list + bash gate in this port:
    - `src/permissions.py`
    - `src/runtime.py` (`_infer_permission_denials`)

### Claim A5: “No model brain leaked; mostly tool/harness internals.”
- Verdict: **Substantiated**
- Evidence:
  - Repository is explicitly a clean-room Python harness port and mirror metadata workspace.
  - No model weights/internals present.

## B) `mal_shaikX.txt`

### Claim B1: “CLAUDE.md is loaded every turn, with hierarchy and 40k chars.”
- Verdict: **Not substantiated**
- Evidence:
  - Active turn processing (`src/query_engine.py`) does not inject/load `CLAUDE.md` each turn.
  - `CLAUDE.md` is only read in `memory` command helper: `src/command_implementations/session_commands.py`.
  - No hierarchy parser (`~/.claude/CLAUDE.md`, `.claude/rules/*.md`, `CLAUDE.local.md`) is implemented.

### Claim B2: “Subagents share prompt cache; three execution models fork/teammate/worktree.”
- Verdict: **Partially substantiated**
- Evidence:
  - Subagent creation exists:
    - `forkSubagent` handler in `src/tool_implementations/agent_tools.py`
    - `spawnMultiAgent` handler in `src/tool_implementations/agent_tools.py`
  - Worktree mode exists only as a toggle flag:
    - `src/tool_implementations/mode_tools.py`
    - `src/stores.py`
  - No implemented prompt-cache sharing logic.
  - Teammate mailbox/tmux behavior appears only as mirrored references (e.g., hooks/state sample files), not active logic.

### Claim B3: “Permission modes: bypass / allowEdits / auto classifier; resolver race.”
- Verdict: **Not substantiated**
- Evidence:
  - Implemented permission model is deny-list and bash-name gating:
    - `src/permissions.py`
    - `src/runtime.py` (`_infer_permission_denials`)
  - No auto-classifier permission resolver logic in active Python runtime.

### Claim B4: “Five compaction strategies, 200k/1m windows, 8KB tool previews.”
- Verdict: **Partially substantiated**
- What is substantiated:
  - Compaction exists in active runtime.
- What is not substantiated:
  - Only simple truncation is implemented:
    - `src/query_engine.py` (`compact_messages_if_needed`)
    - `src/transcript.py` (`compact`)
  - No five-strategy system in active implementation.
  - No 200k/1m context-window enforcement in active implementation.
  - No 8KB preview storage behavior in active implementation.

### Claim B5: “Hooks are extension API with 25+ lifecycle events and 5 hook types.”
- Verdict: **Partially substantiated**
- Evidence:
  - Large hooks subsystem appears in mirrored metadata:
    - `src/reference_data/subsystems/hooks.json` (`module_count: 104`, many sample files)
  - Active Python runtime does not implement full hook execution framework described.

### Claim B6: “Sessions persistent as JSONL with --continue/--resume/--fork-session.”
- Verdict: **Partially substantiated**
- Evidence:
  - Persistence exists but as JSON files in `.port_sessions`:
    - `src/session_store.py`
  - Load session CLI exists:
    - `src/main.py` (`load-session`)
  - Claimed JSONL location and flags (`--continue`, `--resume`, `--fork-session`) are not implemented in this port.

### Claim B7: “60+ tools with concurrent read + serialized writes; MCP deferred loading; ToolSearch.”
- Verdict: **Partially substantiated**
- Evidence:
  - Tools inventory is large (184 mirrored entries): `src/tools.py`
  - `ToolSearchTool` handler exists: `src/tool_implementations/tool_search_tool.py`
  - MCP include/exclude filtering exists:
    - `src/tools.py` (`include_mcp`)
  - Claimed concurrent-vs-serialized scheduler is not explicitly implemented in active tool execution loop.

### Claim B8: “Streaming async generators; interruption cheap.”
- Verdict: **Partially substantiated**
- Evidence:
  - Event-stream generator exists with typed events:
    - `src/query_engine.py` (`stream_submit_message`)
  - Explicit interactive Escape-interrupt semantics are not implemented in this CLI.

### Claim B9: “Advanced retry system (exponential backoff, OAuth refresh, model fallback, watchdog).”
- Verdict: **Not substantiated**
- Evidence:
  - No such retry subsystem found in active implementation.

## Other Hosts (Transcript Claims) Verification Summary

### Matt Berman transcript
- **Substantiated/Partial**: architecture/harness focus, sessions, streaming, subagent references.
- **Not substantiated**: detailed permission classifier modes, full compaction taxonomy, exact 66-tool behavior as active runtime.

### Nate Herk transcript
- **Partially substantiated**: coordinator/buddy appear in mirrored metadata.
- **Not substantiated**: autoDream pipeline, LLM memory retrieval engine, undercover mode, capybara runtime behavior.

### Onchain transcript
- Same pattern as Nate:
  - **Partially substantiated** via mirrored metadata references.
  - **Not substantiated** as active Python implementation for core advanced claims.

### Ray Amjad transcript
- **Partially substantiated**: coordinator/buddy/team-memory references in mirrored metadata.
- **Not substantiated**: proactive mode, background skill self-improvement, away summary, deep token budgets, ultra plan cloud runtime, settings sync, background-session manager commands, reversible context-collapse implementation.

## Unified Markdown Matrix

| Host | Source | Claim | Verdict | Evidence |
|---|---|---|---|---|
| Matt | transcript | `CLAUDE.md` loaded every turn | Not substantiated | `src/query_engine.py`, `src/command_implementations/session_commands.py` |
| Matt | transcript | parallel subagent architecture | Partially substantiated | `src/tool_implementations/agent_tools.py`, `src/tool_implementations/mode_tools.py` |
| Matt | transcript | permission auto/smart modes | Not substantiated | `src/permissions.py`, `src/runtime.py` |
| Matt | transcript | compaction is core system | Partially substantiated | `src/query_engine.py`, `src/transcript.py` |
| Matt | transcript | session persistence/resume | Partially substantiated | `src/session_store.py`, `src/main.py` |
| Matt | transcript | 66 tools, read/write partition | Partially substantiated | `src/tools.py`, `src/tool_implementations/__init__.py` |
| Matt | transcript | streaming event architecture | Partially substantiated | `src/query_engine.py` |
| Matt | alfredversa_X | 2300+ files | Partially substantiated | `src/reference_data/archive_surface_snapshot.json` (1902 TS-like files) |
| Matt | alfredversa_X | full recipe incl hidden features | Partially substantiated | `src/reference_data/subsystems/*.json`, placeholder modules |
| Matt | alfredversa_X | can run local recreated/forked version | Substantiated | `src/main.py`, tests under `tests/` |
| Matt | alfredversa_X | model internals not leaked | Substantiated | Clean-room harness structure; no model internals in repo |
| Matt | mal_shaikX | `CLAUDE.md` hierarchy + per-turn load + 40k | Not substantiated | `src/query_engine.py`, `src/command_implementations/session_commands.py` |
| Matt | mal_shaikX | prompt-cache-shared subagents | Partially substantiated | subagent handlers exist; no explicit cache sharing implementation |
| Matt | mal_shaikX | 3 permission modes + resolver race | Not substantiated | `src/permissions.py`, `src/runtime.py` |
| Matt | mal_shaikX | 5 compaction strategies + 200k/1m + 8KB previews | Partially substantiated | only truncation compaction implemented |
| Matt | mal_shaikX | 25+ hook lifecycle engine | Partially substantiated | hooks mirrored metadata: `src/reference_data/subsystems/hooks.json` |
| Matt | mal_shaikX | JSONL sessions + continue/resume/fork-session | Partially substantiated | JSON `.port_sessions` + `load-session`, not claimed CLI flags |
| Matt | mal_shaikX | advanced retry/fallback/watchdog system | Not substantiated | no retry engine found in active implementation |
| Nate | transcript | autoDream memory consolidation | Not substantiated | no active autodream implementation |
| Nate | transcript | LLM-based memory retrieval side-query | Not substantiated | no active retrieval orchestrator in `src` |
| Nate | transcript | undercover mode | Not substantiated | no undercover mode implementation found |
| Nate | transcript | coordinator 4-phase orchestration | Partially substantiated | `src/reference_data/subsystems/coordinator.json`, placeholder package |
| Nate | transcript | buddy deterministic companion | Partially substantiated | `src/reference_data/subsystems/buddy.json`, placeholder package |
| Onchain | transcript | autoDream / LLM retrieval / undercover | Not substantiated | no active implementations found |
| Onchain | transcript | coordinator / buddy | Partially substantiated | mirrored metadata only |
| Ray | transcript | proactive mode / away summary / background self-improvement | Not substantiated | no active implementations found |
| Ray | transcript | coordinator + verification agent | Partially substantiated | metadata references; limited active orchestration |
| Ray | transcript | deep token budgets | Not substantiated | `src/query_engine.py` (`max_budget_tokens=2000`) |
| Ray | transcript | ultra plan / BYOC / settings sync / presentation mode | Not substantiated | no active implementations found |
| Ray | transcript | team memory / context collapse | Partially substantiated (metadata), Not substantiated (active runtime) | `src/reference_data/subsystems/memdir.json`; no active logic |

## Final Assessment

1. The codebase strongly supports claims about being an architecture mirror and local harness skeleton.
2. Many high-visibility leak claims are represented only as mirrored metadata references, not active Python features.
3. For Matt-folder X posts specifically:
   - Some high-level framing claims are supported (local runnable skeleton, harness-level architecture exposure).
   - Most deep behavioral claims (per-turn CLAUDE.md injection, full permission classifier stack, advanced retry system, multi-strategy compaction internals) are **not substantiated in this repository's active implementation**.
4. Verification boundary reiterated: these findings are about the **clean-room `instructkr/claw-code` port** only, not definitive adjudication of the original leaked TypeScript codebase.
