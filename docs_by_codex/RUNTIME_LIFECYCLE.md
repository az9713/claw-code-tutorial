# Runtime Lifecycle

## Bootstrap Lifecycle

`build_bootstrap_graph()` defines the canonical stages:

1. Top-level prefetch side effects
2. Warning handler and environment guards
3. CLI parser and pre-action trust gate
4. `setup()` + commands/agents parallel load
5. Deferred init after trust
6. Mode routing (`local`, `remote`, `ssh`, `teleport`, `direct-connect`, `deep-link`)
7. Query engine submit loop

## Setup Phase

`run_setup()` composes:

- `start_mdm_raw_read()`
- `start_keychain_prefetch()`
- `start_project_scan(root)`
- `run_deferred_init(trusted=<bool>)`

Outputs `SetupReport` with:

- environment fingerprint
- prefetch results
- trusted-mode toggles

## Routing Phase

`PortRuntime.route_prompt()`:

- Tokenizes prompt into lowercase terms.
- Scores command/tool modules against `name`, `source_hint`, `responsibility`.
- Guarantees up to one top command and one top tool in selected set, then fills by score.

## Turn Execution Phase

`QueryEnginePort.submit_message()`:

1. Enforces `max_turns`.
2. Formats output summary (text or JSON structured mode).
3. Updates usage counters (`UsageSummary` word-based approximation).
4. Appends message to transcript store.
5. Compacts transcript/messages if limits exceeded.
6. Emits stop reason (`completed`, `max_budget_reached`, `max_turns_reached`).

`stream_submit_message()` emits structured events:

- `message_start`
- `command_match` (optional)
- `tool_match` (optional)
- `permission_denial` (optional)
- `message_delta`
- `message_stop`

## Session Persistence Phase

`persist_session()`:

- Flushes transcript state
- Saves `.port_sessions/<session_id>.json`
- Stores:
  - `session_id`
  - message tuple
  - input/output token counters

## Runtime Modes

- `remote-mode`, `ssh-mode`, `teleport-mode` currently return placeholder `RuntimeModeReport`.
- `direct-connect-mode`, `deep-link-mode` return placeholder `DirectModeReport`.

These are interface stubs for future transport/runtime integrations.
