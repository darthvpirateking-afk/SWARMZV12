# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Interactive web UI for SWARMZ â€” serves a single-page application
that lets operators browse capabilities, execute tasks, and view
the audit log directly from a browser.

API endpoints (JSON):
    GET  /ui/api/capabilities  â€” list registered tasks
    POST /ui/api/execute       â€” run a task by name with JSON params
    GET  /ui/api/audit         â€” return the audit log
    GET  /ui/api/info          â€” system information

HTML UI:
    GET  /ui                   â€” interactive operator console
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel


from fastapi import Request, Depends

def get_orchestrator(request: Request):
  return getattr(request.app.state, "orchestrator", None)

logger = logging.getLogger(__name__)

router = APIRouter()
_FALLBACK_CORE = None


def _get_fallback_core():
  global _FALLBACK_CORE
  if _FALLBACK_CORE is not None:
    return _FALLBACK_CORE
  try:
    from swarmz import SwarmzCore
    _FALLBACK_CORE = SwarmzCore()
  except Exception:
    _FALLBACK_CORE = None
  return _FALLBACK_CORE


# ---------------------------------------------------------------------------
# Dependency-based SwarmzCore access via orchestrator
# ---------------------------------------------------------------------------
def _get_core(orchestrator=Depends(get_orchestrator)):
  if orchestrator and hasattr(orchestrator, "core"):
    return orchestrator.core
  return _get_fallback_core()


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------
class ExecuteRequest(BaseModel):
    task: str
    params: Dict[str, Any] = {}



@router.get("/ui/api/capabilities")
def api_capabilities(core=Depends(_get_core)):
  if not core:
    return JSONResponse({"capabilities": []})
  return JSONResponse({"capabilities": core.list_capabilities()})



@router.post("/ui/api/execute")
def api_execute(req: ExecuteRequest, core=Depends(_get_core)):
  if not core:
    return JSONResponse({"ok": False, "error": "Core unavailable"}, status_code=500)
  try:
    result = core.execute(req.task, **req.params)
    return JSONResponse({"ok": True, "result": result})
  except Exception as exc:
    return JSONResponse(
      {"ok": False, "error": str(exc)},
      status_code=400,
    )



@router.get("/ui/api/audit")
def api_audit(core=Depends(_get_core)):
  if not core:
    return JSONResponse({"audit": []})
  return JSONResponse({"audit": core.get_audit_log()})



@router.get("/ui/api/info")
def api_info(core=Depends(_get_core)):
  if not core:
    return JSONResponse({"info": {}})
  try:
    info = core.execute("system_info")
  except Exception:
    info = {}
  return JSONResponse({"info": info})


