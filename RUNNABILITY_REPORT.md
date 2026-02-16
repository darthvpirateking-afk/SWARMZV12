# SWARMZ Runnability Report

## Entrypoints
- Backend: FastAPI via `run_swarmz.py` serving on port 8012 (binds 0.0.0.0)
- UI: static assets under `web_ui/` served at `/app` by the backend
- Config: `config/runtime.json` (api_base, ui_base)
- Data dir: `data/` (missions, ledgers, phase/counterfactual artifacts)

## Start Commands
- PowerShell: `./SWARMZ_UP.ps1`
- CMD: `SWARMZ_UP.cmd`
Both run `tools/self_check.py`, install deps (venv), start backend, and open the UI at http://localhost:8012/.

## Health / Connectivity
- Health: `GET http://localhost:8012/v1/health` → ok/version/uptime/data_dir/ui_expected/offline_mode
- Runtime status: `GET http://localhost:8012/v1/runtime/status`
- Counterfactual/phase: `GET http://localhost:8012/v1/runtime/counterfactual`, `GET http://localhost:8012/v1/runtime/phase`
- Dispatch example (Windows curl): `curl -X POST http://localhost:8012/v1/dispatch -H "Content-Type: application/json" -d "{\"goal\":\"hello\",\"category\":\"demo\",\"constraints\":{}}"`

## Known Ports/URLs
- Backend/API: http://localhost:8012
- UI: http://localhost:8012/app (served by backend)
- LAN (phone browser): http://<your_LAN_IP>:8012

## What Works Now
- Backend boots via SWARMZ_UP scripts; health endpoint responds.
- UI served from `/app`.
- Missions can be dispatched via `/v1/dispatch`.
- Data is written to `data/` (perf/evolution/counterfactual/phase logs, etc.).

## Known Gaps / Risks
- PWA assets rely on existing `web_ui`; ensure built assets are present.
- External AI/model calls remain disabled in OFFLINE_MODE; if you need cloud calls, set `OFFLINE_MODE=0`.
- `package.json` scripts are minimal; frontend tooling may need install/build if modified.
