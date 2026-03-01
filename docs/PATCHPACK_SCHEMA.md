# PatchPack Schema

## Purpose
PatchPacks are additive change bundles for governed migration and evolution.

## Allowed Contents
- New manifests
- New plugins
- New missions
- New docs and tests
- Compatibility adapters

## Append-Only Rules
- PatchPacks must not destructively mutate core components.
- PatchPacks must not remove historical lineage references.
- Any destructive operation requires explicit operator approval and ADR linkage.

## Required Metadata
- `pack_id`
- `created_at`
- `provenance`
- `changes`
- `rollback_artifact`
- `risk_summary`

## Rollback
- Every PatchPack must reference rollback artifact(s) for the previous stable state.
- Rollback instructions must be deterministic and reproducible.
