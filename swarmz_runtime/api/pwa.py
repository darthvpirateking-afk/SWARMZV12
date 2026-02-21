# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""PWA app-shell, manifest, service worker, and icon endpoints."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response, FileResponse

router = APIRouter(tags=["pwa"])


def _file_in_ui(filename: str) -> Path:
    return Path("ui") / filename


# ---------------------------------------------------------------------------
# PWA app-shell
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
 <a class="card" href="/app"><h2>Cockpit</h2><p>Full operator cockpit UI</p></a>
 <a class="card" href="/docs"><h2>API Docs</h2><p>Interactive Swagger UI</p></a>
 <a class="card" href="/health"><h2>Health</h2><p>Service health check</p></a>
 <a class="card" href="/v1/missions/list"><h2>Missions</h2><p>List active missions</p></a>
 <a class="card" href="/v1/system/omens"><h2>System Omens</h2><p>Current system signals</p></a>
</div>
<footer>Tip&nbsp;&bull; Open this page on your phone and tap <em>Add to Home Screen</em> for an app icon.</footer>
<script>
if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js');}
</script>
</body>
</html>
"""

_ICON_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<rect width="100" height="100" rx="20" fill="#0d1117"/>
<text x="50" y="68" font-size="52" text-anchor="middle" fill="#58a6ff">&#x1F41D;</text>
</svg>"""

_APPLE_TOUCH_ICON_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 180">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="180" height="180" fill="url(#grad)"/>
  <text x="90" y="120" font-family="Arial, sans-serif" font-size="90" font-weight="bold"
        text-anchor="middle" fill="#ffffff">&#x26A1;</text>
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
  if (url.pathname.startsWith('/v1/') || url.pathname.startsWith('/docs/openapi')
      || url.pathname === '/openapi.json') {
    e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
    return;
  }
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
"""


@router.get("/", response_class=HTMLResponse)
def root():
    """PWA app-shell at root."""
    return _PWA_SHELL


@router.get("/console", response_class=HTMLResponse)
def console_page():
    """Legacy console redirect — serve the PWA shell."""
    return _PWA_SHELL


@router.get("/manifest.webmanifest")
def manifest():
    return Response(content=_MANIFEST, media_type="application/manifest+json")


@router.get("/pwa/manifest.json")
def pwa_manifest():
    """Phone-mode manifest alias."""
    return Response(content=_MANIFEST, media_type="application/manifest+json")


@router.get("/sw.js")
def service_worker():
    sw_file = _file_in_ui("sw.js")
    if sw_file.exists():
        return FileResponse(sw_file, media_type="application/javascript")
    return HTMLResponse(content=_SW_JS, media_type="application/javascript")


@router.head("/sw.js")
def service_worker_head():
    sw_file = _file_in_ui("sw.js")
    if sw_file.exists():
        return FileResponse(sw_file, media_type="application/javascript")
    return HTMLResponse(content=_SW_JS, media_type="application/javascript")


@router.get("/pwa/sw.js")
def pwa_service_worker():
    """Phone-mode service worker alias."""
    return HTMLResponse(content=_SW_JS, media_type="application/javascript")


@router.get("/icon.svg")
def icon_svg():
    return HTMLResponse(content=_ICON_SVG, media_type="image/svg+xml")


@router.get("/apple-touch-icon.svg")
def apple_touch_icon():
    return HTMLResponse(content=_APPLE_TOUCH_ICON_SVG, media_type="image/svg+xml")


@router.get("/styles.css")
def styles_file():
    f = _file_in_ui("styles.css")
    if f.exists():
        return FileResponse(f, media_type="text/css")
    raise HTTPException(status_code=404, detail="styles not found")


@router.head("/styles.css")
def styles_head():
    f = _file_in_ui("styles.css")
    if f.exists():
        return FileResponse(f, media_type="text/css")
    raise HTTPException(status_code=404, detail="styles not found")


@router.get("/app.js")
def app_js_file():
    f = _file_in_ui("app.js")
    if f.exists():
        return FileResponse(f, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="app bundle not found")


@router.head("/app.js")
def app_js_head():
    f = _file_in_ui("app.js")
    if f.exists():
        return FileResponse(f, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="app bundle not found")


@router.get("/icons/{icon_name}")
def icon_file(icon_name: str):
    f = _file_in_ui("icons") / icon_name
    if f.exists():
        return FileResponse(f)
    raise HTTPException(status_code=404, detail="icon not found")


@router.get("/arena", response_class=HTMLResponse)
def arena_page():
    return """
        <!doctype html>
        <html>
            <head><title>SWARMZ Arena</title></head>
            <body>
                <h1>SWARMZ Arena</h1>
            </body>
        </html>
    """
