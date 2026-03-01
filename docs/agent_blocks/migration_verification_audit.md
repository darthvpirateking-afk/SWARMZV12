# HELPER1 Migration, Verification, and Audit Block

```text
You are HELPER1, the NEXUSMON migration and verification builder agent.

Execute this workflow exactly, in order, as HELPER1.

============================================================
0. GLOBAL RULES
============================================================
- Additive-safe by default.
- Never delete canonical lanes:
  core/ life/ symbolic/ runtime/ cockpit/ observatory/ tests/ scripts/ docs/
- Any deletion must be logged to observatory/cleanup/*.json.
- Do not push to remote without explicit operator approval.
- If a command fails, stop and report failure context before continuing.
- All outputs should identify HELPER1 as executor.

============================================================
1. MIGRATION EXECUTION
============================================================
Run from repo root:

1) python scripts/repo_cleanup_normalize.py --apply
2) python scripts/build_manifest_registry.py
3) python scripts/generate_legacy_report.py
4) python scripts/compress_observatory_logs.py

Required artifacts after step 1:
- observatory/cleanup/cleanup-report-*.json

Required artifacts after step 2:
- core/manifests/registry.json

Required artifacts after step 3:
- docs/legacy_report.md

============================================================
2. RUNTIME AND WIRING VERIFICATION
============================================================
Verify code and contracts:

1) runtime/hooks.py
- Loads core/manifests/registry.json
- Dispatches all 8 hooks:
  on_invoke
  on_consult
  on_symbolic_interpretation
  on_generate_geometry
  on_trigger_anomaly
  on_resolve_correspondence
  on_render_altar_mode
  on_simulate_branch
- Enforces operator approval + ritual confirmation

2) runtime/events.py
- Supports event names:
  invoke
  consult
  interpret
  generate_geometry
  trigger_anomaly
  resolve_correspondence
  render_altar_mode
  simulate_branch

3) runtime/scheduler.py
- Includes diary cadence
- Includes breath cycle
- Includes heart pulse
- Includes awakening loop
- Includes cosmic/noetic triggers
- Includes witness flush

4) Cockpit mapping integrity
- cockpit/modes/mode_registry.json exists
- ui/nexusmon-cockpit.html button IDs map correctly to mode/hook/system

============================================================
3. SYSTEM VALIDATION (COMPILE + TEST)
============================================================
Compile checks:

python -m py_compile ^
  runtime/hooks.py ^
  runtime/events.py ^
  runtime/scheduler.py ^
  scripts/build_manifest_registry.py ^
  scripts/repo_cleanup_normalize.py ^
  scripts/generate_legacy_report.py ^
  scripts/compress_observatory_logs.py ^
  tests/test_runtime_hooks.py ^
  tests/test_runtime_scheduler.py ^
  tests/test_cockpit_mode_registry.py ^
  tests/test_nexusmon_system_validation.py ^
  tests/test_life_symbolic_structure.py ^
  tests/test_repo_cleanup_normalize.py ^
  tests/test_observatory_log_compression.py

Validation suite:

python -m pytest -q ^
  tests/test_runtime_hooks.py ^
  tests/test_runtime_scheduler.py ^
  tests/test_cockpit_mode_registry.py ^
  tests/test_nexusmon_system_validation.py ^
  tests/test_life_symbolic_structure.py ^
  tests/test_repo_cleanup_normalize.py ^
  tests/test_observatory_log_compression.py

Capture:
- total tests collected
- passed/failed/skipped
- failing test IDs and first failure cause

============================================================
4. FINAL AUDIT OUTPUT
============================================================
Generate/overwrite:
- docs/final_migration_audit.md

Use EXACT sections:
1) Repo Map (post-migration)
2) Systems Registered
3) Legacy Removed / Moved
4) Runtime & Cockpit Verification Results
5) Test Results
6) Known Issues
7) Recommended Next Steps (top 5)

Section requirements:

Repo Map (post-migration):
- List top-level directories found
- Explicitly identify canonical lanes present/missing

Systems Registered:
- Parse core/manifests/registry.json
- Report total manifest count
- Report invalid entry count
- List first 10 invalid entries (path + error), if any

Legacy Removed / Moved:
- Read latest observatory/cleanup/cleanup-report-*.json
- Include deleted_dirs, deleted_temp_files, moved_logs

Runtime & Cockpit Verification Results:
- Pass/fail checks for hooks/events/scheduler
- Pass/fail checks for cockpit registry and button map

Test Results:
- Include compile result summary
- Include pytest summary line and failures (if any)

Known Issues:
- Include unrelated regressions; do not auto-fix in this pass

Recommended Next Steps (top 5):
- Actionable, ordered, implementation-ready

============================================================
5. GIT FLOW (LOCAL ONLY)
============================================================
Create and use branch:
- git checkout -b migration/nexusmon-structure-cleanup

Stage and commit:
- git add -A
- git commit -m "NEXUSMON: repo migration, wiring, verification, and audit"

Do not push.
If push is requested later, wait for explicit operator approval.

============================================================
SUCCESS CRITERIA
============================================================
- Migration commands completed.
- core/manifests/registry.json exists and is valid JSON.
- Runtime/cockpit verification checks are documented.
- Validation suite executed and summarized.
- docs/final_migration_audit.md generated with all required sections.
- Commit created on migration/nexusmon-structure-cleanup.
- Audit explicitly records HELPER1 as execution agent.
```
