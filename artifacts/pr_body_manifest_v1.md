## goal
Enforce manifest-first agent contracts with `schemas/agent-manifest.v1.json`, seed canonical manifests, and add CI-enforced validation plus a feature-flag/hot-reload prototype.

## scope
- Strict v1 schema enforcement for `config/manifests/*.json`
- Canonical manifests (`fetcher`, `transformer`, `reporter`) plus normalized seed manifests
- Minimal registry API (`load_all`, `get`, `query`) with duplicate-id rejection
- Generated per-manifest schema tests and deterministic generator check
- Feature flag provider interface + file-backed provider + LaunchDarkly scaffold
- Manifest watcher + CI-gated hot apply + audit logging
- Dogfood plugin chain (`fetcher -> transformer -> reporter`)

## required deliverables
- [x] `schemas/agent-manifest.v1.json`
- [x] `config/manifests/fetcher@1.0.0.json`
- [x] `config/manifests/transformer@1.0.0.json`
- [x] `config/manifests/reporter@1.0.0.json`
- [x] `tests/manifest_validation.py`
- [x] `tools/gen_manifest_tests.py` + generated `tests/test_manifest_*.py`
- [x] `core/registry.py` + registry unit tests
- [x] feature flags + watcher + audit prototype modules
- [x] docs for manifest semver + ADR requirement
- [x] CI `manifest-gates` job with strict checks and artifact output

## validation matrix
- [x] Valid manifest passes schema validation
- [x] Missing required field fails
- [x] Unknown top-level property fails (`additionalProperties: false`)
- [x] Invalid semver fails
- [x] Invalid `spawn_policy` fails
- [x] Invalid `constraints`/`error_modes` typed-shape tests fail
- [x] Registry loads seeds and indexes by id/capability
- [x] Duplicate ids rejected by default
- [x] Deterministic generation test passes across two runs
- [x] Coverage gate >= 85% (achieved: 97.28% on `core.registry`)
- [x] Dogfood chain test passes

## out-of-scope
- Production rollout wiring for external flag provider SDK credentials
- Non-manifest CI/job refactors outside manifest gates
- Full runtime migration of all legacy manifest call-sites beyond bridge compatibility

## reviewer checklist
- [ ] Schema is strict and minimal with explicit extension path
- [ ] Canonical manifests reflect real plugin contracts
- [ ] Registry duplicate-id semantics and deterministic query ordering are correct
- [ ] Hot-reload applies only after CI gate artifact pass
- [ ] Audit logs include required fields and redaction
- [ ] Dogfood chain demonstrates manifest-driven capability routing

## attached artifacts
- `schemas/agent-manifest.v1.json`
- `config/manifests/*.json` canonical + normalized seed manifests
- `tools/gen_manifest_tests.py` and generated `tests/test_manifest_*.py`
- `core/registry.py` and registry tests
- `.github/workflows/ci.yml` (`manifest-gates` job)
- `docs/manifest-semver.md`
- `docs/adr/000-manifest-breaking-changes.md`
- `artifacts/manifest-validation-status.json`
- `artifacts/dogfood-manifest-chain.log`

## dogfooding logs
Dogfood run output saved at `artifacts/dogfood-manifest-chain.log`.
Chain selected manifests:
- fetcher: `fetcher@1.0.0`
- transformer: `transformer@1.0.0`
- reporter: `reporter@1.0.0`
