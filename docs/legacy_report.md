# Legacy Report

- Generated from: `observatory/cleanup/cleanup-report-20260228T160425Z.json`
- Timestamp: `2026-02-28T16:04:25.878782Z`
- Apply mode: `False`

## Deleted Legacy Folders
- None found matching configured legacy patterns.

## Deleted Legacy Files
- `hologram_snapshots/snapshot_1772294483_d57fdf8d.tmp`

## Moved Logs
- `data/server_live.log -> observatory/logs/data__server_live.log`

## Replacement Mapping
- Legacy or scattered runtime manifests -> `core/manifests/registry.json`
- Scattered telemetry/log files -> `observatory/logs/`
- Non-unified hook paths -> `runtime/hooks.py` + `runtime/events.py`
- Ad-hoc scheduler loops -> `runtime/scheduler.py`
- Symbolic/life API operations -> governed via backend routers and manifest-gated hooks

## Remaining TODOs
- Top-level normalization backlog (operator-reviewed; intentionally not auto-moved):
- `__pycache__`
- `addons`
- `api`
- `apps`
- `artifacts`
- `backend`
- `bootstrap`
- `config`
- `control_plane`
- `data`
- `design`
- `dev`
- `evolution`
- `forge`
- `frontend`
- `galileo`
- `hologram_snapshots`
- `k8s`
- `kernel_runtime`
- `matrix`
- `mobile`
- `models`
- `nexusmon`
- `operator_console`
- `operator_interface`
- `packs`
- `paste-agent`
- `plugins`
- `prepared_actions`
- `public`
- `schemas`
- `skills`
- `src`
- `swarmz`
- `swarmz_app`
- `swarmz_runtime`
- `system`
- `theorem_kb`
- `tools`
- `ui`
- `web`
- `web_ui`

## Notes
- Top-level extras detected; not auto-moved to avoid non-deterministic breakage.
- Use this report as an operator-reviewed migration backlog for structural normalization.
