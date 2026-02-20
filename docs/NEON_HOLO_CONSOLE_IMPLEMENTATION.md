# SWARMZ Neon Holo Console Implementation

This document maps the neon + hologram UI spec into the current SWARMZ web control surface.

## Visual Language (Neon-on-Dark-Glass)

Implemented in `web_ui/styles.css`:

- Tokenized palette (`--neon-cyan`, `--neon-magenta`, `--neon-lime`, `--neon-violet`)
- Glass surfaces (`--glass`, `--glass-strong`) + blurred panel treatment
- Glow rules via `--shadow-neon` for controls and active surfaces
- Scanline overlay using fixed `body::before`

## Layout + Depth Planes

- Added `z2` depth plane class and hologram panel styling (`.holo-panel`)
- Existing card grid retained for readability and operational density
- Layering remains deterministic for accessibility and audit-first workflows

## Hologram Spec Mapping

- Additive blend highlights on `.holo-panel::after`
- Scanline + slight luminance pulse (`@keyframes holoPulse`)
- Neon border emphasis and focus rings for interaction feedback

## Components / Interaction States

- New console surface in `web_ui/index.html`:
  - Output log (`#consoleOutput`)
  - Prompt input (`#consolePrompt`)
  - Syntax preview (`#consolePreview`)
  - Autocomplete chips (`#consoleAutocomplete`)
  - Run/Clear actions

## Motion Language

Duration tokens in CSS:

- `--dur-fast`: 120ms
- `--dur-mid`: 220ms
- `--dur-slow`: 420ms

Applied to focus, hover, and hologram pulse.

## Command Console Behavior

Implemented in `web_ui/app.js`:

- Prompt command parser
- Tab autocomplete
- Clickable suggestion chips
- Syntax token map rendering:
  - keyword
  - flag
  - number
  - string

Supported commands:

- `help`
- `health`
- `runs`
- `audit`
- `command-center`
- `dispatch <goal>`
- `pair <pin>`
- `clear`

## System Feel (Sound + Haptics)

Implemented best-effort browser hooks in `web_ui/app.js`:

- Audio tones using Web Audio API (`AudioContext`)
- Haptic pulses using `navigator.vibrate` when available
- Triggered on success/error/dispatch events

## Compact Wireframe Blueprint

Primary stack:

1. Status pills
2. Neon holo console (prompt + preview + autocomplete)
3. Existing operational cards (pairing, ignition, meta, matrix, kernel, command center, runs, detail, audit)

## Text-to-Image Prompt Templates

### Prompt A (Control Deck)

"Futuristic neon hologram command console dashboard, dark glass panels, cyan-magenta glow, scanlines, readable operator controls, high contrast typography, minimal clutter, depth layers Z0-Z3, cyber command center, clean UI wireframe"

### Prompt B (Mobile PWA)

"Mobile-first holographic control UI, neon cyan and violet highlights, dark translucent cards, command prompt with autocomplete chips, subtle glow, scanline overlay, practical readable controls, system status pills"

### Prompt C (Mission Ops Wall)

"Advanced mission operations dashboard, hologram data cards, neon token syntax console, audit log panel, futuristic but usable enterprise UI, blue-black glass aesthetic, crisp sans typography"
