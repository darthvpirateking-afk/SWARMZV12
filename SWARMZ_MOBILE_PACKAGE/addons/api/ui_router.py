# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Interactive web UI for SWARMZ Ã¢â‚¬â€ serves a single-page application
that lets operators browse capabilities, execute tasks, and view
the audit log directly from a browser.

API endpoints (JSON):
    GET  /ui/api/capabilities  Ã¢â‚¬â€ list registered tasks
    POST /ui/api/execute       Ã¢â‚¬â€ run a task by name with JSON params
    GET  /ui/api/audit         Ã¢â‚¬â€ return the audit log
    GET  /ui/api/info          Ã¢â‚¬â€ system information

HTML UI:
    GET  /ui                   Ã¢â‚¬â€ interactive operator console
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


def _select_self_name_from_presence(
  presence: Dict[str, Any], avoid_pattern: bool = False
) -> str:
  if avoid_pattern:
    return "Vesper"
  style = presence.get("style", {})
  context = presence.get("context", {})
  realm = str(context.get("realm", "COSMOS")).upper()
  form = str(context.get("form", "CORE")).upper()
  intensity = str(style.get("intensity", "medium-high")).lower()
  if realm == "COSMOS" and form == "CORE":
    return "AstraCore Regent"
  if "high" in intensity:
    return "Sovereign Vector"
  return "Master Swarmz Prime"


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


def _build_presence_bundle() -> Dict[str, Any]:
  from swarmz_runtime.core.form_evolution_map import FormEvolutionMap
  from swarmz_runtime.core.persona_layer import (
    Form,
    MissionRank,
    PersonaContext,
    PersonaLayer,
    Realm,
    SwarmTier,
  )
  from swarmz_runtime.core.presence_engine import PresenceConfig, PresenceEngine
  from swarmz_runtime.core.realm_tone_matrix import RealmToneMatrix
  from swarmz_runtime.core.swarm_behavior_model import SwarmBehaviorModel
  from swarmz_runtime.core.throne_governance import ThroneGovernance

  realm_matrix = RealmToneMatrix()
  form_map = FormEvolutionMap()
  swarm_model = SwarmBehaviorModel()
  throne = ThroneGovernance(operator_id="regan")

  persona_layer = PersonaLayer(realm_matrix, form_map, swarm_model)
  presence_engine = PresenceEngine(persona_layer, throne, PresenceConfig())

  ctx = PersonaContext(
    realm=Realm.COSMOS,
    form=Form.CORE,
    mission_rank=MissionRank.S,
    swarm_tier=SwarmTier.T3,
  )
  style = presence_engine.render_style(ctx)

  return {
    "context": {
      "realm": ctx.realm.value,
      "form": ctx.form.value,
      "mission_rank": ctx.mission_rank.value,
      "swarm_tier": ctx.swarm_tier.value,
    },
    "style": {
      "tone": style.tone,
      "metaphor_level": style.metaphor_level,
      "density": style.density,
      "formality": style.formality,
      "pacing": style.pacing,
      "intensity": style.intensity,
    },
    "constraints": throne.describe_constraints(),
    "presence_engine": presence_engine,
    "style_obj": style,
  }


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
# Enhanced Companion Chat Endpoint
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str


