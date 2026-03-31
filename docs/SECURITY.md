# Security Policy

---

## Supported Versions

This project is at an early stage (v0.1.x). Security fixes are applied to the `main` branch only.

---

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report vulnerabilities by emailing the maintainer via the contact information on the [instructkr GitHub profile](https://github.com/instructkr). Include:

1. A description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Any suggested mitigation

You can expect an acknowledgement within 72 hours. We will work with you to understand the issue and coordinate a fix before any public disclosure.

---

## Permission System

### Tool Deny-Lists

Tool access is controlled by `ToolPermissionContext` (`src/permissions.py`). It maintains two deny structures:

- **`deny_names`** — exact tool names to block (`frozenset[str]`, case-insensitive)
- **`deny_prefixes`** — name prefixes to block (`tuple[str, ...]`, case-insensitive)

These can be set via the CLI (`--deny-tool`, `--deny-prefix`) or programmatically via `ToolPermissionContext.from_iterables()`.

### Automatic Bash Tool Gating

`PortRuntime._infer_permission_denials()` automatically generates a `PermissionDenial` for any tool whose name contains `"bash"` (case-insensitive). This gating is unconditional during `bootstrap_session()` and `run_turn_loop()` and cannot be disabled via configuration flags.

Reason: Bash-named tools represent destructive shell execution capabilities. In this Python port, they are placeholders with shim implementations, but the gating exists to mirror the original harness's safety model.

### Permission Denials are Tracked

All permission denials are recorded in `QueryEnginePort.permission_denials` and included in `TurnResult.permission_denials` so they are visible in session output and Markdown reports.

---

## Trust-Gated Deferred Initialisation

`run_deferred_init(trusted: bool)` (`src/deferred_init.py`) controls four subsystems that are only enabled in trusted contexts:

| Subsystem | Risk when enabled |
|-----------|------------------|
| `plugin_init` | Plugins may execute arbitrary code |
| `skill_init` | Skills may invoke external tools |
| `mcp_prefetch` | MCP connections contact external servers |
| `session_hooks` | Hooks run on lifecycle events |

`PortRuntime.bootstrap_session()` passes `trusted=True`. When building integrations that receive prompts from untrusted sources, consider calling `run_deferred_init(trusted=False)` and constructing the session manually.

---

## Session Data Handling

Sessions are stored as plain JSON files in `.port_sessions/` relative to the working directory:

```
.port_sessions/<uuid>.json
```

Each file contains the session ID, message history (submitted prompts only), and token counts. No API keys, credentials, or user-identifiable data are written by the Python port.

**Recommendations:**

- Add `.port_sessions/` to your `.gitignore` (it is already ignored in this repository).
- Delete stale session files when they are no longer needed.
- If running in a multi-user environment, ensure `.port_sessions/` has appropriate filesystem permissions (e.g. `chmod 700`).

---

## No Network Communication

This Python port makes **no outbound network connections**. The prefetch stubs (`src/prefetch.py`) simulate MDM reads and keychain prefetch locally and do not contact external services.

If the Rust port or future versions introduce network features, this section will be updated.

---

## Dependency Surface

The project has zero external dependencies — only the Python standard library. There is no `pip` dependency tree to audit for transitive vulnerabilities.

---

## Clean-Room Implementation Notice

This codebase is a clean-room Python rewrite. It does not contain any Anthropic proprietary source code. Security researchers should be aware that this is a structural mirror, not an operational clone of the original Claude Code system. Vulnerabilities in the original Claude Code product should be reported directly to Anthropic via their responsible disclosure programme.
