# `docs_by_codex` Documentation Suite

Last updated: March 31, 2026

This directory is a complete, code-derived documentation set for the Python-first `claw-code` workspace. It is written for three audiences:

- Users/operators running the CLI
- Developers extending and maintaining the Python code
- Architects evaluating parity, boundaries, and evolution paths

## Read First

1. [System Overview](./SYSTEM_OVERVIEW.md)
2. [Quickstart](./QUICKSTART.md)
3. [Architecture](./ARCHITECTURE.md)
4. [Agentic Harness](./AGENTIC_HARNESS.md)

## Full Map

- [System Overview](./SYSTEM_OVERVIEW.md)
- [Quickstart](./QUICKSTART.md)
- [Architecture](./ARCHITECTURE.md)
- [Agentic Harness](./AGENTIC_HARNESS.md)
- [Runtime Lifecycle](./RUNTIME_LIFECYCLE.md)
- [CLI Reference](./CLI_REFERENCE.md)
- [Python API Reference](./PYTHON_API_REFERENCE.md)
- [Configuration and Security](./CONFIGURATION_AND_SECURITY.md)
- [Testing and Quality Gates](./TESTING_AND_QUALITY.md)
- [Operations Runbook](./OPERATIONS_RUNBOOK.md)
- [Extension and Porting Guide](./EXTENSION_AND_PORTING_GUIDE.md)
- [Roadmap and ADR Backlog](./ROADMAP_AND_ADR_BACKLOG.md)
- [Glossary](./GLOSSARY.md)
- [Documentation Maintenance Standard](./DOC_MAINTENANCE_STANDARD.md)

## Related Documentation

A second documentation suite lives in [`docs/`](../docs/INDEX.md). It provides:
- Full dataclass field tables for every type
- Complete API signatures with parameter descriptions
- Troubleshooting guide
- Detailed architecture with root-level mirror file mapping

When both suites cover the same topic, the code is the final authority. Both suites should be updated together when code changes.

## Source of Truth Policy

- Code behavior is authoritative.
- This documentation is authoritative for onboarding and operations intent.
- When code and docs diverge, fix docs and code in the same pull request.
- Any PR that changes CLI arguments, runtime semantics, or persisted formats must update at least one file in this directory.