@router.post("/ui/api/companion/chat")
def api_companion_chat(req: ChatRequest):
    """Enhanced SWARMZ companion chat with sophisticated personality"""
    try:
        from core.companion import chat
        from core.companion_master import rename_master

        presence = _build_presence_bundle()
        message_lower = req.message.lower()
        asks_name_decision = (
            "name" in message_lower
            and (
                "decide" in message_lower
                or "choose" in message_lower
                or "regan asked" in message_lower
                or "what would you like to be called" in message_lower
            )
        )
        asks_better_non_pattern_name = (
            "better" in message_lower
            and ("not pattern" in message_lower or "non pattern" in message_lower)
        )

        if asks_name_decision or asks_better_non_pattern_name:
            chosen_name = _select_self_name_from_presence(
                presence, avoid_pattern=asks_better_non_pattern_name
            )
            rename_master(chosen_name)
            if asks_better_non_pattern_name:
                reply = (
                    f"Regan asked for something better and not pattern-based. "
                    f"I choose: {chosen_name}."
                )
            else:
                reply = (
                    f"Regan asked me to decide, and I choose this name: {chosen_name}. "
                    "I accept this designation."
                )
            constrained_reply = presence["presence_engine"].apply_constraints(
                reply, presence["style_obj"]
            )
            return JSONResponse(
                {
                    "ok": True,
                    "reply": constrained_reply,
                    "raw_reply": reply,
                    "source": "name_decision",
                    "personality_active": True,
                    "display_name": chosen_name,
                    "presence_context": presence["context"],
                    "presence_style": presence["style"],
                    "constraints": presence["constraints"],
                }
            )

        result = chat(req.message)
        reply = result.get("reply", "I'm processing that...")
        constrained_reply = presence["presence_engine"].apply_constraints(
            reply, presence["style_obj"]
        )
        return JSONResponse(
            {
                "ok": True,
                "reply": constrained_reply,
                "raw_reply": reply,
                "source": result.get("source", "Enhanced Companion"),
                "personality_active": True,
                "presence_context": presence["context"],
                "presence_style": presence["style"],
                "constraints": presence["constraints"],
            }
        )
    except Exception as exc:
        return JSONResponse(
            {
                "ok": False,
                "error": str(exc),
                "reply": "I'm having trouble accessing my enhanced systems right now.",
                "personality_active": False,
            },
            status_code=500,
        )

class _RenameRequest(BaseModel):
    name: str


@router.post("/ui/api/companion/rename")
def api_companion_rename(body: _RenameRequest):
    """Set a new display name for the companion. Persists to companion_master.json."""
    try:
        from core.companion_master import rename_master
        updated = rename_master(body.name)
        return JSONResponse({"ok": True, "display_name": updated.get("display_name", body.name)})
    except Exception as exc:
        logger.warning("rename_master failed: %s", exc)
        return JSONResponse({"ok": False, "display_name": body.name, "error": str(exc)}, status_code=500)

@router.get("/ui/api/companion/presence")
def api_companion_presence():
    """Get current derived persona context and expression profile."""
    presence = _build_presence_bundle()
    return JSONResponse(
        {
            "ok": True,
            "context": presence["context"],
            "style": presence["style"],
            "constraints": presence["constraints"],
        }
    )


@router.get("/ui/api/companion/avatar")
def api_companion_avatar():
    """Get avatar appearance data for enhanced SWARMZ"""
    presence = _build_presence_bundle()
    try:
        from core.companion_master import get_display_name
        display_name = get_display_name()
    except Exception:
        display_name = "MASTER SWARMZ"
    return JSONResponse(
        {
            "display_name": display_name,
            "appearance": {
                "form": "cybernetic_humanoid",
                "body_color": "matte_black",
                "circuit_color": "electric_blue",
                "core_color": "golden_energy",
                "crown_fragments": True,
                "height": "ethereal_tall",
              "mode": "focused",
            },
            "personality_traits": [
              "governed",
              "deterministic",
              "doctrine_aligned",
                "technically_advanced",
              "operator_controlled",
            ],
            "presence_context": presence["context"],
            "presence_style": presence["style"],
            "constraints": presence["constraints"],
        }
    )


# ---------------------------------------------------------------------------
# HTML interface
# ---------------------------------------------------------------------------
_UI_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SWARMZ Ã¢â‚¬â€ Operator Console</title>
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
  btn.disabled=false;btn.removeAttribute('aria-busy');btn.textContent='\u25b6 Execute';
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
    body.innerHTML=entries.map((e,i)=>`<tr><td>${i+1}</td><td>${e.action} <span class="tag">${Object.keys(e.context||{}).join(', ')}</span></td><td>${e.approved?'\u2705':'\u274c'}</td></tr>`).join('');
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
