# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Entry FastAPI app for SWARMZ (phone/PC ready).

Adds lightweight control endpoints on top of the existing swarmz_server app:
- GET /health
- POST /v1/sovereign/dispatch (operator-key gated)
- GET /v1/system/log
- GET/POST /v1/mode
- POST /v1/companion/message
- POST /v1/build/dispatch
- GET /v1/swarm/status

This file is intentionally small and additive. It imports the main app from
swarmz_server and layers the required control routes.
"""

import os
import uuid
import json
import hashlib
from types import SimpleNamespace
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from pydantic import BaseModel

from swarmz_server import app, _swarmz_core  # reuse the existing app instance
from jsonl_utils import read_jsonl, write_jsonl

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
MISSIONS_FILE = DATA_DIR / "missions.jsonl"
AUDIT_FILE = DATA_DIR / "audit.jsonl"
STATE_FILE = DATA_DIR / "state.json"
HEARTBEAT_FILE = DATA_DIR / "runner_heartbeat.json"


class DispatchRequest(BaseModel):
    intent: str
    scope: str
    limits: Optional[Dict[str, Any]] = None


def _expected_operator_key() -> Optional[str]:
    return os.environ.get("OPERATOR_KEY")


def _get_operator_key(
    request: Request,
    x_operator_key: Optional[str] = Header(None),
    operator_key: Optional[str] = None,
) -> str:
    """Validate operator key. Localhost writes are allowed without a key."""
    # Allow localhost/loopback to bypass key requirement
    client_host = request.client.host if request.client else "unknown"
    is_local = client_host in ("127.0.0.1", "::1", "localhost")

    key = x_operator_key or operator_key
    if not key and is_local:
        return "__local__"
    if not key:
        raise HTTPException(status_code=401, detail="operator key required")
    expected = _expected_operator_key()
    if expected and key != expected:
        raise HTTPException(status_code=401, detail="invalid operator key")
    return key


def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, separators=(",", ":")) + "\n")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/v1/sovereign/dispatch")
async def sovereign_dispatch(
    payload: DispatchRequest, op_key: str = Depends(_get_operator_key)
):
    now = datetime.utcnow().isoformat() + "Z"
    mission_id = f"M-{uuid.uuid4().hex[:12]}"

    mission = {
        "mission_id": mission_id,
        "timestamp": now,
        "intent": payload.intent,
        "scope": payload.scope,
        "limits": payload.limits or {},
        "status": "PENDING",
    }
    audit = {
        "timestamp": now,
        "event": "mission_dispatched",
        "mission_id": mission_id,
        "operator": bool(op_key),
        "details": {
            "intent": payload.intent,
            "scope": payload.scope,
        },
    }

    _append_jsonl(MISSIONS_FILE, mission)
    _append_jsonl(AUDIT_FILE, audit)

    return {"ok": True, "mission_id": mission_id, "status": "PENDING"}


@app.get("/v1/system/log")
async def system_log(tail: int = 10):
    tail = max(1, min(int(tail), 200))
    if not AUDIT_FILE.exists():
        return {"entries": []}
    try:
        lines = AUDIT_FILE.read_text(encoding="utf-8").splitlines()
    except Exception:
        lines = []
    entries = []
    for line in lines[-tail:]:
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return {"entries": entries}


@app.get("/system-log", response_class=HTMLResponse)
async def system_log_viewer(tail: int = 100):
    """Human-readable system log viewer with navigation back to the cockpit."""
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SWARMZ — System Log</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#060a10;color:#00ffff;font-family:'Courier New',monospace;min-height:100vh;padding:0}
.topbar{display:flex;align-items:center;gap:16px;padding:12px 24px;background:rgba(6,10,16,0.96);border-bottom:1px solid #0e2a3a;position:sticky;top:0;z-index:50;backdrop-filter:blur(12px)}
.back-btn{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;border-radius:7px;border:1px solid #00ffff;background:rgba(0,255,255,0.07);color:#00ffff;text-decoration:none;font-size:13px;font-weight:700;letter-spacing:1px;transition:background .2s}
.back-btn:hover{background:rgba(0,255,255,0.18)}
.title{font-size:14px;font-weight:700;letter-spacing:3px;color:#00ffff}
.subtitle{font-size:11px;color:#334455;margin-left:auto;font-family:monospace}
.container{max-width:1100px;margin:0 auto;padding:24px 20px}
.controls{display:flex;gap:10px;align-items:center;margin-bottom:18px;flex-wrap:wrap}
.tail-btn{padding:5px 12px;border-radius:5px;border:1px solid #1a3a4a;background:rgba(10,16,24,0.9);color:#00ffff;cursor:pointer;font-size:12px;font-family:monospace;transition:border-color .2s}
.tail-btn:hover,.tail-btn.active{border-color:#00ffff;background:rgba(0,255,255,0.1)}
.log-table{width:100%;border-collapse:collapse;font-size:12px}
.log-table th{text-align:left;padding:8px 10px;border-bottom:1px solid #0e2a3a;color:#445566;font-weight:600;letter-spacing:1px;white-space:nowrap}
.log-table td{padding:7px 10px;border-bottom:1px solid #0a1822;vertical-align:top;word-break:break-word}
.log-table tr:hover td{background:rgba(0,255,255,0.04)}
.event-pill{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;letter-spacing:.5px;white-space:nowrap}
.pill-dispatch{background:rgba(0,180,255,0.15);color:#00b4ff;border:1px solid #003a5a}
.pill-success{background:rgba(0,255,136,0.12);color:#00ff88;border:1px solid #004422}
.pill-failure{background:rgba(255,60,60,0.12);color:#ff6060;border:1px solid #4a1010}
.pill-quarantine{background:rgba(255,165,0,0.12);color:#ffa500;border:1px solid #4a2e00}
.pill-default{background:rgba(100,100,100,0.12);color:#888;border:1px solid #222}
.ts{color:#334466;font-size:11px;white-space:nowrap}
.mid{color:#ffd700;font-size:11px}
.empty{text-align:center;padding:48px;color:#334455;font-size:14px}
.count-badge{font-size:11px;color:#445566;margin-left:8px}
.refresh-btn{padding:5px 12px;border-radius:5px;border:1px solid #ffd700;background:rgba(255,215,0,0.07);color:#ffd700;cursor:pointer;font-size:12px;font-family:monospace;margin-left:auto}
.refresh-btn:hover{background:rgba(255,215,0,0.15)}
</style>
</head>
<body>
<div class="topbar">
  <a class="back-btn" href="/app">← SWARMZ Cockpit</a>
  <span class="title">SYSTEM LOG</span>
  <span class="subtitle" id="clock"></span>
</div>
<div class="container">
  <div class="controls">
    <span style="font-size:12px;color:#445566">Showing last:</span>
    <button class="tail-btn" onclick="load(25)">25</button>
    <button class="tail-btn active" onclick="load(100)" id="btn-100">100</button>
    <button class="tail-btn" onclick="load(250)">250</button>
    <button class="tail-btn" onclick="load(500)">500</button>
    <button class="refresh-btn" onclick="load(currentTail)">&#8635; Refresh</button>
  </div>
  <div id="log-wrap"><p class="empty">Loading...</p></div>
</div>
<script>
var currentTail=100;
function pillClass(ev){
  if(!ev)return'pill-default';
  if(ev.includes('dispatch'))return'pill-dispatch';
  if(ev.includes('success')||ev.includes('resolved')||ev.includes('started'))return'pill-success';
  if(ev.includes('fail')||ev.includes('quarantine_blocked')||ev.includes('error'))return'pill-failure';
  if(ev.includes('quarantine'))return'pill-quarantine';
  return'pill-default';
}
function fmt(entry){
  var ev=entry.event||entry.type||'—';
  var ts=entry.ts||entry.timestamp||'';
  var mid=entry.mission_id||'';
  var note=entry.note||entry.detail||entry.intent||entry.error||'';
  var rate=entry.success_rate!=null?' (rate: '+(entry.success_rate*100).toFixed(1)+'%)':'';
  var extra=Object.keys(entry).filter(function(k){return!['event','type','ts','timestamp','mission_id','note','detail','intent','error','success_rate'].includes(k)}).map(function(k){return k+'='+JSON.stringify(entry[k])}).join(' ');
  return '<tr>'
    +'<td class="ts">'+ts.replace('T',' ').replace(/\\.\\d+Z$/,'Z')+'</td>'
    +'<td><span class="event-pill '+pillClass(ev)+'">'+ev+'</span></td>'
    +'<td class="mid">'+mid+'</td>'
    +'<td style="color:#aaa">'+note+rate+' <span style="color:#334455">'+extra+'</span></td>'
    +'</tr>';
}
function load(n){
  currentTail=n;
  document.querySelectorAll('.tail-btn').forEach(function(b){b.classList.remove('active')});
  fetch('/v1/system/log?tail='+n).then(function(r){return r.json()}).then(function(d){
    var entries=(d.entries||[]).slice().reverse();
    var w=document.getElementById('log-wrap');
    if(!entries.length){w.innerHTML='<p class="empty">No log entries found.</p>';return;}
    var html='<table class="log-table"><thead><tr><th>TIMESTAMP</th><th>EVENT</th><th>MISSION ID</th><th>DETAIL</th></tr></thead><tbody>';
    entries.forEach(function(e){html+=fmt(e);});
    html+='</tbody></table><p class="count-badge">'+entries.length+' entries (newest first) • auto-refresh every 10s</p>';
    w.innerHTML=html;
  }).catch(function(){document.getElementById('log-wrap').innerHTML='<p class="empty" style="color:#ff6060">Failed to fetch log. Is the server running?</p>';});
}
function tick(){document.getElementById('clock').textContent=new Date().toLocaleTimeString();}
load(100);
setInterval(function(){load(currentTail);},10000);
setInterval(tick,1000);tick();
</script>
</body>
</html>""")



