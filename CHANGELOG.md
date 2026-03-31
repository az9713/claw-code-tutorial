# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### In Progress
- Rust port on the `dev/rust` branch — faster, memory-safe harness runtime.

---

## [0.1.0] — 2026-03-31

Initial public release of the Python porting workspace.

### Added

**Workspace infrastructure**
- `src/` Python porting workspace with 66+ modules
- `src/reference_data/` — JSON snapshots of the original surface (207 commands, 184 tools, 30 subsystems)
- `tests/test_porting_workspace.py` — 20 unit and CLI integration tests

**Core runtime**
- `PortRuntime` — prompt routing, session bootstrap, multi-turn loop
- `QueryEnginePort` — conversation engine with token-budget enforcement, message compaction, streaming events, and structured-output mode
- `BootstrapGraph` — 7-stage startup lifecycle model
- `RuntimeSession` — immutable record of a bootstrapped session

**Inventory**
- 207 mirrored command entries loaded from `commands_snapshot.json`
- 184 mirrored tool entries loaded from `tools_snapshot.json`
- `ExecutionRegistry` — shim wrappers (`MirroredCommand`, `MirroredTool`) for each entry

**Subsystem packages (30)**
- Placeholder packages for: `assistant`, `bootstrap`, `bridge`, `buddy`, `cli`, `components`, `constants`, `coordinator`, `entrypoints`, `hooks`, `keybindings`, `memdir`, `migrations`, `moreright`, `native_ts`, `outputStyles`, `plugins`, `remote`, `schemas`, `screens`, `server`, `services`, `skills`, `state`, `types`, `upstreamproxy`, `utils`, `vim`, `voice`

**Session & transcript**
- JSON-based session persistence to `.port_sessions/`
- `TranscriptStore` with in-memory compaction and flush

**Permission system**
- `ToolPermissionContext` — deny-list by exact name or prefix
- Automatic bash-tool gating in `PortRuntime`

**CLI (22 subcommands)**
- `summary`, `manifest`, `parity-audit`, `setup-report`
- `commands`, `tools`, `show-command`, `show-tool`
- `route`, `bootstrap`, `turn-loop`
- `exec-command`, `exec-tool`
- `flush-transcript`, `load-session`
- `command-graph`, `tool-pool`, `bootstrap-graph`
- `remote-mode`, `ssh-mode`, `teleport-mode`, `direct-connect-mode`, `deep-link-mode`

**Parity audit**
- `parity_audit.py` — compares Python workspace coverage against the archived TypeScript surface when a local archive is present

### Milestones
- Fastest GitHub repository in history to reach 30K stars
- Featured in *The Wall Street Journal*, March 21, 2026
- Entire initial porting session orchestrated with [oh-my-codex (OmX)](https://github.com/Yeachan-Heo/oh-my-codex)
