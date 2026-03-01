# NEXUSMON Fusion Manifest

This manifest fuses prior operator directives, implemented runtime layers, and governance artifacts into one anchored system record.

## Ownership + Provenance
- Operator ownership anchor: Regan (operator sovereign profile)
- Provenance registry: `data/fusion/idea_registry.jsonl`
- Integrity model: append-only hash chain (`prev_hash` -> `hash`)
- Verification endpoint: `/v1/fusion/verify`

## Fused System Layers
- Prime organism runtime
- Federation manager
- Partner + Shadow evolution
- Operator OS (cockpit APIs)
- Artifact Vault (lineage, experiments, outcomes)
- Operator Identity Layer
- Policy-as-code enforcement
- Charter + Prime Directive governance
- Operational pipeline (blueprint -> offer -> checkout -> fulfillment -> ledger)

## Canonical Documents
- [docs/NEXUSMON_AGENT_BUILD_FINAL.md](docs/NEXUSMON_AGENT_BUILD_FINAL.md)
- [docs/NEXUSMON_BUILD_MATRIX.md](docs/NEXUSMON_BUILD_MATRIX.md)
- [docs/NEXUSMON_DUAL_MODE_CHARTER.md](docs/NEXUSMON_DUAL_MODE_CHARTER.md)

## Registry Usage
Register any major idea/spec before implementation:

- `POST /v1/fusion/register`
  - title
  - owner
  - source
  - summary
  - tags
  - linked_docs

Then verify continuity:

- `GET /v1/fusion/verify`
- `GET /v1/fusion/summary`

## Operational Intent
This fusion layer exists to preserve authorship lineage, lock idea history to implementation history, and prevent design drift across future NEXUSMON evolution.

