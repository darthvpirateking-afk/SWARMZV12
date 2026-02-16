# SWARMZ First Run

## What happens on desktop
- SWARMZ runs as a local web app in your browser. Open http://localhost:8012/ after start.
- The UI is a PWA shell (manifest + service worker) cached for offline viewing.

## What happens on phone
- Connect the phone to the same Wi-Fi/LAN and open the LAN URL shown at startup (e.g., http://LAN_IP:8012/).
- Pair with the operator PIN from the host console.

## "App on phone" truth
- A PWA already ships (manifest.json + sw.js). You can "Install" from the browser prompt for an app-like icon and offline UI shell.
- There is no native store app; use the browser/PWA.

## Offline mode
- Set OFFLINE_MODE=true before starting to disable external model calls. Missions will log and mark status `offline`; UI + logs keep working.
- Health endpoint reports `offline_mode:true` so the UI shows "Mode: Offline".

## How to start
- One-time setup: `python tools/swarmz_onboard.py` (chooses bind/port, writes config/runtime.json, checks health).
- Daily run: `SWARMZ_UP.ps1` (or .cmd) for normal session.
- Always-on: `SWARMZ_DAEMON_UP.ps1`/`.cmd` to auto-restart and log to data/daemon.log.

## How to know it’s working
- Check http://localhost:8012/v1/health → `{ "ok": true }`.
- UI status pills show Health: OK and Mode: Online/Offline.
- Audit panel in UI shows events; data/audit.jsonl grows.

## First thing to try
- From UI, click Dispatch and enter a goal (e.g., “status”).
- Or call: `curl -X POST http://localhost:8012/v1/dispatch -H "X-Operator-Key: <PIN>" -d '{"goal":"status"}'`.

## Where data lives
- data/ : missions.jsonl, audit.jsonl, profile.txt, daemon.log.
- config/ : runtime.json.
- data/operator_anchor.json + data/operator_pin.txt: operator identity/PIN.