# ---------------------------------------------------------------------------
# HTML interface
# ---------------------------------------------------------------------------
_UI_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SWARMZ â€” Operator Console</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  background:#0d1117;color:#c9d1d9;padding:1rem;max-width:900px;margin:auto}
h1{font-size:1.6rem;color:#58a6ff;margin-bottom:.25rem}
.subtitle{font-size:.85rem;color:#8b949e;margin-bottom:1.25rem}
h2{font-size:1.1rem;color:#58a6ff;margin:1.25rem 0 .5rem;border-bottom:1px solid #21262d;padding-bottom:.35rem}
/* Info bar */
.info-bar{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:1rem}
.info-chip{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:.4rem .75rem;font-size:.8rem}
.info-chip b{color:#58a6ff}
/* Capabilities list */
.cap-grid{display:grid;gap:.5rem;grid-template-columns:repeat(auto-fill,minmax(260px,1fr))}
.cap-card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:.7rem .85rem;cursor:pointer;transition:border-color .15s}
.cap-card:hover,.cap-card.selected{border-color:#58a6ff}
.cap-card .name{font-weight:600;color:#e6edf3;font-size:.9rem}
.cap-card .desc{font-size:.78rem;color:#8b949e;margin-top:.15rem}
.cap-card .params{font-size:.72rem;color:#7d8590;margin-top:.25rem;font-family:monospace}
/* Execute panel */
.exec-panel{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1rem;margin-top:.5rem}
.exec-panel label{font-size:.85rem;color:#8b949e;display:block;margin-bottom:.3rem}
.exec-panel input,.exec-panel textarea{width:100%;background:#0d1117;color:#c9d1d9;border:1px solid #30363d;
  border-radius:6px;padding:.5rem .65rem;font-family:monospace;font-size:.85rem;margin-bottom:.6rem}
.exec-panel textarea{resize:vertical;min-height:60px}
.exec-panel input:focus,.exec-panel textarea:focus{outline:none;border-color:#58a6ff}
.btn{display:inline-block;padding:.5rem 1.1rem;border-radius:6px;border:none;font-weight:600;
  font-size:.85rem;cursor:pointer;transition:opacity .15s}
.btn:active{opacity:.7}
.btn-primary{background:#238636;color:#fff}
.btn-secondary{background:#21262d;color:#c9d1d9;border:1px solid #30363d;margin-left:.4rem}
/* Result */
.result-box{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:.6rem .75rem;
  margin-top:.5rem;font-family:monospace;font-size:.82rem;white-space:pre-wrap;max-height:300px;overflow:auto}
.result-box.error{border-color:#f85149;color:#f85149}
.result-box.success{border-color:#238636}
/* Audit table */
.audit-table{width:100%;border-collapse:collapse;font-size:.82rem;margin-top:.4rem}
.audit-table th,.audit-table td{text-align:left;padding:.4rem .55rem;border-bottom:1px solid #21262d}
.audit-table th{color:#8b949e;font-weight:600;background:#161b22;position:sticky;top:0}
.audit-scroll{max-height:320px;overflow:auto;border:1px solid #30363d;border-radius:8px}
.tag{display:inline-block;padding:1px 6px;border-radius:4px;font-size:.72rem;background:#1f6feb33;color:#58a6ff}
footer{margin-top:2rem;font-size:.72rem;color:#484f58;text-align:center}
</style>
</head>
<body>

<h1>&#x1F41D; SWARMZ Operator Console</h1>
<p class="subtitle">Interactive interface &middot; Execute tasks, browse capabilities, inspect audit log</p>

<!-- System Info -->
<div class="info-bar" id="info-bar"><span class="info-chip">Loading&hellip;</span></div>

<!-- Capabilities -->
<h2>Available Capabilities</h2>
<div class="cap-grid" id="cap-grid"></div>

<!-- Execute -->
<h2>Execute Task</h2>
<div class="exec-panel">
  <label for="exec-task">Task name</label>
  <input id="exec-task" placeholder="e.g. echo" autocomplete="off">
  <label for="exec-params">Parameters (JSON)</label>
  <textarea id="exec-params" placeholder='{"message": "Hello"}'></textarea>
  <button class="btn btn-primary" id="exec-btn">&#x25B6; Execute</button>
  <button class="btn btn-secondary" id="clear-btn">Clear</button>
  <div id="exec-result" aria-live="polite"></div>
</div>

<!-- Audit Log -->
<h2>Audit Log <button class="btn btn-secondary" id="refresh-audit" style="font-size:.75rem;padding:.25rem .6rem">&#x21BB; Refresh</button></h2>
<div class="audit-scroll" id="audit-scroll">
  <table class="audit-table">
    <thead><tr><th>#</th><th>Action</th><th>Approved</th></tr></thead>
    <tbody id="audit-body"><tr><td colspan="3">Loading&hellip;</td></tr></tbody>
  </table>
</div>

<footer>SWARMZ &middot; Operator-Sovereign System</footer>

<script>
const API = location.origin;
async function jget(url){const r=await fetch(API+url);return r.json();}
async function jpost(url,body){const r=await fetch(API+url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});return r.json();}

/* --- System Info --- */
async function loadInfo(){
  try{
    const d=await jget('/ui/api/info');
    const bar=document.getElementById('info-bar');
    const i=d.info||{};
    bar.innerHTML=Object.entries(i).map(([k,v])=>`<span class="info-chip"><b>${k}:</b> ${v}</span>`).join('');
  }catch(e){console.error(e);}
}

/* --- Capabilities --- */
let caps={};
async function loadCaps(){
  try{
    const d=await jget('/ui/api/capabilities');
    caps=d.capabilities||{};
    const grid=document.getElementById('cap-grid');
    grid.innerHTML='';
    for(const[name,meta]of Object.entries(caps).sort(([a],[b])=>a.localeCompare(b))){
      const card=document.createElement('div');
      card.className='cap-card';
      card.dataset.name=name;
      const params=meta.params?Object.entries(meta.params).map(([k,v])=>k+': '+v).join(', '):'';
      card.innerHTML=`<div class="name">${name}</div>`
        +(meta.description?`<div class="desc">${meta.description}</div>`:'')
        +(params?`<div class="params">${params}</div>`:'');
      card.onclick=()=>selectTask(name,meta);
      grid.appendChild(card);
    }
  }catch(e){console.error(e);}
}

function selectTask(name,meta){
  document.getElementById('exec-task').value=name;
  const params=meta.params||{};
  const tmpl={};
  for(const k of Object.keys(params)) tmpl[k]='';
  document.getElementById('exec-params').value=Object.keys(params).length?JSON.stringify(tmpl,null,2):'{}';
  document.querySelectorAll('.cap-card').forEach(c=>c.classList.toggle('selected',c.dataset.name===name));
}

/* --- Execute --- */
document.getElementById('exec-btn').onclick=async()=>{
  const task=document.getElementById('exec-task').value.trim();
  if(!task){showResult({ok:false,error:'Please enter a task name'});return;}
  let params={};
  const raw=document.getElementById('exec-params').value.trim();
  if(raw){try{params=JSON.parse(raw);}catch(e){showResult({ok:false,error:'Invalid JSON: '+e.message});return;}}
  const btn=document.getElementById('exec-btn');
  btn.disabled=true;btn.setAttribute('aria-busy','true');btn.textContent='Running\u2026';
  try{
    const d=await jpost('/ui/api/execute',{task,params});
    showResult(d);
    loadAudit();
  }catch(e){showResult({ok:false,error:String(e)});}
  btn.disabled=false;btn.removeAttribute('aria-busy');btn.textContent='\u25B6 Execute';
};

document.getElementById('clear-btn').onclick=()=>{
  document.getElementById('exec-task').value='';
  document.getElementById('exec-params').value='';
  document.getElementById('exec-result').innerHTML='';
  document.querySelectorAll('.cap-card.selected').forEach(c=>c.classList.remove('selected'));
};

function showResult(d){
  const box=document.getElementById('exec-result');
  if(d.ok){
    box.innerHTML=`<div class="result-box success">${JSON.stringify(d.result,null,2)}</div>`;
  }else{
    box.innerHTML=`<div class="result-box error">${d.error||'Unknown error'}</div>`;
  }
}

/* --- Audit Log --- */
async function loadAudit(){
  try{
    const d=await jget('/ui/api/audit');
    const body=document.getElementById('audit-body');
    const entries=d.audit||[];
    if(entries.length===0){body.innerHTML='<tr><td colspan="3" style="color:#8b949e">No entries yet</td></tr>';return;}
    body.innerHTML=entries.map((e,i)=>`<tr><td>${i+1}</td><td>${e.action} <span class="tag">${Object.keys(e.context||{}).join(', ')}</span></td><td>${e.approved?'\u2705':'\u274C'}</td></tr>`).join('');
  }catch(e){console.error(e);}
}
document.getElementById('refresh-audit').onclick=loadAudit;

/* --- Init --- */
loadInfo();loadCaps();loadAudit();
</script>
</body>
</html>
"""


@router.get("/ui", response_class=HTMLResponse)
def ui_page():
    """Serve the interactive operator console."""
    return _UI_HTML

