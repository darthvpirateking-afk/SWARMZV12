# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Control endpoints — mode, swarm status, AI status, companion, runtime, security.

Consolidates the control-plane routes previously in server.py and
swarmz_runtime/api/server.py.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from swarmz_runtime.api.models import (
    BuildDispatchRequest,
    DispatchRequest,
    MissionCreateRequest,
    ModeRequest,
    TaskExecuteRequest,
    TaskExecuteResponse,
)

router = APIRouter(tags=["control"])

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _ROOT_DIR / "data"
_DATA_DIR.mkdir(exist_ok=True, parents=True)
_MISSIONS_FILE = _DATA_DIR / "missions.jsonl"
_AUDIT_FILE = _DATA_DIR / "audit.jsonl"
_STATE_FILE = _DATA_DIR / "state.json"
_HEARTBEAT_FILE = _DATA_DIR / "runner_heartbeat.json"


# ---------------------------------------------------------------------------
# JSONL / state helpers
# ---------------------------------------------------------------------------
def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, separators=(",", ":"), default=str) + "\n")


def _tail_jsonl(path: Path, limit: int) -> list:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        tail = lines[-limit:]
        return [json.loads(line) for line in tail if line.strip()]
    except Exception:
        return []


def _utc_now_iso_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_state() -> Dict[str, Any]:
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    default = {
        "mode": "COMPANION",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "version": 1,
    }
    _STATE_FILE.write_text(json.dumps(default, indent=2), encoding="utf-8")
    return default


def _write_state(state: Dict[str, Any]) -> None:
    _STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _expected_operator_key() -> Optional[str]:
    return os.environ.get("OPERATOR_KEY")


def _get_operator_key(
    request: Request,
    x_operator_key: Optional[str] = Header(None),
    operator_key: Optional[str] = None,
) -> str:
    """Validate operator key. Localhost writes are allowed without a key."""
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


def compute_phase(total_missions: int, success_count: int) -> str:
    """Compute phase based on mission counts and success rate."""
    if total_missions < 10:
        return "AWAKENING"
    success_rate = success_count / total_missions if total_missions > 0 else 0.0
    if success_rate < 0.3:
        return "QUARANTINE"
    if total_missions < 50:
        return "FORGING"
    return "SOVEREIGN"


# ---------------------------------------------------------------------------
# Mission CRUD (from swarmz_server.py)
# ---------------------------------------------------------------------------
@router.post("/v1/missions/create")
async def create_mission(req: MissionCreateRequest):
    """Create a new mission."""
    from jsonl_utils import write_jsonl

    mission_id = f"mission_{int(datetime.now(timezone.utc).timestamp()*1000)}"
    created_at = _utc_now_iso_z()
    mission = {
        "mission_id": mission_id,
        "goal": req.goal,
        "category": req.category,
        "constraints": req.constraints,
        "results": req.results,
        "status": "PENDING",
        "created_at": created_at,
    }
    write_jsonl(_MISSIONS_FILE, mission)
    audit_event = {
        "event": "mission_created",
        "mission_id": mission_id,
        "timestamp": created_at,
        "goal": req.goal,
        "category": req.category,
    }
    write_jsonl(_AUDIT_FILE, audit_event)
    return {
        "ok": True,
        "mission_id": mission_id,
        "status": "PENDING",
        "created_at": created_at,
        "goal": req.goal,
        "category": req.category,
    }


@router.get("/v1/missions/list")
async def list_missions():
    """List all missions."""
    from jsonl_utils import read_jsonl

    missions, skipped, quarantined = read_jsonl(_MISSIONS_FILE)
    now = _utc_now_iso_z()
    for m in missions:
        if "updated_at" not in m:
            m["updated_at"] = m.get("created_at", now)
    return {
        "ok": True,
        "missions": missions,
        "count": len(missions),
        "skipped_empty": skipped,
        "quarantined": quarantined,
    }


@router.post("/v1/missions/run")
async def run_mission(mission_id: str = None):
    """Run/execute a mission by ID."""
    from jsonl_utils import read_jsonl, write_jsonl

    if not mission_id:
        return {"ok": False, "error": "mission_id required"}
    missions, _, _ = read_jsonl(_MISSIONS_FILE)
    mission = next((m for m in missions if m.get("mission_id") == mission_id), None)
    if not mission:
        return {"ok": False, "error": f"mission_id {mission_id} not found"}
    started_at = _utc_now_iso_z()
    mission["status"] = "RUNNING"
    mission["started_at"] = started_at
    _MISSIONS_FILE.write_text("")
    for m in missions:
        write_jsonl(_MISSIONS_FILE, m)
    audit_event = {
        "event": "mission_run",
        "mission_id": mission_id,
        "timestamp": started_at,
    }
    write_jsonl(_AUDIT_FILE, audit_event)
    return {
        "ok": True,
        "mission_id": mission_id,
        "status": "RUNNING",
        "started_at": started_at,
    }


