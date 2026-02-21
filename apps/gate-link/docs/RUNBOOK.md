# GATE//LINK MVP Runbook

## Purpose

Operational quickstart for the isolated MVP app in `apps/gate-link`.

## Local run

```bash
cd apps/gate-link
npm install
npm run dev
```

## LAN/mobile device run

```bash
cd apps/gate-link
npm run dev:host
```

Open the printed Vite network URL on your device.

## Build and verify

```bash
cd apps/gate-link
npm run typecheck
npm run build
npm run preview
```

## Gameplay loop (MVP)

- Enter mission
- Move partner (`Arrow` keys)
- Use abilities (`Q/W/E`) and chips (`1/2/3`)
- Clear enemy before timer ends
- Receive XP + Data Shards
- Progression persists in browser `localStorage`

## Save controls

- `Space`: redeploy after mission end
- `R`: reset local save and restart session

## Scope boundary

- This is an isolated game prototype under `apps/gate-link`
- No backend coupling to main SWARMZ runtime
- In-game currency is fictional local state only
