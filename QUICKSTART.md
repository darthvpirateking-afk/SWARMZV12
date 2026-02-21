# SWARMZ — Quick Start Guide

Everything you need to run SWARMZ on your desktop and access the UI from your phone.

---

## 1 · One-time setup

```bash
# Clone (if you haven't already)
git clone https://github.com/darthvpirateking-afk/SWARMZV12.git
cd SWARMZV12

# Create a virtual environment and install Python dependencies
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2 · Start the backend (API server)

```bash
# From the repo root (virtual env active):
python run_server.py
```

The server starts on **http://localhost:8012** by default.  
To override: `PORT=9000 python run_server.py`

Verify it is up:

```bash
curl http://localhost:8012/health/live
# → {"status":"alive","runtime":"swarmz-core","pulse":true}
```

---

## 3 · Start the frontend (UI)

Open a **second terminal**:

```bash
cd frontend
npm install          # first time only
npm run dev
```

The UI opens at **http://localhost:5173**  
(Vite proxies `/v1` and `/health` to the backend automatically.)

---

## 4 · Open on your phone

While both the backend and `npm run dev` are running on your desktop:

1. Find your desktop's LAN IP (e.g. `192.168.1.42`):
   - Windows: `ipconfig`
   - Mac/Linux: `ifconfig` or `ip a`
2. On your phone browser, open:  
   `http://<LAN_IP>:5173`
3. **Install as an app** — tap the browser menu → "Add to Home Screen".  
   The app ships a PWA manifest and service worker, so the shell works offline after install.

> Both devices must be on the same Wi-Fi network.

---

## 5 · What each UI card does

| Card | What it does |
|---|---|
| **CockpitTopBar** | Sticky header — shows live runtime status ring + heartbeat pulse |
| **OperatorIdentityPanel** | Your operator name, session ID, build tag |
| **CompanionAvatarDock** | Animated companion glyph that reflects runtime health |
| **RuntimeControlCard** | Start / Stop / Restart the SWARMZ engine with live status |
| **MissionLifecycleCard** | Launch a new mission, monitor active missions, Pause/Resume/Abort |
| **MissionTimelineVisualizer** | Shows state-transition history for each mission (hidden when empty) |
| **KernelLogsViewer** | Live-streaming log viewer with All / Warnings / Errors / Missions tabs |

All cards poll the backend every 3–5 seconds automatically.

---

## 6 · Is the AI working?

The AI/agent layer is wired through the mission engine:

- **Launch a mission** from the `MissionLifecycleCard` — type a goal and press **Launch**.
- The kernel processes it through the `SwarmzOrchestrator`.
- Progress appears in `MissionTimelineVisualizer` and logs appear in `KernelLogsViewer`.

The AI uses the models configured in `config/runtime.json`.  
To run without external API calls, set `OFFLINE_MODE=true` before starting:

```bash
OFFLINE_MODE=true python run_server.py
```

---

## 7 · Improvements shipped today (v12.0 → current)

1. **App Store Tracker removed** — the matrix rankings widget was removed from the cockpit UI so the layout stays clean and focused on mission control.
2. **PWA manifest** (`frontend/public/manifest.json`) — enables "Add to Home Screen" install prompt on Android and iOS Safari.
3. **Service worker** (`frontend/public/sw.js`) — caches the app shell offline; API calls always go live.
4. **Apple PWA meta tags** — `apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style`, and `apple-mobile-web-app-title` so the installed icon looks native on iPhone.
5. **`theme-color` meta tag** — browser chrome tinted SWARMZ teal (`#4EF2C5`) on Android Chrome.
6. **`viewport-fit=cover`** — the UI extends into iPhone notch / Dynamic Island safe areas.
7. **Global CSS reset** (`* { margin: 0; padding: 0; }`) in `index.html` — eliminates browser default margins that caused layout shifts on mobile.
8. **`overscroll-behavior: none`** — prevents the pull-to-refresh bounce on mobile that could confuse the sticky header.
9. **Tighter mobile media query** — breakpoint raised to 600 px (was 480 px), padding reduced to 12 px, gap reduced to 12 px so cards fit comfortably on 375 px screens (iPhone SE / standard).
10. **Title updated** to "SWARMZ Cockpit" — browser tab and PWA splash screen now show the right name.

---

## 8 · How to run tests

```bash
# backend
python3 -m pytest tests/ -q

# frontend type-check
cd frontend && npm run typecheck
```

All 231 backend tests pass. No test changes were required.

---

## 9 · Deployment / always-on

| Target | Command |
|---|---|
| Desktop (Windows) | `SWARMZ_UP.ps1` or `SWARMZ_UP.cmd` |
| Desktop (Unix) | `./RUN.sh api` |
| Always-on daemon | `SWARMZ_DAEMON_UP.ps1` / `SWARMZ_DAEMON_UP.cmd` |
| Docker | `docker compose up` |

The backend listens on `0.0.0.0` so any device on the same network can reach it on port 8012.  
The frontend (Vite dev server) also binds to `0.0.0.0` on port 5173.

For a production build served by the backend:

```bash
cd frontend && npm run build
# static files are output to frontend/dist/
# copy to web_ui/ and the FastAPI StaticFiles mount serves them on /static
```
