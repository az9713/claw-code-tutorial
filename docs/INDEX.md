# Documentation Index

Quick reference for all Claw Code documentation.

> **Porting status: partial implementation — not a complete reimplementation.**
> 33 of 184 tools and 17 of 207 commands now have real handlers (file I/O, bash execution, task/team/agent management, web fetching, cron scheduling, config, and session commands). The remaining 151 tools and 190 commands still return placeholder strings. All 30 subsystem packages load only JSON metadata. The original TypeScript source is not included. See [Architecture § Porting Status](ARCHITECTURE.md#porting-status) for the full breakdown, [TOOL_IMPLEMENTATIONS.md](TOOL_IMPLEMENTATIONS.md) for the tool handler reference, and [COMMAND_IMPLEMENTATIONS.md](COMMAND_IMPLEMENTATIONS.md) for the command handler reference.

> **Two documentation suites exist in this repository:**
> - `docs/` (this suite) — detailed reference documentation with full dataclass field tables, complete API signatures, and comprehensive examples.
> - `docs_by_codex/` — concise operational documentation generated on 2026-03-31, with a maintenance standard, ADR backlog, operations runbook, and roadmap. See [`docs_by_codex/README.md`](../docs_by_codex/README.md) for its index.
>
> Both suites are kept accurate against the code. When they disagree, check the source file — the code is authoritative.

---

## Getting Started

| Document | What it covers |
|----------|---------------|
| [Quick Wins](QUICK_WINS.md) | **Start here** — setup + 5 quick wins for developers, curious users, and researchers |
| [Verification Report](VERIFICATION_REPORT.md) | Audit of every QUICK_WINS.md command: exact outputs, fixes applied, what was skipped and why |
| [Installation](INSTALLATION.md) | Full prerequisites, clone, verify, run tests |
| [Troubleshooting](TROUBLESHOOTING.md) | Common errors and how to fix them |

---

## Using the CLI

| Document | What it covers |
|----------|---------------|
| [CLI Reference](CLI_REFERENCE.md) | All 22 subcommands with flags and examples |
| [Configuration Reference](CONFIGURATION.md) | QueryEngineConfig, permission flags, deferred init, session directory |

---

## Understanding the Codebase

| Document | What it covers |
|----------|---------------|
| [Architecture](ARCHITECTURE.md) | System overview, terminology, bootstrap lifecycle, module map, data flow, streaming events, session lifecycle |
| [API Reference](API_REFERENCE.md) | Every public class, method, and dataclass |
| [Agents](AGENTS.md) | Everything about the agent harness: AgentTool, built-in agents, multi-agent infrastructure, task tools, coordinator mode, permissions |
| [Tool Implementations](TOOL_IMPLEMENTATIONS.md) | The 33 real tool handlers: what each does, which store it touches, and how to add more |
| [Command Implementations](COMMAND_IMPLEMENTATIONS.md) | The 17 real command handlers: what each returns and the dispatch mechanism |
| [Study Plan](STUDY_PLAN.md) | Structured 7-phase reading plan for understanding the codebase inside out |

---

## Contributing

| Document | What it covers |
|----------|---------------|
| [Developer Guide](DEVELOPER_GUIDE.md) | Project layout, code conventions, adding subsystems, adding commands/tools, test patterns, parity audit workflow, JSON schemas |
| [Contributing](../CONTRIBUTING.md) | PR workflow, branch naming, commit messages, clean-room policy |

---

## Project Records

| Document | What it covers |
|----------|---------------|
| [Changelog](../CHANGELOG.md) | Version history and release notes |
| [License](../LICENSE) | MIT License with Anthropic disclaimer |
| [Security](SECURITY.md) | Vulnerability reporting, permission model, session data handling |

---

## Key Concepts at a Glance

**Terminology**

| Term | Short definition |
|------|-----------------|
| Mirrored | A stub entry that records a command/tool's name and original TypeScript path but executes a placeholder |
| Archived | The original TypeScript Claude Code source (may not be present locally) |
| Porting workspace | This Python repository as a whole |
| Subsystem | One of the 30 `src/` packages corresponding to directories in the original TypeScript codebase |
| Reference data | JSON files in `src/reference_data/` describing the archived surface |

**Most-used CLI commands**

```bash
python3 -m src.main summary                    # workspace overview
python3 -m src.main bootstrap "my prompt"      # full session trace
python3 -m src.main route "my prompt"          # see what matches
python3 -m src.main commands --query bash      # search commands
python3 -m src.main tools --no-mcp            # tools without MCP
python3 -m src.main parity-audit               # coverage metrics
python3 -m unittest discover -s tests -v       # run tests
```

**Most-used API entry points**

```python
from src import PortRuntime, QueryEnginePort

# Route a prompt
matches = PortRuntime().route_prompt("review the auth module")

# Full session
session = PortRuntime().bootstrap_session("review the auth module")
print(session.as_markdown())

# Multi-turn loop
results = PortRuntime().run_turn_loop("review the auth module", max_turns=3)

# Stream events
for event in QueryEnginePort.from_workspace().stream_submit_message("my prompt"):
    print(event["type"])
```
