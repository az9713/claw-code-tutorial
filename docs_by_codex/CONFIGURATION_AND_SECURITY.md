# Configuration and Security

## Runtime Configuration Surface

There is no centralized config file yet; configuration is mostly argument-driven and constructor-driven.

## `QueryEngineConfig` Controls

Configured in `src/query_engine.py`:

- `max_turns` (default `8`)
- `max_budget_tokens` (default `2000`)
- `compact_after_turns` (default `12`)
- `structured_output` (default `False`)
- `structured_retry_limit` (default `2`)

## CLI-Level Filters

`tools` subcommand options:

- `--simple-mode`
- `--no-mcp`
- `--deny-tool <name>`
- `--deny-prefix <prefix>`

These map to `ToolPermissionContext` deny-name and deny-prefix checks.

## Trusted Initialization

`run_setup(trusted=True)` gates deferred init toggles:

- plugin init
- skill init
- mcp prefetch
- session hooks

Current implementation is simulated and sets booleans, but the trust boundary is explicitly modeled.

## Persistence and Data Handling

- Session persistence location: `.port_sessions/*.json`
- Stored data:
  - `session_id`
  - user prompts/messages
  - input/output token counters (word-based approximations)
- No encryption at rest by default
- No automatic PII redaction

## Security Posture (Current)

Implemented:

- Explicit deny filter primitive for tools
- Runtime inference that gates bash-like tool names in route results

Not implemented yet:

- Role-based access control
- Signature/integrity validation for snapshot JSON files
- Cryptographic session storage
- Structured secret management integration

## Security Recommendations for Next Iteration

1. Add hash/signature verification for `reference_data` snapshots.
2. Add session encryption option and configurable storage root.
3. Add allowlist mode to `ToolPermissionContext`.
4. Add audit logging for denied tool decisions.
5. Add schema versioning for persisted session payloads.
