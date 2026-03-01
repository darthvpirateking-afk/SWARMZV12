# Cockpit-Only Legacy Prune Report

Date: 2026-03-01
Branch: `migration/cockpit_legacy_prune`

## Deleted Directories
- `ui/` (deleted)
- `web/` (deleted)
- `web_ui/` (deleted)
- `organism/` (not present at prune time)

## Deleted Files
```text
ui/Dockerfile
ui/__init__.py
ui/avatar/avatar_view.js
ui/avatar/controls.js
ui/avatar/test_avatar.html
ui/cockpit/dashboard.js
ui/cockpit/telemetry_view.js
ui/components/MasterSwarmzHologram.tsx
ui/index.html
ui/nexusmon-cockpit.html
ui/package.json
ui/src/App.tsx
ui/src/api.ts
ui/src/avatar/Avatar.tsx
ui/src/avatar/AvatarActions.ts
ui/src/avatar/AvatarPanel.tsx
ui/src/avatar/AvatarState.ts
ui/src/components/Cockpit.tsx
ui/src/components/StatusCard.tsx
ui/src/main.tsx
ui/src/vite-env.d.ts
ui/tsconfig.json
ui/vite.config.ts
web/.gitignore
web/activity_viewer.html
web/app.css
web/app.js
web/avatar.html
web/claimlab.html
web/dev-server.cjs
web/hologram.css
web/hologram.html
web/hologram.js
web/index.html
web/market_lab.html
web/neon-modern.css
web/neon-modern.js
web/nexusmon_cockpit.html
web/nexusmon_console.html
web/nexusmon_console.js
web/nexusmon_landing.html
web/package.json
web/shell.html
web/trials.css
web/trials.html
web/trials.js
web/vercel.json
web_ui/app.js
web_ui/icons/icon-192.png
web_ui/icons/icon-512.png
web_ui/index.html
web_ui/manifest.json
web_ui/styles.css
web_ui/sw.js
```

## New Cockpit Asset Map Summary
Generated: `cockpit/assets/asset_map.json`

- `js_bundles`: 22
- `css_bundles`: 1
- `images`: 0
- `mode_components`: 15

Validation:
- Every asset map path resolves to an existing file: pass

## New Cockpit Mode Registry Summary
Generated: `cockpit/modes/registry.json`

- Entries: 15
- IDs:
  - `altar_modes`
  - `cosmic_hud`
  - `cryptid_radar`
  - `federation_council`
  - `grimoire_viewer`
  - `lineage_tree`
  - `lost_civilization_scanner`
  - `memory_palace_explorer`
  - `multiverse_viewer`
  - `pantheon_browser`
  - `relic_inventory`
  - `sigil_renderer`
  - `sovereign_mirror_panel`
  - `synchronicity_web`
  - `time_echo_viewer`

Validation:
- Every registry path resolves to an existing mode file: pass

## Canonical Bridge Status
- Frontend canonical bridge module added: `cockpit/src/canonical_bridge.js`
- `cockpit/index.html` now loads canonical bridge before app boot
- Cockpit client now resolves hologram endpoints from canonical bridge only
- Direct `/hologram/*` usage removed from cockpit source
- Server mount added: `/v1/canonical/cockpit/hologram` (alongside existing `/hologram` compatibility mount)

## Cockpit Health Check Results
| Check | Result |
|---|---|
| `GET /cockpit/` | 200 |
| Mode static loads (`/cockpit/modes/*.tsx`) | 15/15 pass |
| `GET /v1/canonical/agents` | 200 |
| `GET /v1/canonical/agents/health` | 200 |
| `GET /v1/canonical/traces/recent` | 200 |
| `GET /v1/canonical/cockpit/state` | 200 |
| `GET /v1/canonical/cockpit/hologram/snapshot/latest` | 200 |
| `WS /v1/canonical/cockpit/hologram/ws` | connected, initial `hologram.snapshot` received |

## Route Compatibility
- `GET /` -> redirects to `/cockpit/` (307)
- `GET /organism` -> redirects to `/cockpit/` (307)
- `GET /console` -> redirects to `/cockpit/` (307)
