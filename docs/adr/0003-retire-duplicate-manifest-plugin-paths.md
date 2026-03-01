# ADR-0003: Retire Duplicate Manifest/Plugin Paths (Proposal)

- Status: Proposed
- Date: 2026-03-01
- Scope: Future destructive cleanup, not executed in Phase 4

## Context
Canonical paths are:
- manifests: `config/manifests/`
- plugins: `plugins/`

Duplicate/legacy paths still exist for compatibility.

## Proposal
Converge on canonical paths only after:
1. Alias map is complete.
2. All active loaders read canonical paths.
3. CI and replay confirm no runtime resolution drift.

## Guardrails
- No deletion in Phase 4.
- Operator-approved destructive PR only.
- Rollback artifact required.

## Rollback
Re-enable path aliases and restore removed path loaders from release tag.
