# NEXUSMON STYLE CANON — v1.0

> **Purpose:** Lock the visual language so every UI/asset matches the same "NEXUSMON" look.

## 0) IMMUTABLE RULE

If anything conflicts: **the reference images win**. Match their vibe, spacing, glow, density, and "glass HUD" feel.

## 1) REFERENCE PACK

Reference images are stored in `/design/moodboard/`:

- `ref_01.png` — `ref_07.png` (PNG)
- `ref_08.jpg` — `ref_09.jpg` (JPEG)

**Agent rule:**
- If the tool supports image input: ALWAYS attach these refs when generating UI/branding.
- If it does not: use the "Style DNA" + "Tokens" below exactly.

## 2) STYLE DNA

**"Ancient-future cosmic command HUD":**

- Deep black space background + faint star dust + subtle vertical "data rain"
- Frosted-glass panels with thin neon outlines
- Electric violet core energy + cyan/teal diagnostics + occasional mint highlights
- Circular radars, orbit rings, lattice grids, node graphs
- Minimal, high-contrast typography (sci-fi sans) + microtext + tick marks
- Glow is controlled (no overbloom), edges are crisp, corners slightly chamfered
- UI feels like an instrument panel: measured, engineered, not playful

## 3) TOKENS

### 3.1 Base Colors (dominant)

| Token            | Value                     |
|------------------|---------------------------|
| Void             | `#05070C`                 |
| Deep Slate       | `#0B1017`                 |
| Panel Shadow     | `rgba(0,0,0,0.55)`       |
| Glass Fill       | `rgba(18,24,32,0.55)`    |
| Glass Fill 2     | `rgba(10,14,20,0.35)`    |

### 3.2 Accent Colors (signature)

| Token            | Value      |
|------------------|------------|
| Neon Violet      | `#A855F7`  |
| Electric Purple  | `#7C3AED`  |
| Plasma Magenta   | `#D946EF`  |
| Neon Cyan        | `#22D3EE`  |
| Teal Scan        | `#14B8A6`  |
| Mint Status      | `#86EFAC`  |
| Warning Amber    | `#F59E0B`  |
| Error Red        | `#EF4444`  |

### 3.3 Glow + Stroke Rules

- Border stroke: 1px–2px, never thick
- Outer glow: 8–16px blur, 20–40% opacity
- Inner glow: 4–10px blur, 15–30% opacity
- Use glow only on key affordances (buttons, active graph lines, core nodes)

### 3.4 Layout Rules (HUD geometry)

- Primary frame: top title bar + left nav + central "scene" + right diagnostics
- Panels align to an 8px grid
- Spacing: 16/24/32px rhythm
- Corner radius: 14–18px (not bubbly, not sharp)
- Use thin separators + micro labels + numeric readouts

### 3.5 Typography

| Role    | Fonts                               |
|---------|-------------------------------------|
| Titles  | Orbitron / Rajdhani / Oxanium (all caps) |
| Body    | Inter / IBM Plex Sans               |
| Numbers | IBM Plex Mono / JetBrains Mono      |

**Rules:**
- Titles letter-spacing: +0.08em
- Small labels: 10–12px, 70–80% opacity
- No "cute" fonts, no serif

## 4) COMPONENT BLUEPRINTS

### 4.1 Glass Panel

- Background: `rgba(18,24,32,0.55)`
- Backdrop blur: 12–18px (if supported)
- Border: `1px solid rgba(34,211,238,0.25)` or `rgba(168,85,247,0.22)`
- Inner highlight line: 1px at top with 10–15% opacity
- Noise/scanline overlay: 2–4% opacity

### 4.2 HUD Button (3 states)

| State  | Appearance                                         |
|--------|----------------------------------------------------|
| Idle   | Dark glass + faint border                          |
| Hover  | Border brightens + slight inner glow               |
| Active | Neon fill gradient (violet→cyan) + stronger glow   |

Text always all caps, compact.

### 4.3 Graph / Radar / Lattice

- Thin grid lines (5–10% opacity)
- 1–2 bright traces (cyan/violet)
- Nodes glow on focus only
- Add tick marks + small numeric labels

### 4.4 Background "Space + Data"

- Star field subtle
- Vertical "matrix rain" extremely faint
- Occasional lens specks / nebula haze behind center content

## 5) DO / DON'T (QUALITY GATES)

### DO ✅

- Keep it dark, crisp, instrument-like
- Use controlled glow and thin geometry
- Put numbers everywhere (efficiency, stability, units, uptime)
- Use symmetry and circular motifs

### DON'T ❌

- No cartoon / no flat playful UI
- No thick borders, no heavy gradients everywhere
- No cluttered rainbow palette
- No glossy skeuomorphic buttons
- No random icons; everything looks "engineered"

## 6) PROMPT CORE

**Base prompt (UI mock / dashboard / panel):**

> NEXUSMON command HUD interface, dark space background with subtle star dust and faint vertical data rain, frosted glass panels, thin neon cyan and electric violet outlines, circular radar rings, orbit lines, node lattice network visualization, microtext labels, numeric readouts, crisp sci-fi typography, controlled glow, cinematic high detail, symmetrical layout, ultra clean instrument panel, no cartoon, no flat design

**Negative prompt:**

> cartoon, kawaii, childish, thick borders, oversaturated rainbow, messy layout, blurry text, low contrast, chunky UI

## 7) AGENT INSTRUCTION

You are implementing NEXUSMON UI and assets.
You must obey the NEXUSMON STYLE CANON v1.0.
Do not invent a new aesthetic. Reuse tokens + components.
When producing UI, always specify:
- background layer
- panel layer
- accent usage
- typography choice
- glow rules

If unsure, simplify (fewer elements), keep the look.

## 8) FAST "STYLE CHECK" (BEFORE SHIPPING ANY SCREEN)

A screen is valid only if:
- [ ] It reads as "cosmic HUD / command console" in 1 second
- [ ] 80% of the pixels are dark
- [ ] Accents are limited to 2–3 hues (violet/cyan/teal)
- [ ] Borders are thin and crisp
- [ ] Glow is present but not flooding the page

