# ADR-0001: Canonical Backend Selection

- Status: Accepted
- Date: 2026-02-28
- Decision Owners: Operator + Core Runtime Maintainers

## Context
NEXUSMON currently exposes overlapping backend surfaces:
- `swarmz_server.py`
- `swarmz_runtime/api/server.py`

This overlap increases drift risk across routes, startup behavior, and integration contracts.

## Decision
`swarmz_server.py` is the canonical backend runtime surface for v0.1 migration.

`swarmz_runtime/api/server.py` remains a legacy-compatible surface during migration and is not removed in this phase.

## Rationale
- `swarmz_server.py` already carries the broadest active endpoint coverage.
- Existing tests and integrations are more heavily centered on this surface.
- Canonicalizing one runtime reduces contract ambiguity without destructive edits.

## Consequences
- New canonical app wrapper will be introduced in `backend/app.py`.
- Entry scripts will be normalized to route through canonical runtime path.
- Compatibility behavior remains additive during migration.

## Non-Goals
- No deletion of legacy runtime in this ADR.
- No major route removals or breaking API changes.

## Rollback Plan
If canonicalization causes regression:
1. Revert commits associated with this ADR rollout.
2. Restore prior entrypoint/runtime wiring.
3. Re-open ADR with updated migration evidence.

## References
- Codex v0.1 (frozen)
- Core boundary policy
- Runtime invariants (artifact to be added in migration)
