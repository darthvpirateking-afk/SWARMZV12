# SWARMZ First Run

## What happens on desktop
- SWARMZ runs as a local web app in your browser. Open the URL derived from `config/runtime.json` (default http://localhost:8012/).
- The UI is a PWA shell (manifest + service worker) cached for offline viewing.

## What happens on phone
- Connect the phone to the same Wi-Fi/LAN and open the LAN URL shown at startup (http://<LAN_IP>:PORT from runtime config).
- Pair with the operator PIN from the host console (`data/operator_pin.txt`).

## "App on phone" truth
- A PWA already ships (manifest.json + sw.js). You can "Install" from the browser prompt for an app-like icon and offline UI shell.
- There is no native store app; use the browser/PWA.

## Offline mode
- Set OFFLINE_MODE=true (or set `offlineMode: true` in `config/runtime.json`) before starting to disable external model calls. Missions will log and mark status `offline`; UI + logs keep working.
- Health endpoint reports `offline_mode:true` so the UI shows "Mode: Offline".

## How to start
- One-time setup: `python tools/swarmz_onboard.py` (choose bind/port/offline, writes config/runtime.json, ensures operator anchor/pin, runs doctor, smoke-starts server once).
- Daily run: `SWARMZ_UP.ps1` (or `.cmd`) for normal session; it reads runtime config, runs self_check, opens the browser, and starts the server.
- Always-on: `SWARMZ_DAEMON_UP.ps1`/`.cmd` to auto-restart and log to `data/daemon.log` (reads runtime config first).

## How to know it’s working
- Check `GET /v1/health` (e.g., `Invoke-RestMethod http://127.0.0.1:8012/v1/health | ConvertTo-Json`) → `ok: true`.
- UI status pills show Health: OK and Mode: Online/Offline.
- Audit panel in UI shows events; `data/audit.jsonl` grows.

## First thing to try
- From UI, click Dispatch and enter a goal (e.g., “status”).
- Or call (category must be coin/forge/library/sanctuary):
	`python -c "import json,urllib.request; data=json.dumps({'goal':'status','category':'coin','constraints':{}}).encode(); req=urllib.request.Request('http://127.0.0.1:8012/v1/dispatch', data=data, headers={'Content-Type':'application/json','X-Operator-Key':'<PIN>'}); print(urllib.request.urlopen(req).read().decode())"`

## Where data lives
- data/ : missions.jsonl, audit.jsonl, profile.txt, daemon.log.
- config/ : runtime.json.
- data/operator_anchor.json + data/operator_pin.txt: operator identity/PIN.
