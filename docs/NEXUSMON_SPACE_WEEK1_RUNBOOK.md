# NEXUSMON Space Pivot Week 1 Runbook

This runbook covers the first space worker mission:

- intent: `swarmz-minion-space-sim`
- artifact: `packs/<mission_id>/moon_transit.json`
- ingestion: Nexusmon XP + artifact vault + mission note

## Optional dependency

Install astropy for higher-fidelity transit calculations:

```powershell
pip install -r requirements-space.txt
```

Without astropy, the worker uses a deterministic fallback approximation and still completes.

## Step 1: Set build mode

```powershell
curl -X POST "http://localhost:8012/v1/mode" `
  -H "Content-Type: application/json" `
  -d "{\"mode\":\"BUILD\"}"
```

## Step 2: Dispatch the space mission

```powershell
curl -X POST "http://localhost:8012/v1/build/dispatch" `
  -H "Content-Type: application/json" `
  -d "{\"intent\":\"swarmz-minion-space-sim\",\"spec\":{\"date_utc\":\"2026-03-01\",\"lat_deg\":-37.8136,\"lon_deg\":144.9631,\"elevation_m\":30,\"timezone\":\"Australia/Melbourne\"}}"
```

Capture the returned `mission_id`.

## Step 3: Let the runner execute

If `run_server.py` is running normally, `swarm_runner` runs in the background.

Check status:

```powershell
curl "http://localhost:8012/v1/swarm/status"
```

## Step 4: Verify artifacts

Expected files:

- `packs/<mission_id>/result.json`
- `packs/<mission_id>/moon_transit.json`

Example:

```powershell
Get-Content "packs/<mission_id>/result.json"
Get-Content "packs/<mission_id>/moon_transit.json"
```

`result.json` includes:

- `type: space_moon_transit`
- `method: astropy|fallback`
- `transit_utc`
- `quality_score`
- `xp_awarded`
- `artifact_id`
- `note`

## Step 5: Verify Nexusmon growth signals

### XP updated

Inspect `data/nexusmon.db`:

- table: `entity_state`
- field: `evolution_xp`

### Artifact stored

Inspect `data/nexusmon.db`:

- table: `artifacts`
- new row tagged with `space`, `moon`, `transit`, `simulation`

## Step 6: Verify audit events

Inspect `data/audit.jsonl` for:

- `mission_started`
- `space_sim_completed`
- `mission_finished`