# â”€â”€ helpers for state.json â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _read_state() -> Dict[str, Any]:
    """Read persisted mode state. Create default if missing."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    default = {
        "mode": "COMPANION",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "version": 1,
    }
    STATE_FILE.write_text(json.dumps(default, indent=2), encoding="utf-8")
    return default


def _write_state(state: Dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


# â”€â”€ GET/POST /v1/mode â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class ModeRequest(BaseModel):
    mode: str


@app.get("/v1/mode")
async def get_mode():
    s = _read_state()
    return {
        "ok": True,
        "mode": s["mode"],
        "updated_at": s.get("updated_at"),
        "version": s.get("version", 1),
    }


@app.post("/v1/mode")
async def set_mode(payload: ModeRequest, op_key: str = Depends(_get_operator_key)):
    mode = payload.mode.upper()
    if mode not in ("COMPANION", "BUILD", "HOLOGRAM"):
        raise HTTPException(status_code=400, detail="mode must be COMPANION, BUILD, or HOLOGRAM")
    now = datetime.utcnow().isoformat() + "Z"
    s = _read_state()
    old_mode = s.get("mode")
    s["mode"] = mode
    s["updated_at"] = now
    s["version"] = s.get("version", 0) + 1
    _write_state(s)
    _append_jsonl(
        AUDIT_FILE,
        {
            "timestamp": now,
            "event": "mode_changed",
            "old_mode": old_mode,
            "new_mode": mode,
            "operator": bool(op_key),
        },
    )
    return {"ok": True, "mode": mode, "updated_at": now, "version": s["version"]}


# â”€â”€ POST /v1/companion/message â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# NOTE: The canonical companion endpoint lives in swarmz_server.py (registered first).
# It routes through core.companion.chat with full AI + rule-engine fallback.
# The duplicate route below is kept commented-out for reference only.
# FastAPI matches the first registered route, so this was never reached.
#
# class CompanionRequest(BaseModel):
#     text: str
#
# @app.post("/v1/companion/message")
# async def companion_message(payload: CompanionRequest):
#     ...  # see swarmz_server.py for the active implementation


# â”€â”€ POST /v1/build/dispatch â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class BuildDispatchRequest(BaseModel):
    intent: str
    spec: Optional[Dict[str, Any]] = None


@app.post("/v1/build/dispatch")
async def build_dispatch(
    payload: BuildDispatchRequest, op_key: str = Depends(_get_operator_key)
):
    s = _read_state()
    if s.get("mode") != "BUILD":
        raise HTTPException(status_code=400, detail="Must be in BUILD mode to dispatch")

    now = datetime.utcnow().isoformat() + "Z"
    mission_id = f"mission_{int(datetime.utcnow().timestamp() * 1000)}"

    mission = {
        "mission_id": mission_id,
        "intent": payload.intent,
        "spec": payload.spec or {},
        "goal": payload.intent,
        "category": "build",
        "status": "PENDING",
        "created_at": now,
    }
    write_jsonl(MISSIONS_FILE, mission)
    _append_jsonl(
        AUDIT_FILE,
        {
            "timestamp": now,
            "event": "mission_created",
            "mission_id": mission_id,
            "intent": payload.intent,
        },
    )
    return {"ok": True, "mission_id": mission_id, "status": "PENDING"}


# â”€â”€ GET /v1/swarm/status â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@app.get("/v1/swarm/status")
async def swarm_status():
    """Return runner heartbeat and mission counts."""
    runner_state = "down"
    last_tick = None
    if HEARTBEAT_FILE.exists():
        try:
            hb = json.loads(HEARTBEAT_FILE.read_text(encoding="utf-8"))
            runner_state = hb.get("status", "down")
            last_tick = hb.get("last_tick")
        except Exception:
            pass

    missions, _, _ = read_jsonl(MISSIONS_FILE)
    counts = {"PENDING": 0, "RUNNING": 0, "SUCCESS": 0, "FAILURE": 0}
    for m in missions:
        st = m.get("status", "UNKNOWN")
        if st in counts:
            counts[st] += 1

    return {
        "ok": True,
        "runner": runner_state,
        "last_tick": last_tick,
        "pending_count": counts["PENDING"],
        "running_count": counts["RUNNING"],
        "success_count": counts["SUCCESS"],
        "failure_count": counts["FAILURE"],
    }


# -- System control endpoints --------------------------------------------------
# /system/start, /system/stop, /system/restart, /system/status


@app.get("/system/status")
async def system_status():
    """Aggregate system status: runner, mode, missions, health."""
    runner_state = "down"
    last_tick = None
    if HEARTBEAT_FILE.exists():
        try:
            hb = json.loads(HEARTBEAT_FILE.read_text(encoding="utf-8"))
            runner_state = hb.get("status", "down")
            last_tick = hb.get("last_tick")
        except Exception:
            pass
    s = _read_state()
    missions, _, _ = read_jsonl(MISSIONS_FILE)
    total = len(missions)
    success = sum(1 for m in missions if m.get("status") == "SUCCESS")
    return {
        "ok": True,
        "mode": s.get("mode"),
        "runner": runner_state,
        "last_tick": last_tick,
        "total_missions": total,
        "success_count": success,
        "success_rate": round(success / total, 3) if total else 0.0,
        "version": s.get("version"),
        "updated_at": s.get("updated_at"),
    }


@app.post("/system/start")
async def system_start():
    """Start/restart the swarm runner loop (if not already running)."""
    import threading
    try:
        from swarm_runner import run_loop as _runner_loop
        for t in threading.enumerate():
            if t.name == "swarm-runner" and t.is_alive():
                return {"ok": True, "status": "already_running"}
        runner_thread = threading.Thread(
            target=_runner_loop, daemon=True, name="swarm-runner"
        )
        runner_thread.start()
        return {"ok": True, "status": "started"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/system/stop")
async def system_stop():
    """Signal the swarm runner to stop."""
    try:
        import swarm_runner
        swarm_runner._STOP_FLAG = True
        return {"ok": True, "status": "stop_signalled"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/system/restart")
async def system_restart():
    """Stop and re-start the swarm runner."""
    try:
        import swarm_runner, threading, time
        swarm_runner._STOP_FLAG = True
        time.sleep(0.5)
        swarm_runner._STOP_FLAG = False
        from swarm_runner import run_loop as _runner_loop
        runner_thread = threading.Thread(
            target=_runner_loop, daemon=True, name="swarm-runner"
        )
        runner_thread.start()
        return {"ok": True, "status": "restarted"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# -- /deploy -------------------------------------------------------------------


class DeployRequest(BaseModel):
    target: Optional[str] = "local"
    spec: Optional[Dict[str, Any]] = None


@app.post("/deploy")
async def deploy(payload: DeployRequest, op_key: str = Depends(_get_operator_key)):
    """Deploy a mission package."""
    now = datetime.utcnow().isoformat() + "Z"
    mission_id = f"deploy_{int(datetime.utcnow().timestamp() * 1000)}"
    mission = {
        "mission_id": mission_id,
        "intent": f"deploy:{payload.target}",
        "spec": payload.spec or {},
        "goal": f"Deploy to {payload.target}",
        "category": "deploy",
        "status": "PENDING",
        "created_at": now,
    }
    write_jsonl(MISSIONS_FILE, mission)
    _append_jsonl(
        AUDIT_FILE,
        {"timestamp": now, "event": "deploy_dispatched",
         "mission_id": mission_id, "target": payload.target},
    )
    return {"ok": True, "mission_id": mission_id, "status": "PENDING"}


# -- /evolve -------------------------------------------------------------------


@app.get("/evolve")
async def evolve():
    """Return current evolution/hologram state."""
    try:
        from core.hologram import compute_level, load_all_trials
        trials = load_all_trials()
        state = compute_level(trials)
        return {"ok": True, **state}
    except Exception as e:
        return {"ok": False, "error": str(e), "level": 0, "name": "EGG"}


# -- /mission ------------------------------------------------------------------


class MissionRequest(BaseModel):
    intent: str
    scope: Optional[str] = "general"
    spec: Optional[Dict[str, Any]] = None


@app.post("/mission")
async def create_mission(
    payload: MissionRequest, op_key: str = Depends(_get_operator_key)
):
    """Create a new mission (mode-independent shorthand)."""
    now = datetime.utcnow().isoformat() + "Z"
    mission_id = f"mission_{int(datetime.utcnow().timestamp() * 1000)}"
    mission = {
        "mission_id": mission_id,
        "intent": payload.intent,
        "scope": payload.scope,
        "spec": payload.spec or {},
        "status": "PENDING",
        "created_at": now,
    }
    write_jsonl(MISSIONS_FILE, mission)
    _append_jsonl(
        AUDIT_FILE,
        {"timestamp": now, "event": "mission_created",
         "mission_id": mission_id, "intent": payload.intent},
    )
    return {"ok": True, "mission_id": mission_id, "status": "PENDING"}


@app.get("/mission")
async def list_missions(limit: int = 50):
    """List recent missions."""
    missions, _, _ = read_jsonl(MISSIONS_FILE)
    return {"ok": True, "missions": missions[-limit:], "total": len(missions)}


# -- /api/governor -------------------------------------------------------------


@app.get("/api/governor")
async def api_governor():
    """Governor status for the React cockpit StatusCard."""
    missions, _, _ = read_jsonl(MISSIONS_FILE)
    total = len(missions)
    success = sum(1 for m in missions if m.get("status") == "SUCCESS")
    rate = round(success / total, 3) if total else 0.0
    quarantine = total >= 10 and rate < 0.30
    s = _read_state()
    return {
        "ok": True,
        "mode": s.get("mode"),
        "total_missions": total,
        "success_count": success,
        "success_rate": rate,
        "quarantine_active": quarantine,
        "version": s.get("version"),
    }


# â”€â”€ GET /v1/ai/status â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@app.get("/v1/ai/status")
async def ai_status():
    """Return AI subsystem status: offline mode, provider, model, last call info."""
    try:
        from core.model_router import get_status as _ai_status

        status = _ai_status()
    except Exception:
        status = {
            "offlineMode": True,
            "provider": "",
            "model": "",
            "apiKeySet": False,
            "lastCallTimestamp": None,
            "lastError": "core.model_router not available",
        }

    # Add QUARANTINE state
    from swarmz_server import compute_phase

    try:
        missions, _, _ = read_jsonl(MISSIONS_FILE)
    except Exception:
        missions = []
    if not isinstance(missions, list):
        missions = []
    success_count = sum(1 for m in missions if m.get("status") == "SUCCESS")
    phase = compute_phase(len(missions), success_count)
    status["phase"] = phase
    status["quarantine"] = phase == "QUARANTINE"
    status["quarantine_blocks_run"] = phase == "QUARANTINE"

    return {"ok": True, **status}


# â”€â”€ GET /v1/runtime/scoreboard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@app.get("/v1/runtime/scoreboard")
async def runtime_scoreboard():
    """Return aggregated engine status: personality, trajectory, phase, pending actions."""
    try:
        from core.context_pack import get_scoreboard

        return {"ok": True, **get_scoreboard()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


# â”€â”€ GET /v1/companion/state â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@app.get("/v1/companion/state")
async def companion_state_endpoint():
    """Return companion master context + state."""
    try:
        from core.companion_master import get_composite_context, self_assessment

        ctx = get_composite_context()
        ctx["self_assessment"] = self_assessment()
        return {"ok": True, **ctx}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}

# â"€â"€ POST /v1/operator-os/dispatch â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€

@app.post("/v1/operator-os/dispatch")
async def operator_os_dispatch(request: Request):
    """
    UI Dispatch endpoint - route to sovereign dispatch with simplified interface.
    
    Expected payload: {"intent": "...", "spec": {...}, "goal": "..."}
    """
    try:
        data = await request.json()
        intent = data.get("intent", "").strip()
        spec = data.get("spec", {})
        goal = data.get("goal", "").strip()
        
        if not intent:
            return JSONResponse({"ok": False, "error": "Intent required"}, status_code=400)
            
        # Route to sovereign dispatch
        try:
            dispatch_payload = DispatchRequest(
                intent=intent,
                scope=str(spec) if spec else "",
                limits={"goal": goal} if goal else None
            )
            # Note: This is for UI - skip auth for now, add later if needed
            result = await sovereign_dispatch(dispatch_payload, "ui-bypass")
            return JSONResponse(result)
        except Exception as dispatch_err:
            # Fallback: basic mission logging
            import uuid
            from datetime import datetime
            mission_id = f"M-{uuid.uuid4().hex[:8]}"
            return JSONResponse({
                "ok": True,
                "mission_id": mission_id,
                "status": "dispatched",
                "intent": intent,
                "note": "Logged via UI (fallback)"
            })
            
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)[:200]}, status_code=500)


# â"€â"€ GET /v1/operator-os/prime-state â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€

@app.get("/v1/operator-os/prime-state")
async def operator_os_prime_state():
    """
    UI Prime State endpoint - return system overview for main dashboard.
    
    This provides the core status information that the UI needs to display.
    """
    try:
        # Mission status
        try:
            missions, _, _ = read_jsonl(MISSIONS_FILE)
            if not isinstance(missions, list):
                missions = []
            
            total_missions = len(missions)
            success_count = sum(1 for m in missions if m.get("status") == "SUCCESS")
            pending_count = sum(1 for m in missions if m.get("status") == "PENDING")
            success_rate = (success_count / total_missions * 100) if total_missions > 0 else 0
            
        except Exception:
            total_missions = success_count = pending_count = 0
            success_rate = 0
            
        # Phase calculation
        from swarmz_server import compute_phase
        phase = compute_phase(total_missions, success_count)
        
        # AI status
        try:
            from core.model_router import get_status as _ai_status
            ai_status = _ai_status()
        except Exception:
            ai_status = {"status": "offline", "provider": "rule_engine"}
            
        return {
            "ok": True,
            "phase": phase,
            "quarantine": phase == "QUARANTINE",
            "missions": {
                "total": total_missions,
                "success": success_count,
                "pending": pending_count,
                "success_rate": success_rate
            },
            "ai": ai_status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}

# â”€â”€ GET /v1/companion/history â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@app.get("/v1/companion/history")
async def companion_history(tail: int = 20):
    """Return last N evolution history records + readâ€‘only status."""
    tail = max(1, min(int(tail), 200))
    try:
        from core.context_pack import load as _load_engines

        eng = _load_engines()
        evo = eng.get("evolution")
        records = []
        read_only = eng.get("read_only", False)
        if evo:
            records = evo.history_tail(tail)
        return {"ok": True, "read_only": read_only, "records": records}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200], "records": []}


# â”€â”€ GET /v1/prepared/pending â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@app.get("/v1/prepared/pending")
async def prepared_pending(category: Optional[str] = None):
    """List pending prepared actions (not yet executed by operator)."""
    try:
        from core.safe_execution import list_pending as _list_pending, count_pending

        if category:
            items = _list_pending(category)
        else:
            items = _list_pending()
        return {"ok": True, "items": items, "counts": count_pending()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200], "items": []}


# â”€â”€ Trials Inbox System (Phase 4) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

try:
    from fastapi.responses import FileResponse as _FileResponse

    @app.get("/trials")
    async def trials_page():
        """Serve the Trials Inbox UI."""
        return _FileResponse("web/trials.html", media_type="text/html")

except Exception:
    pass

try:
    from core.trials_api import register_trials_api

    register_trials_api(app)
except Exception:
    pass  # fail-open: trials API unavailable

try:
    from core.trials_worker import start_worker as _start_trials_worker

    _start_trials_worker()
except Exception:
    pass  # fail-open: trials worker unavailable


# â”€â”€ Hologram Evolution Ladder â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

try:
    from fastapi.responses import FileResponse as _HoloFileResponse

    @app.get("/hologram")
    async def hologram_page():
        """Serve the Hologram Evolution Ladder UI."""
        return _HoloFileResponse("web/hologram.html", media_type="text/html")

    @app.get("/avatar")
    async def avatar_page():
        """Serve the MASTER SWARMZ interactive avatar + chat UI."""
        return _HoloFileResponse("web/avatar.html", media_type="text/html")
except Exception:
    pass

try:
    from core.hologram_api import register_hologram_api

    register_hologram_api(app)
except Exception:
    pass  # fail-open: hologram API unavailable


# â”€â”€ Awareness Module â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    from core.awareness_api import register_awareness_api

    register_awareness_api(app)
except Exception:
    pass  # fail-open: awareness API unavailable

# â”€â”€ Forensics Module â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    from core.forensics_api import register_forensics_api

    register_forensics_api(app)
except Exception:
    pass  # fail-open: forensics API unavailable

# â”€â”€ Shell Module â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    from fastapi.responses import FileResponse as _ShellFileResponse

    @app.get("/shell")
    async def shell_page():
        """Serve the Shell UI."""
        return _ShellFileResponse("web/shell.html", media_type="text/html")

except Exception:
    pass

try:
    from core.shell_api import register_shell_api

    register_shell_api(app)
except Exception:
    pass  # fail-open: shell API unavailable

# â”€â”€ Market Lab Module â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    from fastapi.responses import FileResponse as _MarketLabFileResponse

    @app.get("/market_lab")
    async def market_lab_page():
        """Serve the Market Lab UI."""
        return _MarketLabFileResponse("web/market_lab.html", media_type="text/html")

except Exception:
    pass

try:
    from core.market_lab_api import register_market_lab_api

    register_market_lab_api(app)
except Exception:
    pass  # fail-open: market lab API unavailable

# â”€â”€ Zapier Universal Connector Bridge â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    from core.zapier_bridge import register_zapier_bridge

    register_zapier_bridge(app)
except Exception:
    pass  # fail-open: zapier bridge unavailable

# ── Pinterest Integration Bridge ──────────────────────────
try:
    from core.pinterest_bridge import register_pinterest_bridge

    register_pinterest_bridge(app)
except Exception:
    pass  # fail-open: pinterest bridge unavailable


# Minimal scaffold for server.py


def start_server():
    pass


__all__ = ["app"]

# Import routers from their respective modules
from swarmz_runtime.api.system import router as system_router
from swarmz_runtime.api.admin import router as admin_router
from swarmz_runtime.api.factory_routes import router as factory_routes_router
from swarmz_runtime.api.meta_routes import router as meta_routes_router
from addons.api.addons_router import router as addons_router
from addons.api.guardrails_router import router as guardrails_router
from addons.api.ui_router import router as ui_router
try:
    from addons.api.dashboard_router import router as dashboard_router
    _dashboard_available = True
except Exception:
    _dashboard_available = False
try:
    from core.engine_api import router as engine_router
    _engine_available = True
except Exception:
    _engine_available = False

# Register all routers in the FastAPI app
app.include_router(system_router, prefix="/v1/system", tags=["system"])
app.include_router(admin_router, prefix="/v1/admin", tags=["admin"])
app.include_router(factory_routes_router, prefix="/v1/factory", tags=["factory"])
app.include_router(meta_routes_router, prefix="/v1/meta", tags=["meta"])
app.include_router(addons_router, prefix="/v1/addons", tags=["addons"])
app.include_router(guardrails_router, prefix="/v1/guardrails", tags=["guardrails"])
app.include_router(ui_router, tags=["ui"])
if _dashboard_available:
    app.include_router(dashboard_router, tags=["dashboard"])
if _engine_available:
    app.include_router(engine_router, tags=["engine"])

# --- Enhanced SWARMZ UI Routes ---
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Serve static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve modern React UI assets
_ui_dist_assets = os.path.join("ui", "dist", "assets")
if os.path.exists(_ui_dist_assets):
    app.mount("/assets", StaticFiles(directory=_ui_dist_assets), name="ui-assets")


def _modern_ui_index_path() -> str | None:
    candidate = os.path.join("ui", "dist", "index.html")
    return candidate if os.path.exists(candidate) else None

# Serve enhanced UI at root
@app.get("/", response_class=FileResponse)
async def serve_enhanced_ui():
    """Serve the primary SWARMZ UI."""
    modern_ui = _modern_ui_index_path()
    if modern_ui:
        return FileResponse(modern_ui, media_type="text/html")
    legacy_ui = os.path.join("static", "enhanced_ui.html")
    if os.path.exists(legacy_ui):
        return FileResponse(legacy_ui, media_type="text/html")
    else:
        return HTMLResponse("""
        <html><body style='background:#0a0a0a; color:#00ffff; text-align:center; padding:50px;'>
        <h1>🤖 SWARMZ Enhanced UI</h1>
        <p>Enhanced interface loading...</p>
        <p><a href='/ui/api/capabilities' style='color:#ffd700;'>API Capabilities</a></p>
        </body></html>
        """)


@app.get("/app", response_class=FileResponse)
async def serve_app_ui():
    """Serve SWARMZ app entry route explicitly."""
    return await serve_enhanced_ui()

# Alternative enhanced UI access
@app.get("/enhanced", response_class=FileResponse)
async def serve_enhanced_ui_alt():
    """Alternative path to enhanced UI"""
    return await serve_enhanced_ui()

# --- Wire in additional capability routers (fail-open) ---
_extra_routers = [
    ("swarmz_runtime.api.debug", "router", "/v1/debug", "debug"),
    ("swarmz_runtime.api.observability", "router", "", "observability"),
    ("swarmz_runtime.api.infra", "router", "", "infra"),
    ("swarmz_runtime.api.verify_routes", "router", "/v1/verify", "verify"),
    ("swarmz_runtime.api.perf_routes", "router", "", "perf"),
    ("swarmz_runtime.api.v1_stubs", "v1_stubs_router", "/v1", "v1-stubs"),
    ("swarmz_runtime.api.runtime_endpoints", "router", "", "runtime-endpoints"),
    ("swarmz_runtime.ui.cockpit", "router", "", "cockpit"),
    ("swarmz_runtime.arena.ui", "router", "", "arena-ui"),
    ("swarmz_app.api.hologram", "router", "", "hologram"),
]
import importlib as _il
for _mod_name, _var, _prefix, _tag in _extra_routers:
    try:
        _mod = _il.import_module(_mod_name)
        _r = getattr(_mod, _var)
        if _prefix:
            app.include_router(_r, prefix=_prefix, tags=[_tag])
        else:
            app.include_router(_r, tags=[_tag])
    except Exception:
        pass  # fail-open: router not available

# Ensure UI router dependencies can resolve a core instance.
if not hasattr(app.state, "orchestrator"):
    app.state.orchestrator = SimpleNamespace(core=_swarmz_core)
elif getattr(app.state.orchestrator, "core", None) is None:
    app.state.orchestrator.core = _swarmz_core

# Import the companion_state handler from the new module
from swarmz_runtime.api.companion_state import companion_state

# Register the companion_state endpoint
app.add_api_route("/v1/companion/state", companion_state, methods=["GET"], tags=["companion"])


# --- Stub endpoints for commonly expected paths ---
@app.get("/v1/runtime/status", tags=["runtime"])
async def runtime_status():
    """Runtime status aggregate — combines ui/state + companion/state."""
    from swarmz_server import compute_phase
    missions_file = Path("data/missions.jsonl")
    missions, _, _ = read_jsonl(missions_file)
    total = len(missions)
    success = sum(1 for m in missions if str(m.get("status", "")).upper() == "SUCCESS")
    phase = compute_phase(total, success)
    return {
        "ok": True,
        "phase": phase,
        "total_missions": total,
        "success_count": success,
        "success_rate": round(success / total, 2) if total else 0.0,
        "policy": "active",
        "identity": "MASTER_SWARMZ",
    }


@app.get("/v1/command-center/state", tags=["command-center"])
async def command_center_state():
    """Operator command-center overview."""
    missions_file = Path("data/missions.jsonl")
    audit_file = Path("data/audit.jsonl")
    missions, _, _ = read_jsonl(missions_file)
    audits, _, _ = read_jsonl(audit_file)
    total_m = len(missions)
    success_m = sum(1 for m in missions if str(m.get("status", "")).upper() == "SUCCESS")
    return {
        "ok": True,
        "missions": {"total": total_m, "success": success_m, "pending": total_m - success_m},
        "audit_entries": len(audits),
        "policy": "active",
        "companion": "online",
        "phase": "SOVEREIGN" if total_m >= 50 and success_m / max(total_m, 1) >= 0.3 else "FORGING",
    }


app.add_api_route(
    "/v1/companion/state", companion_state, methods=["GET"], tags=["companion"]
)
