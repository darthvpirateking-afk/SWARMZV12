# ADR-0002: Retire Legacy Backend Routes (Proposal)

- Status: Proposed
- Date: 2026-03-01
- Scope: Future destructive cleanup, not executed in Phase 4

## Context
Canonical backend is `swarmz_server.py`, while legacy route surfaces remain active for compatibility.
This duplicates ownership and increases drift risk.

## Proposal
After compatibility window and replay validation:
1. Inventory legacy-only routes.
2. Ensure canonical replacements exist.
3. Migrate clients.
4. Remove legacy-only routes in a controlled major cleanup.

## Guardrails
- No removal without operator approval.
- Diff and rollback artifact required.
- Replay and smoke checks must pass pre/post.

## Rollback
Restore removed routes from tagged release and re-enable compatibility overlay.
