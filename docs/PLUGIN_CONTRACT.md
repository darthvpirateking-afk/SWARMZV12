# Plugin Contract

## Manifest Requirements
- Every plugin must have a manifest that validates against `schemas/agent-manifest.v1.json`.
- Required fields and types must match schema exactly.
- Undeclared fields are not allowed unless schema extension explicitly permits them.

## Capability Declaration Rules
- Capabilities are allowlists, not hints.
- Plugin runtime behavior must remain within declared capabilities.
- Capability escalation attempts must be rejected and logged.

## Allowed Side Effects
- Side effects are capability-bound.
- Plugins must not mutate:
  - `core/`
  - `schemas/`
  - kernel runtime configuration
- Any plugin violating core boundary is quarantined.

## Testing Expectations
- Schema validation tests for plugin manifests.
- Capability-bound execution tests.
- Failure mode tests (invalid inputs, missing dependencies, runtime exceptions).
- Observability tests for redaction and event emission.

## Versioning and Deprecation
- Additive-only evolution by default.
- Breaking manifest/plugin behavior requires ADR + migration notes.
- Deprecated plugin behavior must include replacement path and rollback guidance.
