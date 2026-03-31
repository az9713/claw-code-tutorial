# Roadmap and ADR Backlog

## Vision

Evolve from metadata mirror scaffold to a robust, policy-driven harness runtime while preserving traceability to archived surface parity.

## Near-Term Roadmap (0-3 months)

1. Add schema versioning and validation for `reference_data` snapshots.
2. Add structured error model for CLI and API surfaces.
3. Add deterministic, compatibility-safe session file versioning.
4. Add richer tests for routing/scoring and persistence edge cases.

## Mid-Term Roadmap (3-6 months)

1. Introduce real command/tool execution adapters for selected high-value entries.
2. Replace remote mode stubs with transport abstractions.
3. Add security hardening (allowlists, encrypted session store, audit logs).
4. Add typed JSON schema artifacts for snapshots and sessions.

## Long-Term Roadmap (6+ months)

1. Runtime-equivalent behavior parity for prioritized command/tool paths.
2. Pluggable policy engine for trust, permissions, and environment gates.
3. Multi-tenant, production-grade persistence and observability.

## ADR Backlog

Use this format:

```text
ADR-XXXX: <title>
Status: Proposed | Accepted | Superseded
Date: YYYY-MM-DD
Context:
Decision:
Consequences:
```

Proposed ADRs:

1. ADR-0001: Snapshot Schema Versioning and Validation
2. ADR-0002: Session Persistence Backward Compatibility Contract
3. ADR-0003: Tool Permission Model (`deny` + `allow` + policy hooks)
4. ADR-0004: Runtime Mode Transport Interface Design
5. ADR-0005: Structured Error Envelope for CLI and Library APIs

## Documentation Governance

- Documentation owner: maintainers of `src/main.py`, `src/runtime.py`, `src/query_engine.py`.
- Required review for architecture-affecting PRs: at least one maintainer review.
- Update cadence: per merged feature, not batched monthly.
