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
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import Depends, Header, HTTPException, Request
from pydantic import BaseModel

from swarmz_server import app  # reuse the existing app instance
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

# Register all routers in the FastAPI app
app.include_router(system_router, prefix="/v1/system", tags=["system"])
app.include_router(admin_router, prefix="/v1/admin", tags=["admin"])
app.include_router(factory_routes_router, prefix="/v1/factory", tags=["factory"])
app.include_router(meta_routes_router, prefix="/v1/meta", tags=["meta"])
app.include_router(addons_router, prefix="/v1/addons", tags=["addons"])
app.include_router(guardrails_router, prefix="/v1/guardrails", tags=["guardrails"])

# Import the companion_state handler from the new module
from swarmz_runtime.api.companion_state import companion_state

# Register the companion_state endpoint
app.add_api_route(
    "/v1/companion/state", companion_state, methods=["GET"], tags=["companion"]
)
