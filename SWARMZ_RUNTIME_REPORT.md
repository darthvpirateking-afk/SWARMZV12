# SWARMZ Runtime Audit

## Logging
- Legacy server logging only in `swarmz_server.py` (writes to data/server_live.log); current FastAPI runtime (`swarmz_runtime/api/server.py`) had no centralized logging before this pass.
- Mission/audit events are appended as JSONL via `swarmz_runtime/storage/db.py` and `swarmz_runtime/core/engine.py` (audit entries include timestamps).
- No built-in verbose flag prior to this pass; added optional verbose toggle (`--verbose`) to surface start/stop and telemetry prints.

## Telemetry
- Before: no dedicated telemetry bus; durations and failures were not tracked; mission/audit logs captured events only.
- After: lightweight telemetry bus (`swarmz_runtime/core/telemetry.py`) appends events, durations, failures; mission runs emit durations to `data/runtime_metrics.jsonl`; generic events go to `data/telemetry.jsonl`.
- No CPU/queue load metrics existed; runtime status endpoint now reports coarse load estimate and average step time when available.

## Execution Model
- Uvicorn FastAPI app (`run_swarmz.py` -> `swarmz_runtime/api/server.py`) single-process, async-capable; mission logic inside `SwarmzEngine` is synchronous.
- Auto loop (`swarmz_runtime/core/autoloop.py`) runs in a daemon thread with tick interval sleep; rate-limited and kill-switch aware.
- Missions stored/updated in JSONL files (`data/missions.jsonl`, `data/audit.jsonl`); no IPC beyond files and in-memory engine instance.

## Bottlenecks / Risks
- Mission updates rewrite/read JSONL files per call; potential I/O cost grows with file size (no indexing).
- Auto loop performs repeated disk reads/writes each tick; sleeps guard against busy spinning.
- No caching for mission loads; every list/detail reads the file.
- No prior timing metrics to spot slow paths (now added).

## Runtime Visibility
- Before: limited visibility—`/v1/ui/state` in legacy server, missions/audit endpoints, but no live runtime status.
- After: new `/v1/runtime/status` exposes active missions, queued pending missions, average step time, last telemetry event, and a coarse system load estimate; audit tail and runs endpoints already provide recent history.

## Gaps Remaining / Notes
- No CPU/memory sampling yet; status endpoint reports only mission-derived load.
- Mission execution still synchronous; no parallel execution of independent tasks implemented.
- File-based storage remains; large logs could slow reads—consider rotation/compaction later (not changed here per constraints).
- Polling loops are rate-limited and sleep-backed; no busy-wait detected, but they still rely on time-based wakeups rather than events.

## Suggested Next Checks
- Observe `data/runtime_metrics.jsonl` growth and rotate if needed.
- If mission volume increases, consider indexing/compaction for JSONL reads (outside current additive scope).
- Optionally surface CPU/memory snapshots into telemetry for load estimation.
