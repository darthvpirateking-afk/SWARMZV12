# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import os
import json
import socket
import secrets
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from zoneinfo import ZoneInfo

from swarmz_runtime.core.engine import SwarmzEngine
from swarmz_runtime.api import missions, system, admin
from addons.api.addons_router import router as addons_router
from addons.api.guardrails_router import router as guardrails_router
from addons.api.dashboard_router import router as dashboard_router
from addons.api.ui_router import router as ui_router
from addons.auth_gate import LANAuthMiddleware
from addons.rate_limiter import RateLimitMiddleware
from swarmz_runtime.api import missions, system, admin, ecosystem

app = FastAPI(
    title="SWARMZ",
    version=os.getenv("SWARMZ_VERSION", "0.0.0"),
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
UI_DIR = ROOT_DIR / "web_ui"
DATA_DIR.mkdir(exist_ok=True, parents=True)
START_TIME = datetime.now(timezone.utc)


def _load_runtime_config() -> Dict[str, Any]:
    cfg_path = ROOT_DIR / "config" / "runtime.json"
    if not cfg_path.exists():
        return {}
    try:
        raw = json.loads(cfg_path.read_text())
    except Exception:
        return {}

    # Normalize legacy keys to the requested schema without breaking older config
    cfg: Dict[str, Any] = {}
    if isinstance(raw, dict):
        cfg.update(raw)
        api_base = raw.get("apiBaseUrl") or raw.get("api_base") or raw.get("api_base_url")
        ui_base = raw.get("uiBaseUrl") or raw.get("ui_base") or raw.get("ui_base_url")
        if api_base:
            cfg["apiBaseUrl"] = api_base
        if ui_base:
            cfg["uiBaseUrl"] = ui_base
        if "bind" not in cfg and raw.get("host"):
            cfg["bind"] = raw.get("host")
        if "port" not in cfg and raw.get("api_port"):
            cfg["port"] = raw.get("api_port")
        if "offlineMode" not in cfg and "offline_mode" in raw:
            cfg["offlineMode"] = raw.get("offline_mode")
    return cfg


def _lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _resolve_offline_mode(cfg: Dict[str, Any]) -> bool:
    env_val = os.getenv("OFFLINE_MODE")
    if env_val is not None and env_val not in {"", "0", "false", "False"}:
        return True
    if env_val is not None and env_val in {"0", "false", "False"}:
        return False
    return bool(cfg.get("offlineMode"))


def _load_operator_pin() -> Dict[str, Any]:
    """Resolve operator PIN, preferring env, then config, otherwise generate."""
    pin_source = "env"
    pin = os.getenv("SWARMZ_OPERATOR_PIN")
    config_path = DATA_DIR / "config.json"
    pin_file = DATA_DIR / "operator_pin.txt"

    if not pin and config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
            if cfg.get("operator_pin"):
                pin = str(cfg.get("operator_pin")).strip()
                pin_source = "config"
        except Exception:
            pin = None

    if not pin and pin_file.exists():
        try:
            pin = pin_file.read_text().strip()
            pin_source = "file"
        except Exception:
            pin = None

    generated = False
    if not pin:
        pin = "".join(secrets.choice("0123456789") for _ in range(6))
        pin_source = "generated"
        generated = True
        pin_file.write_text(pin)
        print(f"[SWARMZ] Generated operator PIN; saved to {pin_file}")

    return {"pin": pin, "source": pin_source, "file": pin_file, "generated": generated}


_runtime_cfg = _load_runtime_config()
OFFLINE_MODE = _resolve_offline_mode(_runtime_cfg)

_pin_info = _load_operator_pin()
OPERATOR_PIN = _pin_info["pin"]
app.state.operator_pin_source = _pin_info

VERBOSE = os.getenv("SWARMZ_VERBOSE", "0") not in {"0", "false", "False", None}
telemetry.set_verbose(VERBOSE)

engine = SwarmzEngine(data_dir=str(DATA_DIR))
engine.offline_mode = OFFLINE_MODE
engine.operator_key = OPERATOR_PIN


def get_engine() -> SwarmzEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SwarmzEngine()
    return _engine_instance

missions.get_engine = get_engine
system.get_engine = get_engine
admin.get_engine = get_engine
ecosystem.set_engine_provider(get_engine)

app.include_router(missions.router, prefix="/v1/missions", tags=["missions"])
app.include_router(system.router, prefix="/v1/system", tags=["system"])
app.include_router(admin.router, prefix="/v1/admin", tags=["admin"])
app.include_router(addons_router, prefix="/v1/addons", tags=["addons"])
app.include_router(guardrails_router, prefix="/v1/guardrails", tags=["guardrails"])
app.include_router(dashboard_router, tags=["dashboard"])
app.include_router(ui_router, tags=["ui"])
app.include_router(ecosystem.router, prefix="/v1/ecosystem", tags=["ecosystem"])

# ---------------------------------------------------------------------------
# PWA app-shell served at /
# ---------------------------------------------------------------------------
_PWA_SHELL = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SWARMZ</title>
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.svg">
<meta name="theme-color" content="#0d1117">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
background:#0d1117;color:#c9d1d9;display:flex;flex-direction:column;align-items:center;
justify-content:center;min-height:100vh;padding:1.5rem;text-align:center}
h1{font-size:2rem;margin-bottom:.25rem;color:#58a6ff}
.tag{font-size:.85rem;color:#8b949e;margin-bottom:1.5rem}
.cards{display:grid;gap:.75rem;width:100%;max-width:400px}
a.card{display:block;padding:1rem;border-radius:10px;background:#161b22;
text-decoration:none;color:#c9d1d9;border:1px solid #30363d;transition:border-color .2s}
a.card:hover{border-color:#58a6ff}
a.card h2{font-size:1rem;color:#58a6ff;margin-bottom:.25rem}
a.card p{font-size:.85rem;color:#8b949e}
footer{margin-top:2rem;font-size:.75rem;color:#484f58}
</style>
</head>
<body>
<h1>&#x1F41D; SWARMZ</h1>
<p class="tag">Operator-Sovereign Mission Engine &middot; v1.0.0</p>
<div class="cards">
 <a class="card" href="/ui"><h2>Operator Console</h2><p>Interactive UI &mdash; execute tasks, browse capabilities</p></a>
 <a class="card" href="/dashboard"><h2>Dashboard</h2><p>Mission monitoring &amp; status</p></a>
 <a class="card" href="/docs"><h2>API Docs</h2><p>Interactive Swagger UI</p></a>
 <a class="card" href="/health"><h2>Health</h2><p>Service health check</p></a>
 <a class="card" href="/v1/missions/list"><h2>Missions</h2><p>List active missions</p></a>
 <a class="card" href="/v1/system/omens"><h2>System Omens</h2><p>Current system signals</p></a>
 <a class="card" href="/v1/system/predictions"><h2>Predictions</h2><p>Engine forecasts</p></a>
</div>
<footer>Tip&nbsp;&bull; Open this page on your phone and tap <em>Add to Home Screen</em> for an app icon.</footer>
<script>
if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js');}
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def root():
    return _PWA_SHELL

# ---------------------------------------------------------------------------
# PWA assets
# ---------------------------------------------------------------------------
_ICON_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<rect width="100" height="100" rx="20" fill="#0d1117"/>
<text x="50" y="68" font-size="52" text-anchor="middle" fill="#58a6ff">&#x1F41D;</text>
</svg>"""

_MANIFEST = """\
{
  "name": "SWARMZ",
  "short_name": "SWARMZ",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0d1117",
  "theme_color": "#0d1117",
  "icons": [
    {"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml"},
    {"src": "/apple-touch-icon.svg", "sizes": "180x180", "type": "image/svg+xml"}
  ]
}"""

_SW_JS = """\
const CACHE = 'swarmz-v1';
const SHELL = ['/', '/manifest.webmanifest', '/icon.svg', '/apple-touch-icon.svg'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(
    ks.filter(k => k !== CACHE).map(k => caches.delete(k))
  )));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // Network-first for API calls and OpenAPI spec
  if (url.pathname.startsWith('/v1/') || url.pathname.startsWith('/docs/openapi')
      || url.pathname === '/openapi.json') {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }
  // Cache-first for shell assets
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request))
  );
});
"""

@app.get("/manifest.webmanifest")
def manifest():
    return Response(content=_MANIFEST, media_type="application/manifest+json")

@app.get("/sw.js")
def service_worker():
    sw_file = _file_in_ui("sw.js")
    if sw_file.exists():
        return FileResponse(sw_file, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="service worker not found")


@app.post("/v1/sovereign/dispatch")
def sovereign_dispatch(body: SovereignDispatch):
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    mission_id = f"M-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(4)}"
    mission = {
        "mission_id": mission_id,
        "intent": body.intent,
        "scope": body.scope,
        "limits": body.limits,
        "status": "PENDING",
        "timestamp": ts,
    }
    missions_file = DATA_DIR / "missions.jsonl"
    audit_file = DATA_DIR / "audit.jsonl"
    _append_jsonl(missions_file, mission)
    _append_jsonl(audit_file, {"ts": ts, "event": "sovereign_dispatch", "mission_id": mission_id})
    return {"ok": True, "mission_id": mission_id, "status": "PENDING"}


@app.get("/v1/system/log")
def system_log(tail: int = 10):
    lim = max(1, min(tail, 500))
    audit_file = DATA_DIR / "audit.jsonl"
    return {"entries": _tail_jsonl(audit_file, lim)}


@app.head("/sw.js")
def service_worker_head():
    sw_file = _file_in_ui("sw.js")
    if sw_file.exists():
        return FileResponse(sw_file, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="service worker not found")


@app.get("/styles.css")
def styles_file():
    f = _file_in_ui("styles.css")
    if f.exists():
        return FileResponse(f, media_type="text/css")
    raise HTTPException(status_code=404, detail="styles not found")


@app.head("/styles.css")
def styles_head():
    f = _file_in_ui("styles.css")
    if f.exists():
        return FileResponse(f, media_type="text/css")
    raise HTTPException(status_code=404, detail="styles not found")


@app.get("/app.js")
def app_js_file():
    f = _file_in_ui("app.js")
    if f.exists():
        return FileResponse(f, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="app bundle not found")


@app.head("/app.js")
def app_js_head():
    f = _file_in_ui("app.js")
    if f.exists():
        return FileResponse(f, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="app bundle not found")


@app.get("/icons/{icon_name}")
def icon_file(icon_name: str):
    f = _file_in_ui("icons") / icon_name
    if f.exists():
        return FileResponse(f)
    raise HTTPException(status_code=404, detail="icon not found")

