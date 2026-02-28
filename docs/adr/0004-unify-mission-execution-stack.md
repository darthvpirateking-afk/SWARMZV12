# ADR-0004: Unify Mission Execution Stack (Proposal)

- Status: Proposed
- Date: 2026-03-01
- Scope: Future destructive cleanup, not executed in Phase 4

## Context
Mission execution exists across multiple stacks and eras.
Phase 4 introduces canonical mission templates and canonical execution endpoints.

## Proposal
Adopt one mission execution lane:
1. Canonical mission template registry.
2. Canonical mission executor interface.
3. Compatibility adapters for legacy engines.
4. Decommission duplicate executors after migration evidence.

## Guardrails
- Deterministic replay required.
- No fallback loops.
- Operator approval and rollback artifact required.

## Rollback
Re-enable legacy mission path routing and disable canonical-only enforcement flags.
