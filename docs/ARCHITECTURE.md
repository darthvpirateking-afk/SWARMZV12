# NEXUSMON Architecture

NEXUSMON v0.1 is a governed, deterministic kernel architecture.

Biological terminology is doctrine/UI vocabulary only.
Kernel behavior is strict contracts, manifests, routing, validation, and observability.

## Canonical Backend
- Canonical runtime surface: `swarmz_server.py`
- Canonicalization decision: `docs/adr/0001-canonical-backend.md`
- Legacy-compatible runtime during migration: `swarmz_runtime/api/server.py`

## v0.1 Kernel Components
- Manifest schema: `schemas/agent-manifest.v1.json`
- Manifest model/validation: `core/agent_manifest.py`
- Manifest registry: `core/manifest_registry.py`
- Spawn context: `core/spawn_context.py`
- Capability router: `core/capability_router.py`
- Observability baseline: `core/observability.py`
- Seed manifest: `config/manifests/helper1.manifest.json`
- Plugin runtime unit: `plugins/helper1.py` (migration target)

## Frontend Surfaces
- `frontend/` (React/Vite)
- `ui/` (React cockpit)
- `cockpit/` (Preact)
- `web/` (static surface)

All surfaces must converge on canonical backend contracts.

## Governance and Boundaries
- Core boundary: `docs/CORE_BOUNDARY.md`
- Runtime invariants: `docs/RUNTIME_INVARIANTS.md` (migration artifact)
- Plugin contract: `docs/PLUGIN_CONTRACT.md` (migration artifact)

## Migration Policy
- Additive-first and reversible.
- No silent behavior changes.
- No destructive deletion without explicit operator approval.
