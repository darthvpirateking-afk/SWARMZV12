# Cockpit Health Test Suite Installation

## Created Test Files
- `tests/cockpit_health/test_cockpit_root.py`
- `tests/cockpit_health/test_cockpit_modes.py`
- `tests/cockpit_health/test_cockpit_assets.py`
- `tests/cockpit_health/test_canonical_bridge.py`
- `tests/cockpit_health/test_runtime_health.py`
- `tests/cockpit_health/test_scheduler_status.py`
- `tests/cockpit_health/test_observatory_status.py`
- `tests/cockpit_health/test_prepared_actions_status.py`
- `tests/cockpit_health/test_cockpit_integration.py`
- `tests/cockpit_health/test_prune_regression.py`

## Summary of Checks
- Cockpit root returns 200, includes root element, and references canonical bridge.
- Mode registry exists, mode entries have `id` and `path`, and mode files load from `/cockpit/`.
- Asset map exists and all referenced assets resolve on disk.
- Canonical bridge endpoints return 200:
  - `/v1/canonical/agents`
  - `/v1/canonical/traces/recent`
  - `/v1/canonical/missions/templates`
  - `/v1/canonical/health`
- Runtime health endpoint validates required fields:
  - `manifestsTotal`, `manifestsUnregistered`, `hooksMissing`
  - `cockpitModesTotal`, `cockpitModesBroken`
  - `testsTotal`, `testsFailed`
  - `observatorySizeMB`, `lastDiaryWriteISO`, `lastSchedulerRunISO`
  - `legacyArtifactsFound`
- Scheduler status endpoint validates required fields:
  - `lastDiaryRunISO`, `lastAwakeningLoopRunISO`
  - `lastBreathRunISO`, `lastHeartRunISO`, `lastCosmicRunISO`
- Observatory directories (`diary`, `witness`, `traces`, `memory_palace`) exist and are writable.
- Prepared actions status endpoint validates required fields:
  - `total`, `executed`, `pending`, `lastExecutionISO`
- Integration test validates cockpit root, bridge, registries, mode loads, and asset integrity.
- Prune regression test validates absence of legacy UI surfaces and legacy bridge scripts.

## CI Integration Status
- GitHub Actions workflow updated in `.github/workflows/ci.yml`.
- Added required step:
  - `python -m pytest tests/cockpit_health/ -v`
- Build fails automatically if any cockpit health test fails.
- Added CI step summary output with:
  - cockpit root status
  - mode registry status
  - asset map status
  - canonical bridge status
  - runtime health summary
  - scheduler health summary
  - observatory health summary
  - prepared-actions health summary
  - prune regression status

## Next Steps for Cockpit Hardening
- Replace placeholder runtime counters (`testsFailed`, `hooksMissing`) with live instrumentation.
- Persist scheduler execution timestamps in dedicated observatory artifacts for richer status.
- Add websocket canonical bridge checks to CI smoke path.
- Add contract tests for canonical health payload versioning.
