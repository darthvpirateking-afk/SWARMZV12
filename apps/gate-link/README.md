# GATE//LINK (MVP)

Mobile-first tactical RPG prototype.

## Current MVP

- 5x5 tactical dual-grid combat shell
- Partner controlled by player
- Shadow ally auto-fights
- Chips (3-slot hand) for burst/heal/buff/summon effects
- Gate missions with timer and rewards
- Local progression save (partner level/form + data shards)

## Controls

- Move: Arrow keys
- Abilities: `Q`, `W`, `E`
- Chips: `1`, `2`, `3`
- Redeploy after mission: `Space`
- Reset local save: `R`

## Run

```bash
cd apps/gate-link
npm install
npm run dev
```

## Validate

```bash
npm run typecheck
npm run build
```

## Safety boundary

- In-game economy (`Data Shards`) is local fictional currency.
- No real-token linkage in gameplay systems.
