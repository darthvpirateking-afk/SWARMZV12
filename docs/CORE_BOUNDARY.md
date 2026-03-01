# NEXUSMON Core Boundary

> **Enforced.** Any change to a Core module requires an ADR + second reviewer approval.

## The rule
> If removing or changing this module forces changes in more than one other module, it is Core.

## Core modules (immutable without ADR)

| Module | Responsibility | Change rule |
|--------|---------------|-------------|
| `schemas/agent-manifest.v1.json` | Manifest contract - single source of truth | Additive -> minor bump. Breaking -> major + ADR |
| `core/agent_manifest.py` | Typed manifest model + validation | No new fields without schema update first |
| `core/manifest_registry.py` | Capability-indexed registry | API shape frozen at v0.1 |
| `core/spawn_context.py` | Context envelope + least-privilege | Privilege escalation always rejected |
| `core/capability_router.py` | Scoring, fallback, conflict detection | Weights configurable; algorithm -> ADR |
| `core/observability.py` | Structured log schema + trace IDs | Field additions OK; removals -> ADR |

## Non-Core (additive via plugins/patchpacks)
- `plugins/` - plugin manifests and implementations
- `config/manifests/` - seed/operator manifests (data, not code)
- `swarmz_server.py` - API layer
- `backend/agent/` - agent implementations

## What "no core mutation" means in practice

| Scenario | Action |
|----------|--------|
| New capability token needed | Add to manifest `capabilities[]` |
| New manifest field needed | Add to `extensions{}` |
| Bug in routing logic | Fix + ADR + replay test |
| New spawn policy needed | ADR required - spawn policies are a Core enum |

## Enforcement
- `mypy --strict` on all Core modules - zero errors required
- Branch coverage >= 85% on Core modules
- `ruff check` - zero warnings
- PR touching Core without ADR link -> auto-blocked by PR template

## Required References
- Architecture overview: `docs/ARCHITECTURE.md`
- Runtime law: `docs/RUNTIME_INVARIANTS.md`
- Plugin behavior contract: `docs/PLUGIN_CONTRACT.md`
- Additive bundle guidance: `docs/PATCHPACK_SCHEMA.md`
