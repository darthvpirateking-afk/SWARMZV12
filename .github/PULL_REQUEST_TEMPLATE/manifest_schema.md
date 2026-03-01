# PR: Manifest Schema Change

## Type
- [ ] New manifest in `config/manifests/`
- [ ] Additive schema field (minor version bump)
- [ ] Breaking schema change (major bump + ADR required)

## Version impact
| Before | After | Type |
|--------|-------|------|
| `v?.?.?` | `v?.?.?` | additive / breaking / patch |

**ADR (if breaking):** `docs/adr/ADR-NNN-<title>.md`

## Manifest checklist
- [ ] All required fields present
- [ ] `id` matches `^[a-z][a-z0-9_-]*$`
- [ ] `version` is valid semver
- [ ] `capabilities` use `namespace.action`, no duplicates
- [ ] `spawn_policy` is `singleton | pooled | ephemeral`
- [ ] `error_modes` covers all three required failure paths
- [ ] No unknown top-level fields (use `extensions`)

## CI gates
- [ ] `pytest tests/test_manifest_schema.py` green
- [ ] `mypy --strict` zero errors
- [ ] Branch coverage >= 85%
- [ ] `ruff check .` clean