# ---------------------------------------------------------------------------
# UI state (from swarmz_server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/ui/state")
async def ui_state():
    """Get UI state including server, missions, and phase."""
    from jsonl_utils import read_jsonl

    missions, _, _ = read_jsonl(_MISSIONS_FILE)
    audit_events, _, _ = read_jsonl(_AUDIT_FILE)

    status_counts = {}
    success_count = 0
    for m in missions:
        status = m.get("status", "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
        if status == "SUCCESS":
            success_count += 1

    last_events = audit_events[-10:] if audit_events else []
    phase = compute_phase(len(missions), success_count)

    import socket

    def _get_lan_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    port = int(os.environ.get("PORT", "8012"))
    lan_ip = _get_lan_ip()
    now = _utc_now_iso_z()
    return {
        "ok": True,
        "server": {
            "version": "1.0.0",
            "now": now,
            "lan_url": f"http://{lan_ip}:{port}",
            "local_url": f"http://127.0.0.1:{port}",
        },
        "missions": {"count_total": len(missions), "count_by_status": status_counts},
        "last_events": last_events,
        "phase": phase,
    }


# ---------------------------------------------------------------------------
# Debug (from swarmz_server.py)
# ---------------------------------------------------------------------------
_last_exception_traceback = None


@router.get("/v1/debug/traceback_last")
async def traceback_last():
    return {
        "ok": True,
        "traceback": _last_exception_traceback or "No exception recorded",
    }


# ---------------------------------------------------------------------------
# Task execution (from swarmz_server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/tasks")
async def list_tasks():
    try:
        from swarmz import SwarmzCore

        core = SwarmzCore()
        capabilities = core.list_capabilities()
        return {"success": True, "tasks": capabilities, "count": len(capabilities)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/v1/execute", response_model=TaskExecuteResponse)
async def execute_task(request: TaskExecuteRequest):
    try:
        from swarmz import SwarmzCore

        core = SwarmzCore()
        result = core.execute(request.task, **request.params)
        return TaskExecuteResponse(success=True, result=result)
    except ValueError as e:
        return TaskExecuteResponse(success=False, error=f"Task not found: {str(e)}")
    except Exception as e:
        return TaskExecuteResponse(success=False, error=str(e))


# ---------------------------------------------------------------------------
# Audit (from swarmz_server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/audit")
async def get_audit_log():
    try:
        from swarmz import SwarmzCore

        core = SwarmzCore()
        audit = core.get_audit_log()
        return {"success": True, "audit_log": audit, "count": len(audit)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/v1/audit/tail")
def audit_tail(limit: int = 10):
    lim = max(1, min(limit, 500))
    return {"entries": _tail_jsonl(_AUDIT_FILE, lim)}


# ---------------------------------------------------------------------------
# Security (from swarmz_server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/security/status")
async def security_status(limit_events: int = 50):
    from addons.security import security_status_snapshot

    snapshot = security_status_snapshot(limit_events=limit_events)
    return {"ok": True, **snapshot}


# ---------------------------------------------------------------------------
# System info (from swarmz_server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/system/info")
async def system_info():
    try:
        from swarmz import SwarmzCore

        core = SwarmzCore()
        info = core.execute("system_info")
        return {"success": True, "info": info}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Honeypots (from swarmz_server.py)
# ---------------------------------------------------------------------------
@router.get("/admin")
async def admin_honeypot(request: Request):
    from addons.security import honeypot_endpoint

    return await honeypot_endpoint(request, label="root_admin")


@router.get("/v1/admin/secret")
async def admin_secret_honeypot(request: Request):
    from addons.security import honeypot_endpoint

    return await honeypot_endpoint(request, label="api_admin_secret")


# ---------------------------------------------------------------------------
# Companion message (from swarmz_server.py)
# ---------------------------------------------------------------------------
@router.post("/v1/companion/message")
async def companion_message(request: Request):
    try:
        data = await request.json()
        user_message = data.get("text", "").strip()
        if not user_message:
            return JSONResponse(
                {"ok": False, "error": "Empty message."}, status_code=400
            )

        try:
            from core.companion import chat as companion_chat

            result = companion_chat(user_message)
            resp = {
                "ok": True,
                "reply": result.get("reply", "(empty)"),
                "source": result.get("source", "unknown"),
            }
            if result.get("provider"):
                resp["provider"] = result["provider"]
            if result.get("model"):
                resp["model"] = result["model"]
            if result.get("latencyMs"):
                resp["latencyMs"] = result["latencyMs"]
            return JSONResponse(resp)
        except Exception as companion_err:
            lower = user_message.lower()
            if "status" in lower:
                reply = "System operational. Use the BUILD tab to dispatch missions."
            elif "help" in lower:
                reply = "COMMANDS: status | help | mode | missions | memory"
            elif "mode" in lower:
                reply = "Use the mode tabs in the HUD to switch COMPANION / BUILD / HOLOGRAM."
            elif "mission" in lower:
                reply = "Use BUILD mode to create and dispatch missions."
            else:
                reply = "ACKNOWLEDGED: " + user_message[:120]
            return JSONResponse(
                {
                    "ok": True,
                    "reply": reply,
                    "source": "inline_fallback",
                    "warning": f"core.companion unavailable: {str(companion_err)[:100]}",
                }
            )
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ---------------------------------------------------------------------------
# Sovereign dispatch (from server.py — operator-key gated)
# ---------------------------------------------------------------------------
@router.post("/v1/sovereign/dispatch")
async def sovereign_dispatch_legacy(
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

    _append_jsonl(_MISSIONS_FILE, mission)
    _append_jsonl(_AUDIT_FILE, audit)
    return {"ok": True, "mission_id": mission_id, "status": "PENDING"}


# ---------------------------------------------------------------------------
# System log (from server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/system/log")
async def system_log(tail: int = 10):
    t = max(1, min(int(tail), 200))
    return {"entries": _tail_jsonl(_AUDIT_FILE, t)}


# ---------------------------------------------------------------------------
# Mode (from server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/mode")
async def get_mode():
    s = _read_state()
    return {
        "ok": True,
        "mode": s["mode"],
        "updated_at": s.get("updated_at"),
        "version": s.get("version", 1),
    }


@router.post("/v1/mode")
async def set_mode(payload: ModeRequest, op_key: str = Depends(_get_operator_key)):
    mode = payload.mode.upper()
    if mode not in ("COMPANION", "BUILD"):
        raise HTTPException(status_code=400, detail="mode must be COMPANION or BUILD")
    now = datetime.utcnow().isoformat() + "Z"
    s = _read_state()
    old_mode = s.get("mode")
    s["mode"] = mode
    s["updated_at"] = now
    s["version"] = s.get("version", 0) + 1
    _write_state(s)
    _append_jsonl(
        _AUDIT_FILE,
        {
            "timestamp": now,
            "event": "mode_changed",
            "old_mode": old_mode,
            "new_mode": mode,
            "operator": bool(op_key),
        },
    )
    return {"ok": True, "mode": mode, "updated_at": now, "version": s["version"]}


# ---------------------------------------------------------------------------
# Build dispatch (from server.py)
# ---------------------------------------------------------------------------
@router.post("/v1/build/dispatch")
async def build_dispatch(
    payload: BuildDispatchRequest, op_key: str = Depends(_get_operator_key)
):
    from jsonl_utils import write_jsonl

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
    write_jsonl(_MISSIONS_FILE, mission)
    _append_jsonl(
        _AUDIT_FILE,
        {
            "timestamp": now,
            "event": "mission_created",
            "mission_id": mission_id,
            "intent": payload.intent,
        },
    )
    return {"ok": True, "mission_id": mission_id, "status": "PENDING"}


# ---------------------------------------------------------------------------
# Swarm status (from server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/swarm/status")
async def swarm_status():
    from jsonl_utils import read_jsonl

    runner_state = "down"
    last_tick = None
    if _HEARTBEAT_FILE.exists():
        try:
            hb = json.loads(_HEARTBEAT_FILE.read_text(encoding="utf-8"))
            runner_state = hb.get("status", "down")
            last_tick = hb.get("last_tick")
        except Exception:
            pass

    missions, _, _ = read_jsonl(_MISSIONS_FILE)
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


# ---------------------------------------------------------------------------
# AI status (from server.py + swarmz_runtime/api/server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/ai/status")
async def ai_status():
    from jsonl_utils import read_jsonl

    missions_result = read_jsonl(_MISSIONS_FILE)
    if isinstance(missions_result, tuple):
        missions = missions_result[0]
    elif isinstance(missions_result, list):
        missions = missions_result
    else:
        missions = []

    success_count = sum(
        1
        for m in missions
        if str(m.get("status", "")).upper() in {"SUCCESS", "COMPLETED"}
    )
    total = len(missions)
    success_rate = (success_count / total) if total else 0.0

    if total < 10:
        phase = "AWAKENING"
    elif success_rate < 0.3:
        phase = "QUARANTINE"
    elif total < 50:
        phase = "FORGING"
    else:
        phase = "SOVEREIGN"

    return {
        "ok": True,
        "phase": phase,
        "quarantine": phase == "QUARANTINE",
        "missions_total": total,
        "success_rate": success_rate,
    }


# ---------------------------------------------------------------------------
# Runtime scoreboard (from server.py + swarmz_runtime/api/server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/runtime/scoreboard")
async def runtime_scoreboard():
    deterministic_traits = {
        "logic": 0.60,
        "precision": 0.62,
        "empathy": 0.64,
        "stability": 0.70,
    }
    return {
        "ok": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "personality": dict(deterministic_traits),
        "partner_traits": deterministic_traits,
        "traits_mode": "deterministic_static",
    }


# ---------------------------------------------------------------------------
# Runtime status (from swarmz_runtime/api/server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/runtime/status")
def runtime_status():
    return {
        "ok": True,
        "active_agents": 0,
        "queued_tasks": 0,
        "system_load_estimate": 0.0,
    }


# ---------------------------------------------------------------------------
# Companion state (from server.py + swarmz_runtime/api/server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/companion/state")
async def companion_state_endpoint():
    try:
        from core.companion_master import get_composite_context, self_assessment

        ctx = get_composite_context()
        ctx["self_assessment"] = self_assessment()
        return {"ok": True, **ctx}
    except Exception:
        return {
            "ok": True,
            "state": "active",
            "master_identity": "MASTER_SWARMZ",
            "self_assessment": "MASTER_SWARMZ companion state is active.",
        }


# ---------------------------------------------------------------------------
# Companion history (from server.py + swarmz_runtime/api/server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/companion/history")
async def companion_history(tail: int = 20):
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
    except Exception:
        return {"ok": True, "records": [], "history": [], "read_only": True}


# ---------------------------------------------------------------------------
# Prepared pending (from server.py + swarmz_runtime/api/server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/prepared/pending")
async def prepared_pending(category: Optional[str] = None):
    base = _ROOT_DIR / "prepared_actions"
    items = []
    counts: Dict[str, int] = {}

    if base.exists():
        for category_dir in base.iterdir():
            if not category_dir.is_dir():
                continue
            if category and category_dir.name != category:
                continue

            pending_in_category = 0
            for mission_dir in category_dir.iterdir():
                if not mission_dir.is_dir():
                    continue
                proposal_file = mission_dir / "proposal.json"
                if not proposal_file.exists():
                    continue
                try:
                    payload = json.loads(proposal_file.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if payload.get("executed"):
                    continue

                pending_in_category += 1
                payload["category"] = category_dir.name
                items.append(payload)

            counts[category_dir.name] = pending_in_category

    return {
        "ok": True,
        "pending": items,
        "items": items,
        "count": len(items),
        "counts": counts,
    }


# ---------------------------------------------------------------------------
# Runs (from swarmz_runtime/api/server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/runs")
def runs():
    from jsonl_utils import read_jsonl

    runs_file = _DATA_DIR / "runs.jsonl"
    result = read_jsonl(runs_file)

    if not result or not isinstance(result, tuple):
        entries = []
    else:
        entries, _, _ = result

    return {"runs": entries, "count": len(entries)}


# ---------------------------------------------------------------------------
# Config runtime (from swarmz_runtime/api/server.py)
# ---------------------------------------------------------------------------
@router.get("/config/runtime.json")
def config_runtime():
    port = int(os.environ.get("PORT", "8012"))
    base = os.environ.get("BASE_URL") or f"http://127.0.0.1:{port}"

    cfg_path = _ROOT_DIR / "config" / "runtime.json"
    runtime_cfg = {}
    if cfg_path.exists():
        try:
            runtime_cfg = json.loads(cfg_path.read_text())
        except Exception:
            pass

    merged = {
        "apiBaseUrl": base,
        "uiBaseUrl": base,
        "port": port,
        "offlineMode": os.getenv("OFFLINE_MODE", "false") not in {"0", "false", "False", ""},
    }
    merged.update(runtime_cfg)
    return merged


# ---------------------------------------------------------------------------
# Pairing (from swarmz_runtime/api/server.py)
# ---------------------------------------------------------------------------
@router.get("/v1/pairing/info")
def pairing_info():
    pin_file = _DATA_DIR / "operator_pin.txt"
    if pin_file.exists():
        pin = pin_file.read_text().strip()
        return {"pin": pin, "source": "file", "file": str(pin_file), "generated": False}
    return {"pin": None, "source": "none", "generated": False}


@router.post("/v1/pairing/pair")
def pairing_pair():
    # This endpoint is wired in create_app with access to operator_pin state
    return {"ok": False, "error": "pairing not configured in extracted router"}
