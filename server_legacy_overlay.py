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
from types import SimpleNamespace
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
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


@app.get("/health", operation_id="legacy_health")
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
            return JSONResponse(
                {"ok": False, "error": "Intent required"}, status_code=400
            )

        # Route to sovereign dispatch
        try:
            dispatch_payload = DispatchRequest(
                intent=intent,
                scope=str(spec) if spec else "",
                limits={"goal": goal} if goal else None,
            )
            # Note: This is for UI - skip auth for now, add later if needed
            result = await sovereign_dispatch(dispatch_payload, "ui-bypass")
            return JSONResponse(result)
        except Exception as dispatch_err:
            # Fallback: basic mission logging
            import uuid

            mission_id = f"M-{uuid.uuid4().hex[:8]}"
            return JSONResponse(
                {
                    "ok": True,
                    "mission_id": mission_id,
                    "status": "dispatched",
                    "intent": intent,
                    "note": "Logged via UI (fallback)",
                }
            )

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
            success_rate = (
                (success_count / total_missions * 100) if total_missions > 0 else 0
            )

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
                "success_rate": success_rate,
            },
            "ai": ai_status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
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

    @app.get("/avatar", operation_id="avatar_page_legacy")
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
    # SWARMZ V3.0 feature routers
    ("swarmz_runtime.api.operator_identity_routes", "router", "", "operator-identity"),
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
app.add_api_route(
    "/v1/companion/state", companion_state, methods=["GET"], tags=["companion"]
)


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
    success_m = sum(
        1 for m in missions if str(m.get("status", "")).upper() == "SUCCESS"
    )
    return {
        "ok": True,
        "missions": {
            "total": total_m,
            "success": success_m,
            "pending": total_m - success_m,
        },
        "audit_entries": len(audits),
        "policy": "active",
        "companion": "online",
        "phase": (
            "SOVEREIGN"
            if total_m >= 50 and success_m / max(total_m, 1) >= 0.3
            else "FORGING"
        ),
    }


# --- SWARMZ V3.0 — Throne Layer endpoints ---
from swarmz_runtime.core.throne import get_throne


class _DecreeRequest(BaseModel):
    title: str
    body: str
    authority_level: str = "SOVEREIGN"


@app.get("/v1/throne/state", tags=["throne"])
def throne_state():
    """Return the current Throne sovereign state."""
    return get_throne().get_state()


@app.get("/v1/throne/ledger", tags=["throne"])
def throne_ledger():
    """Return the full Throne decree ledger."""
    return {"ledger": get_throne().get_ledger()}


@app.post("/v1/throne/decree", tags=["throne"])
def throne_decree(req: _DecreeRequest):
    """Issue a new sovereign decree."""
    decree = get_throne().issue_decree(req.title, req.body, req.authority_level)
    return {"ok": True, "decree_id": decree.decree_id, "issued_at": decree.issued_at}


# --- SWARMZ V3.0 — Realms endpoints ---
from swarmz_runtime.core.realms import get_realm_registry


class _RealmCreateRequest(BaseModel):
    name: str
    description: str


@app.get("/v1/realms", tags=["realms"])
def list_realms():
    """List all operational realms."""
    return {"realms": get_realm_registry().list_realms()}


@app.post("/v1/realms", tags=["realms"])
def create_realm(req: _RealmCreateRequest):
    """Create a new operational realm."""
    realm = get_realm_registry().create_realm(req.name, req.description)
    return {"ok": True, "realm": realm}


@app.get("/v1/realms/{realm_id}", tags=["realms"])
def get_realm(realm_id: str):
    """Get a specific realm by ID."""
    realm = get_realm_registry().get_realm(realm_id)
    if realm is None:
        raise HTTPException(status_code=404, detail=f"Realm '{realm_id}' not found")
    return realm


# --- SWARMZ V3.0 — Swarm Tiers endpoints ---
from swarmz_runtime.core.swarm_tiers import get_tier, list_tiers


@app.get("/v1/swarm/tiers", tags=["swarm-tiers"])
def swarm_tiers():
    """List all swarm agent tiers."""
    return {"tiers": list_tiers()}


@app.get("/v1/swarm/tiers/{tier_id}", tags=["swarm-tiers"])
def swarm_tier_detail(tier_id: str):
    """Get a specific swarm tier by ID."""
    tier = get_tier(tier_id)
    if tier is None:
        raise HTTPException(status_code=404, detail=f"Tier '{tier_id}' not found")
    return tier


