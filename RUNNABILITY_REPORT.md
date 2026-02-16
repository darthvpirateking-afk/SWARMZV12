# SWARMZ Runnability Report

## Entrypoints
- Backend: FastAPI `server:app` started by `run_server.py` (reads `config/runtime.json` for `bind` + `port`).
- UI: static PWA under `web_ui/` served by backend at `/app`; runtime config exposed at `/config/runtime.json` for the UI.
- Config: `config/runtime.json` (apiBaseUrl, uiBaseUrl, bind, port, uiPort, offlineMode) is the single source of truth.
- Data: `data/` (missions.jsonl, audit.jsonl, operator_pin.txt, daemon.log, runtime ledgers).

## Start Commands
- PowerShell: `./SWARMZ_UP.ps1` (reads runtime config, runs self_check, opens browser, starts server).
- CMD: `SWARMZ_UP.cmd` (same as above).
- Manual: `python run_server.py --host <bind> --port <port>` (defaults come from runtime config).

## Verified Health + Dispatch
- Health: `GET http://127.0.0.1:8012/v1/health` → `{ ok: true, version: 0.0.0, data_dir: ..., ui_expected: http://localhost:8012/app, offline_mode: false }` (tested via Invoke-RestMethod).
- Dispatch (category must be one of coin|forge|library|sanctuary):
	- Command: `python -c "import json,urllib.request; data=json.dumps({'goal':'status check','category':'coin','constraints':{}}).encode(); req=urllib.request.Request('http://127.0.0.1:8012/v1/dispatch', data=data, headers={'Content-Type':'application/json','X-Operator-Key':'<PIN>'}); print(urllib.request.urlopen(req).read().decode())"`
	- Result (sample): `{ "created": {"mission_id": "16e318aa", ...}, "run": {"status": "completed", ...} }`
- Data writes: new lines appended to `data/missions.jsonl` and `data/audit.jsonl` after dispatch.

## Ports and URLs
- Local API: `http://127.0.0.1:8012`
- Local UI: `http://127.0.0.1:8012/app`
- LAN UI/API: `http://<LAN_IP>:8012` (server binds to `bind` from runtime config; default 0.0.0.0).

## What Works
- self_check + doctor pass (doctor warns about nested package roots and shadow dirs but continues).
- Runtime config is consumed by server, startup scripts, and UI.
- Health and dispatch verified; data directory is writable and records missions.
- PWA shell + service worker served from backend.

## Warnings / Notes
- Existing nested package roots and duplicated directories (mobile/mobile, swarmz-mobile/swarmz-mobile) are reported as WARN; keep using repo root as authoritative.
- doctor reports WARN when the server is not running (health unreachable); start the server to clear it.
- Category validation is strict; use coin/forge/library/sanctuary to avoid 500s.
