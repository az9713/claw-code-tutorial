# Documentation Maintenance Standard

## Objective

Keep documentation debt at zero for all externally observable behavior in this repository.

## Definition of Done (Documentation)

A change is not done unless:

1. Affected CLI/API/runtime behavior is documented in `docs_by_codex/`.
2. Existing examples still run as written.
3. Terminology is consistent with [Glossary](./GLOSSARY.md).
4. Tests reflect changed behavior.

## Required Update Matrix

- CLI option added/removed:
  - Update [CLI Reference](./CLI_REFERENCE.md)
  - Update [Quickstart](./QUICKSTART.md) if user-facing
- Runtime lifecycle change:
  - Update [Runtime Lifecycle](./RUNTIME_LIFECYCLE.md)
  - Update [Architecture](./ARCHITECTURE.md) if structural
- Persistence format change:
  - Update [Python API Reference](./PYTHON_API_REFERENCE.md)
  - Update [Operations Runbook](./OPERATIONS_RUNBOOK.md)
  - Add migration note in changelog
- Security/policy change:
  - Update [Configuration and Security](./CONFIGURATION_AND_SECURITY.md)
  - Add ADR entry if design-level

## Review Checklist for Maintainers

1. Are all changed public contracts documented?
2. Are docs still code-accurate after final rebase?
3. Are broken/deprecated commands explicitly marked?
4. Are dates/version references updated?
5. Did we avoid speculative statements not backed by code?
