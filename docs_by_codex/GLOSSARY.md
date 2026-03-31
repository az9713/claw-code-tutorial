# Glossary

- **Archive**: Local ignored TypeScript snapshot expected at `archive/claude_code_ts_snapshot/src`. Presence is detected by `PortContext.archive_available`.
- **Mirrored command/tool entry**: Metadata record loaded from JSON snapshots pointing at the original TypeScript `source_hint`. Python shim executes a placeholder message, not the real logic.
- **Port manifest** (`PortManifest`): Live introspection of Python workspace — file counts, top-level module list.
- **Porting workspace**: This Python repository as a whole — the active reimplementation effort.
- **Parity audit** (`ParityAuditResult`): Coverage comparison between Python workspace and archived surface, based on `ARCHIVE_ROOT_FILES` and `ARCHIVE_DIR_MAPPINGS` mappings in `parity_audit.py`.
- **Reference data**: JSON files in `src/reference_data/` — the command/tool inventories and subsystem metadata.
- **Root-level mirror file**: A Python file in `src/` that maps to a root TypeScript file in the archive (e.g. `QueryEngine.py` mirrors `QueryEngine.ts`). Tracked in `ARCHIVE_ROOT_FILES`.
- **Runtime session** (`RuntimeSession`): Aggregated report object produced by `PortRuntime.bootstrap_session` — includes context, setup, routed matches, execution results, and session path.
- **Subsystem**: One of the 30 `src/` packages corresponding to top-level directories in the original TypeScript codebase.
- **Turn result** (`TurnResult`): Output and accounting record produced by `QueryEnginePort.submit_message`. Contains matched commands/tools, permission denials, usage, and stop reason.
- **Transcript store** (`TranscriptStore`): In-memory list of submitted prompts with compaction (sliding window) and flush (persist marker) semantics.
- **Structured output mode**: When `QueryEngineConfig.structured_output=True`, turn output is a JSON object `{"summary": [...], "session_id": "..."}` instead of plain text.
- **Trusted mode**: `run_setup(trusted=True)` enables all four deferred-init subsystems: plugin_init, skill_init, mcp_prefetch, session_hooks. Always `True` via `PortRuntime`.
- **Tool permission context** (`ToolPermissionContext`): Deny-name and deny-prefix policy object for filtering the tool pool before routing.
- **Stop reason**: Field on `TurnResult` — `"completed"`, `"max_turns_reached"`, or `"max_budget_reached"`.
- **Simple mode**: Tool pool restricted to `BashTool`, `FileReadTool`, `FileEditTool` only.
- **Deferred init** (`DeferredInitResult`): Result of trust-gated subsystem initialisation — four boolean flags: plugin_init, skill_init, mcp_prefetch, session_hooks.
