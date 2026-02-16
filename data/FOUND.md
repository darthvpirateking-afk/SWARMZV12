# FOUND

## Existing
- Backend: FastAPI at run_server.py / swarmz_runtime.api.server, default port 8012, UI in web_ui/.
- Endpoints: /health, /v1/health, /v1/dispatch, /v1/sovereign/dispatch, /v1/system/log, pairing, missions, runtime views.
- Storage: data/ (missions.jsonl, audit.jsonl, profile.txt), packs/ (existing), config/runtime.json.
- Launchers: SWARMZ_UP.ps1/.cmd, daemon loop scripts, smoke tests.

## Will add
- Quality layer under tools/quality with lint/scan wrappers and audit logging.
- Verify/replay/rollback spine under swarmz_runtime.verify + patchpack helpers and endpoints.
- Factory loop and mission graph endpoints under swarmz_runtime.factory.
- Perf/cache endpoints and small perf scripts; scheduler state in data/scheduler*.json(l).
- Control-plane scaffold under apps/control-plane (additive, separate from web_ui).
- Selfcheck runner hitting new endpoints and creating dummy mission + patchpack.

## Will skip
- No restructuring of existing UI/backend; no removal of current endpoints or launchers.

## Start command
- Typical: `python run_server.py --port 8012 --host 0.0.0.0` (or via SWARMZ_UP.ps1/.cmd).
