import os

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
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
    title="SWARMZ Runtime",
    description="Operator-Sovereign Mission Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LANAuthMiddleware)
app.add_middleware(RateLimitMiddleware)

_engine_instance = None

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
    return Response(content=_SW_JS, media_type="application/javascript")

@app.get("/icon.svg")
def icon_svg():
    return Response(content=_ICON_SVG, media_type="image/svg+xml")

@app.get("/apple-touch-icon.svg")
def apple_touch_icon():
    return Response(content=_ICON_SVG, media_type="image/svg+xml")

# ---------------------------------------------------------------------------
# JSON status (moved to /status so /docs still works and / serves the PWA)
# ---------------------------------------------------------------------------
@app.get("/status")
def status():
    return {
        "name": "SWARMZ Runtime",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "dashboard": "/dashboard"
    }


@app.on_event("startup")
def on_startup():
    from addons.schema_version import run_migrations
    run_migrations()

@app.get("/health")
def health_check():
    return get_engine().get_health()

@app.get("/v1/health")
def health_check_v1():
    return get_engine().get_health()


# ---------------------------------------------------------------------------
# Auto-start loop when AUTO=1 environment variable is set
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def _maybe_auto_start():
    if os.environ.get("AUTO", "0") == "1":
        interval = int(os.environ.get("TICK_INTERVAL", "30"))
        from swarmz_runtime.api.ecosystem import _get_loop
        _get_loop().start(interval)
