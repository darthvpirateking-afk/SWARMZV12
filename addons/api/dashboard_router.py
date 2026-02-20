# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Minimal thumb-friendly dashboard â€” serves a small web UI
with missions list, status, costs, pending approvals.

Also provides PWA manifest + service worker for offline caching.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter()

_DASHBOARD_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=yes">
<meta name="theme-color" content="#1a1a2e">
<link rel="manifest" href="/pwa/manifest.json">
<title>SWARMZ Dashboard</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:#1a1a2e;color:#e0e0e0;
  padding:12px;max-width:600px;margin:auto}
h1{font-size:1.4em;margin-bottom:8px;color:#00d4ff}
h2{font-size:1.1em;margin:12px 0 6px;color:#7fdbca}
.card{background:#16213e;border-radius:8px;padding:12px;margin:8px 0;
  border-left:3px solid #00d4ff}
.card.warn{border-left-color:#ff6b6b}
.card.ok{border-left-color:#51cf66}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.8em;margin:2px}
.badge.pending{background:#e67700;color:#fff}
.badge.active{background:#1971c2;color:#fff}
.badge.completed{background:#2b8a3e;color:#fff}
.badge.failed{background:#c92a2a;color:#fff}
.badge.quarantined{background:#862e9c;color:#fff}
.btn{display:inline-block;padding:8px 16px;border-radius:6px;border:none;
  background:#00d4ff;color:#1a1a2e;font-weight:bold;font-size:0.9em;cursor:pointer;
  margin:4px 2px;min-height:44px;min-width:44px}
.btn:active{opacity:0.7}
.btn.danger{background:#ff6b6b}
#status{font-size:0.85em;color:#888;margin:4px 0}
.row{display:flex;flex-wrap:wrap;gap:8px}
.metric{flex:1;min-width:100px;text-align:center;padding:10px;
  background:#16213e;border-radius:8px}
.metric .val{font-size:1.6em;font-weight:bold;color:#00d4ff}
.metric .lbl{font-size:0.75em;color:#888}
ul{list-style:none;padding:0}li{padding:4px 0}
</style>
</head>
<body>
<h1>&#x1F41D; SWARMZ Dashboard</h1>
<div id="status">Loadingâ€¦</div>

<div class="row" id="metrics"></div>

<h2>Missions</h2>
<div id="missions"><em>Loadingâ€¦</em></div>

<h2>Pending Approvals</h2>
<div id="patches"><em>Loadingâ€¦</em></div>

<h2>Budget</h2>
<div id="budget"><em>Loadingâ€¦</em></div>

<h2>Quarantine</h2>
<div id="quarantine"><em>Loadingâ€¦</em></div>

<h2>Quick Actions</h2>
<div>
  <button class="btn" onclick="doExport()">&#x1F4E6; Export Backup</button>
  <button class="btn" onclick="doReplay()">&#x1F504; Replay State</button>
  <button class="btn danger" onclick="location.reload()">&#x21BB; Refresh</button>
</div>
<div id="replay" style="margin-top:8px"></div>

<script>
const API = location.origin;
async function j(url){try{const r=await fetch(API+url);return await r.json()}catch(e){return null}}

async function load(){
  // Health
  const h = await j('/health');
  document.getElementById('status').textContent = h ? `Status: ${h.status} | Active: ${h.active_missions}/${h.max_missions}` : 'Offline';

  // Metrics
  const m = document.getElementById('metrics');
  if(h) m.innerHTML = `
    <div class="metric"><div class="val">${h.active_missions}</div><div class="lbl">Active</div></div>
    <div class="metric"><div class="val">${h.max_missions}</div><div class="lbl">Max</div></div>
    <div class="metric"><div class="val">${h.pattern_counters||0}</div><div class="lbl">Patterns</div></div>`;

  // Missions
  const ml = await j('/v1/missions/list');
  const md = document.getElementById('missions');
  if(ml && ml.missions){
    if(ml.missions.length===0){md.innerHTML='<div class="card ok">No missions yet</div>';} else {
    md.innerHTML = ml.missions.map(m=>`<div class="card">
      <strong>${m.goal||m.id}</strong> <span class="badge ${m.status}">${m.status}</span>
      <br><small>${m.category||''} | ${m.id}</small></div>`).join('');}
  }

  // Patches
  const pl = await j('/v1/addons/patches?status=pending');
  const pd = document.getElementById('patches');
  if(pl && pl.patches){
    if(pl.patches.length===0){pd.innerHTML='<div class="card ok">No pending patches</div>';} else {
    pd.innerHTML = pl.patches.map(p=>`<div class="card warn">
      <strong>${p.description}</strong> <span class="badge pending">pending</span>
      <br><small>${p.patch_id} | ${p.submitted_at||''}</small></div>`).join('');}
  }

  // Budget
  const b = await j('/v1/addons/budget');
  const bd = document.getElementById('budget');
  if(b){bd.innerHTML=`<div class="card"><strong>Spent:</strong> ${b.spent||0} / ${b.hard_cap||'âˆž'} | <strong>Remaining:</strong> ${(b.hard_cap||0)-(b.spent||0)-(b.reserved||0)}</div>`;}

  // Quarantine
  const q = await j('/v1/addons/quarantine');
  const qd = document.getElementById('quarantine');
  if(q){qd.innerHTML = q.quarantined
    ? `<div class="card warn"><span class="badge quarantined">QUARANTINED</span> ${q.reason||''} since ${q.since||''}</div>`
    : `<div class="card ok">System is operational</div>`;}
}

function doExport(){window.open(API+'/v1/addons/backup/export','_blank')}
async function doReplay(){
  const r = await j('/v1/addons/replay');
  document.getElementById('replay').innerHTML = r
    ? `<div class="card"><pre style="white-space:pre-wrap;font-size:0.8em">${JSON.stringify(r,null,2)}</pre></div>`
    : '<div class="card warn">Replay failed</div>';
}

load();
if('serviceWorker' in navigator){navigator.serviceWorker.register('/pwa/sw.js').catch(()=>{});}
</script>
</body>
</html>
"""

_MANIFEST = {
    "name": "SWARMZ Dashboard",
    "short_name": "SWARMZ",
    "start_url": "/dashboard",
    "display": "standalone",
    "background_color": "#1a1a2e",
    "theme_color": "#1a1a2e",
    "description": "Operator-Sovereign Mission Engine Dashboard",
    "icons": [],
}

_SW_JS = """\
const CACHE = 'swarmz-v1';
const PRECACHE = ['/dashboard'];
self.addEventListener('install', e => e.waitUntil(
  caches.open(CACHE).then(c => c.addAll(PRECACHE)).then(() => self.skipWaiting())
));
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).then(r => {
      const clone = r.clone();
      caches.open(CACHE).then(c => c.put(e.request, clone));
      return r;
    }).catch(() => caches.match(e.request))
  );
});
"""


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return _DASHBOARD_HTML


@router.get("/pwa/manifest.json")
def pwa_manifest():
    return JSONResponse(_MANIFEST)


@router.get("/pwa/sw.js")
def pwa_sw():
    from starlette.responses import Response
    return Response(content=_SW_JS, media_type="application/javascript")

