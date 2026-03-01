# Manifest Semver Rules

## Versioning policy
- `MAJOR`: breaking schema or manifest contract changes.
- `MINOR`: additive compatible fields or capability expansions.
- `PATCH`: typo or metadata-only corrections with no contract impact.

## Migration expectations
- Breaking changes require an ADR and migration notes.
- Additive changes must keep old consumers operating until next major.
- Every changed manifest must pass schema validation and generated tests.

## Compatibility windows
- Current major and previous major are supported during migration.
- Hot-reload only applies manifests that pass CI validation for current SHA.

## ADR requirement
- Any core behavior change triggered by manifest evolution must link an ADR in PR.
