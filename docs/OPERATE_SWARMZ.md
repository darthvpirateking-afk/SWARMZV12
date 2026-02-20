# OPERATE SWARMZ (Quick Operator Guide)

## Start + URLs

- Start (Windows): `SWARMZ_UP.ps1` or `SWARMZ_UP.cmd`
- Default local URL: `http://127.0.0.1:8012/`
- API docs: `http://127.0.0.1:8012/docs`
- Health: `http://127.0.0.1:8012/v1/health`
- Phone (same Wi-Fi): `http://<LAN_IP>:8012/`

## Ports and Servers

- Main runtime: port `8012` (configured in `config/runtime.json`)
- Main launcher path: `run_server.py` -> `server:app`
- Alternate launcher path: `swarmz_server.py` (also defaults to `8012`)
- Daemon mode: `SWARMZ_DAEMON_UP.ps1` / `SWARMZ_DAEMON_UP.cmd`
- Docker profile (separate): `8000` API, `5173` UI, `5432` Postgres

## Runtime Profiles (Local vs Render)

- Show current profile:
	- `python tools/switch_runtime_profile.py --show`
- Switch to local profile:
	- `python tools/switch_runtime_profile.py local`
- Switch to Render profile:
	- `python tools/switch_runtime_profile.py render`
- Convenience wrappers:
	- `SWARMZ_PROFILE.cmd local` or `SWARMZ_PROFILE.cmd render`
	- `./SWARMZ_PROFILE.ps1 local` or `./SWARMZ_PROFILE.ps1 render`

## Reconnect to Main Swarm

- One click (CMD): `SWARMZ_MAIN_SWARM.cmd`
- One click (PowerShell): `./SWARMZ_MAIN_SWARM.ps1`
- Manual equivalent: `python tools/switch_runtime_profile.py render`

## What Each Main Button Does (`/app`)

### Pairing
- **Pair Device**: sends your PIN to `/v1/pairing/pair` and stores session token.
- **Refresh Pairing Info**: reads `/v1/pairing/info`.

### Console
- **Run Prompt**: runs your typed command (health, runs, audit, dispatch, pair shortcuts).
- **Clear Console**: clears console output panel.

### Runs / Detail / Audit
- **Refresh Runs**: loads `/v1/runs`.
- **Dispatch Mission**: sends goal/category to `/v1/dispatch`.
- **Refresh Run Detail**: loads `/v1/runs/{id}` for selected run.
- **Refresh Audit**: loads `/v1/audit/tail?limit=50`.

### Ignition
- **Run Command**: executes selected operator action via `/v1/admin/command`.
- **Validate Kernel**: posts to `/v1/verify/kernel`.

### Meta Sovereignty
- **Make Sovereign Decision**: posts context/options to `/v1/meta/decide`.
- **Apply Sovereign Control**: posts controls to `/v1/meta/control`.
- **Check Lattice Status**: reads lattice/meta status via `/v1/meta/lattice`.

### Task Matrix + Kernel Ignition
- **Process Task Matrix**: posts to `/v1/meta/task-matrix`.
- **Get Ignition Status**: reads `/v1/meta/ignition-status`.
- **Execute Kernel Ignition**: posts state vector to `/v1/meta/kernel-ignition`.
- **Clear State**: clears ignition JSON field only.

### Command Center
- **Refresh Command Center**: loads `/v1/command-center/state`.
- **Set Autonomy**: posts autonomy level to `/v1/command-center/autonomy`.
- **Apply Shadow Mode**: posts shadow settings to `/v1/command-center/shadow`.
- **Promote Partner**: posts partner ID to `/v1/command-center/evolution/promote`.
- **Publish Listing**: posts listing to `/v1/command-center/marketplace/publish`.
- **Load Listings**: reads `/v1/command-center/marketplace/list`.

## If Something Feels Stuck

- Check health first: `/v1/health`
- Confirm paired state and token in the Pairing section
- Re-open with `SWARMZ_UP.ps1`
- Use `python tools/swarmz_doctor.py` for diagnostics

## Release Readiness Commands

- Quick release gate (files + config):
	- `python tools/release_gate.py`
- Full smoke gate (health + dispatch):
	- `python tools/release_gate.py --smoke`
- Smoke only:
	- `python tools/release_smoke.py`