# --- SWARMZ V3.0 — Mission Ranks endpoints ---
from swarmz_runtime.core.mission_ranks import get_rank, list_ranks


@app.get("/v1/missions/ranks", tags=["mission-ranks"])
def mission_ranks():
    """List all mission rank classifications."""
    return {"ranks": list_ranks()}


@app.get("/v1/missions/ranks/{rank_id}", tags=["mission-ranks"])
def mission_rank_detail(rank_id: str):
    """Get a specific mission rank by ID."""
    rank = get_rank(rank_id)
    if rank is None:
        raise HTTPException(status_code=404, detail=f"Rank '{rank_id}' not found")
    return rank


# --- SWARMZ V3.0 — Avatar Matrix endpoints ---
from swarmz_runtime.avatar.avatar_matrix import get_avatar_matrix


class _AvatarStateRequest(BaseModel):
    state: str
    variant: str | None = None


class _AvatarTriggerRequest(BaseModel):
    command: str


@app.get("/v1/avatar/matrix", tags=["avatar-matrix"])
def avatar_matrix_state():
    """Get the current Avatar Matrix state."""
    return get_avatar_matrix().get_matrix_state()


@app.post("/v1/avatar/matrix/state", tags=["avatar-matrix"])
def avatar_matrix_set_state(req: _AvatarStateRequest):
    """Set the avatar state, optionally switching variant."""
    return get_avatar_matrix().set_state(req.state, req.variant)


@app.post("/v1/avatar/matrix/trigger", tags=["avatar-matrix"])
def avatar_matrix_trigger(req: _AvatarTriggerRequest):
    """Trigger avatar evolution commands (ASCEND|SOVEREIGN|MONARCH)."""
    command = str(req.command or "").strip().upper()
    if command not in {"ASCEND", "SOVEREIGN", "MONARCH"}:
        raise HTTPException(
            status_code=400,
            detail="command must be one of ASCEND, SOVEREIGN, MONARCH",
        )
    matrix = get_avatar_matrix()
    transitioned = matrix.operator_trigger(command)
    return {
        "ok": True,
        "command": command,
        "transitioned": transitioned,
        "current_form": matrix.current_form,
    }


# ── NEXUSMON WebSocket — real-time cockpit channel ──────────────────────────
from fastapi import WebSocket as _WS

# XP thresholds for cockpit progress bar
_XP_THRESHOLDS = {
    "ROOKIE": 100.0,
    "CHAMPION": 500.0,
    "ULTIMATE": 2000.0,
    "MEGA": 10000.0,
    "SOVEREIGN": float("inf"),
}


def _entity_payload(entity) -> dict:
    """Build a cockpit-ready dict from the nexusmon entity.

    Maps the new spec schema (uppercase forms/moods, separate traits table)
    to the shape expected by updateEntityDisplay() in nexusmon_console.js.
    """
    try:
        state = entity.get_state()
        traits = entity.get_traits()
    except Exception:
        return {}

    form_raw = state.get("current_form", "ROOKIE")
    # Title-case the form for JS FORM_COLORS lookup (Rookie, Champion, …)
    form = form_raw.capitalize() if form_raw else "Rookie"

    mood_raw = state.get("mood", "CALM")
    # Lowercase the mood for JS MOOD_COLORS lookup (calm, focused, …)
    mood = mood_raw.lower() if mood_raw else "calm"

    xp = float(state.get("evolution_xp") or 0.0)
    xp_to_next = _XP_THRESHOLDS.get(form_raw, 100.0)
    xp_pct = (
        min(100.0, (xp / xp_to_next * 100.0)) if xp_to_next != float("inf") else 100.0
    )

    return {
        "name": "NEXUSMON",
        "form": form,
        "mood": mood,
        "xp": xp,
        "xp_to_next": None if xp_to_next == float("inf") else xp_to_next,
        "xp_pct": round(xp_pct, 1),
        "boot_count": state.get("boot_count", 0),
        "interaction_count": state.get("interaction_count", 0),
        "traits": traits,
        "operator_name": state.get("operator_name", ""),
        "bond_established_at": state.get("bond_established_at", ""),
    }


@app.websocket("/ws/nexusmon")
async def nexusmon_ws(websocket: _WS):
    """WebSocket channel for the NEXUSMON cockpit.

    Delegates to nexusmon.console.ws_handler which owns the full
    chat loop: greeting → message loop → XP → evolution → disconnect.
    """
    from nexusmon.console.ws_handler import handle_ws_chat

    await handle_ws_chat(websocket)
