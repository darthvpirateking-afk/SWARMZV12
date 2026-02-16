import os
import json
import socket
import secrets
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from swarmz_runtime.core.engine import SwarmzEngine
from swarmz_runtime.api import missions, ecosystem, admin
from swarmz_runtime.core import telemetry

# SWARMZ must export `app` for run_swarmz.py
app = FastAPI(
    title="SWARMZ",
    version=os.getenv("SWARMZ_VERSION", "0.0.0"),
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
UI_DIR = ROOT_DIR / "web_ui"
DATA_DIR.mkdir(exist_ok=True, parents=True)
START_TIME = datetime.utcnow()


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
    return engine


active_tokens: Dict[str, datetime] = {}
PAIRING_EXEMPT = {"/v1/pairing/pair", "/v1/pairing/info", "/health"}

@app.get("/health")
def health():
    return {"ok": True, "service": "swarmz", "version": app.version}


@app.get("/v1/health")
def v1_health(request: Request):
    cfg = _load_runtime_config()
    offline = _resolve_offline_mode(cfg)
    uptime = (datetime.utcnow() - START_TIME).total_seconds()
    base_url = str(request.base_url).rstrip("/")
    ui_expected = cfg.get("uiBaseUrl") or cfg.get("ui_base") or f"{base_url}"
    return {
        "ok": True,
        "version": app.version,
        "uptime_seconds": round(uptime, 2),
        "data_dir": str(DATA_DIR),
        "ui_expected": ui_expected,
        "offline_mode": offline,
    }


@app.middleware("http")
async def operator_gate(request: Request, call_next):
    if request.method in {"POST", "PUT", "DELETE", "PATCH"} and request.url.path not in PAIRING_EXEMPT:
        auth = request.headers.get("Authorization", "")
        bearer = None
        if auth.lower().startswith("bearer "):
            bearer = auth.split(" ", 1)[1].strip()
        header_key = request.headers.get("X-Operator-Key")
        token_ok = bearer in active_tokens
        key_ok = header_key == OPERATOR_PIN
        if not token_ok and not key_ok:
            return JSONResponse(status_code=401, content={"ok": False, "error": "operator key required"})
    telemetry.record_event("http_request", {"path": str(request.url.path), "method": request.method})
    return await call_next(request)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Keep errors visible + deterministic shape
    telemetry.record_failure("unhandled_exception", str(exc), {"path": str(request.url.path)})
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": str(exc),
            "type": exc.__class__.__name__,
            "path": str(request.url.path),
            "trace": traceback.format_exc(),
        },
    )

class PairRequest(BaseModel):
    pin: str = Field(..., min_length=3)


class DispatchRequest(BaseModel):
    goal: str
    category: str = "general"
    constraints: Dict[str, Any] = Field(default_factory=dict)


class SovereignDispatch(BaseModel):
    intent: str
    scope: Any
    limits: Any | None = None


@app.get("/v1/pairing/info")
def pairing_info(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return {
        "base_url": base_url,
        "requires_pin": True,
        "server_time": datetime.utcnow().isoformat() + "Z",
        "version": app.version,
    }


@app.post("/v1/pairing/pair")
def pairing_pair(body: PairRequest):
    if body.pin != OPERATOR_PIN:
        raise HTTPException(status_code=401, detail="invalid pin")
    token = secrets.token_hex(16)
    active_tokens[token] = datetime.utcnow()
    telemetry.record_event("pairing_success", {"token": token})
    return {"token": token}


@app.get("/v1/runs")
def list_runs():
    runs = engine.db.load_all_missions()
    runs_sorted = sorted(runs, key=lambda r: r.get("updated_at") or r.get("created_at", ""), reverse=True)
    return {"runs": runs_sorted, "count": len(runs_sorted)}


@app.get("/v1/runs/{run_id}")
def get_run(run_id: str):
    run = engine.db.get_mission(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    audit = [a for a in engine.db.load_audit_log(limit=500) if a.get("mission_id") == run_id]
    return {"run": run, "audit": audit}


@app.post("/v1/dispatch")
def dispatch_mission(body: DispatchRequest, request: Request):
    created = engine.create_mission(body.goal, body.category, body.constraints)
    if "error" in created:
        raise HTTPException(status_code=400, detail=created["error"])

    header_key = request.headers.get("X-Operator-Key") or OPERATOR_PIN
    ran = engine.run_mission(created["mission_id"], operator_key=header_key)
    telemetry.record_event("dispatch", {"mission_id": created.get("mission_id"), "goal": body.goal})
    if OFFLINE_MODE:
        ran["offline_mode"] = True
        ran["note"] = "OFFLINE_MODE is enabled; mission stored without external calls"
    return {"created": created, "run": ran}


@app.get("/v1/companion/state")
def companion_state():
    eng = get_engine()
    return {"state": eng.evolution.get_companion_state()}


@app.get("/v1/companion/history")
def companion_history(limit: int = 20):
    eng = get_engine()
    lim = max(1, min(limit, 200))
    return {"entries": eng.evolution.history_tail(limit=lim)}


@app.get("/v1/runtime/scoreboard")
def runtime_scoreboard():
    eng = get_engine()
    return eng.get_scoreboard()


@app.get("/v1/audit/tail")
def audit_tail(limit: int = 50):
    limit = max(1, min(limit, 500))
    entries = engine.db.load_audit_log(limit=limit)
    return {"entries": entries[-limit:], "count": len(entries[-limit:])}


@app.get("/v1/runtime/status")
def runtime_status():
    active = engine.db.get_active_missions()
    pending = [m for m in engine.db.load_all_missions() if m.get("status") == "pending"]
    avg_step = telemetry.avg_duration("run_mission") or telemetry.avg_duration("autoloop_tick")
    last_evt = telemetry.last_event()
    system_load = round(len(active) / max(engine.max_active_missions, 1), 2)
    return {
        "active_agents": len(active),
        "queued_tasks": len(pending),
        "avg_step_time_ms": avg_step,
        "last_event": last_evt,
        "system_load_estimate": system_load,
    }


@app.get("/v1/runtime/counterfactual")
def runtime_counterfactual(limit: int = 50):
    eng = get_engine()
    lim = max(1, min(limit, 200))
    overview = eng.get_counterfactual_overview(limit=lim)
    return {
        "snapshots": overview.get("snapshots", []),
        "counterfactuals": overview.get("counterfactuals", []),
        "reliability": overview.get("reliability", {}),
        "uncertainty": overview.get("uncertainty", {}),
    }


@app.get("/v1/runtime/phase")
def runtime_phase(limit: int = 100):
    eng = get_engine()
    lim = max(1, min(limit, 300))
    overview = eng.get_phase_overview(limit=lim)
    return {
        "history": overview.get("history", []),
        "patterns": overview.get("patterns", {}),
        "interventions": overview.get("interventions", []),
    }


def _include_router_if_present():
    try:
        missions.get_engine = get_engine
        app.include_router(missions.router, prefix="/v1/missions", tags=["missions"])
    except Exception:
        pass
    try:
        ecosystem.set_engine_provider(get_engine)
        app.include_router(ecosystem.router, prefix="/v1/ecosystem", tags=["ecosystem"])
    except Exception:
        pass
    try:
        admin.get_engine = get_engine
        app.include_router(admin.router, prefix="/v1/admin", tags=["admin"])
    except Exception:
        pass


_include_router_if_present()

# Galileo Harness routes (additive)
try:
    from swarmz_runtime.api.galileo_routes import router as galileo_router
    app.include_router(galileo_router)
except Exception:
    pass

# Best-effort: include existing routers if present (do not restructure repo).
# If your repo already has routing elsewhere, this will hook it up.
for mod_path, attr in [
    ("swarmz_runtime.api.routes", "router"),
    ("swarmz_runtime.api.router", "router"),
    ("swarmz_runtime.api.v1.routes", "router"),
    ("swarmz_runtime.api.v1.router", "router"),
]:
    try:
        m = __import__(mod_path, fromlist=[attr])
        r = getattr(m, attr)
        app.include_router(r)
        break
    except Exception:
        continue


def _file_in_ui(name: str) -> Path:
    return UI_DIR / name


if UI_DIR.exists():
    app.mount("/app", StaticFiles(directory=UI_DIR, html=True), name="pwa")


@app.get("/")
def root_index():
    index = _file_in_ui("index.html")
    if index.exists():
        return FileResponse(index)
    return {"ok": True, "message": "SWARMZ runtime ready"}


@app.head("/")
def root_head():
    index = _file_in_ui("index.html")
    if index.exists():
        return FileResponse(index, media_type="text/html")
    return JSONResponse(status_code=200, content={"ok": True})


def _append_jsonl(path: Path, row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, separators=(',', ':')) + "\n")


def _tail_jsonl(path: Path, limit: int = 10) -> list:
    if not path.exists():
        return []
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        continue
    except Exception:
        return []
    return rows[-limit:]


@app.get("/config/runtime.json")
def runtime_config_file(request: Request):
    cfg = _load_runtime_config()
    if not cfg:
        cfg = {}
    base_url = cfg.get("apiBaseUrl") or cfg.get("api_base") or str(request.base_url).rstrip("/")
    ui_url = cfg.get("uiBaseUrl") or cfg.get("ui_base") or f"{base_url}/app"
    bind = cfg.get("bind") or "0.0.0.0"
    port = cfg.get("port") or 8012
    offline = _resolve_offline_mode(cfg)
    merged = {
        "apiBaseUrl": base_url,
        "uiBaseUrl": ui_url,
        "bind": bind,
        "port": port,
        "offlineMode": offline,
    }
    return merged


@app.get("/manifest.json")
def manifest_file():
    manifest = _file_in_ui("manifest.json")
    if manifest.exists():
        return FileResponse(manifest)
    raise HTTPException(status_code=404, detail="manifest not found")


@app.head("/manifest.json")
def manifest_head():
    manifest = _file_in_ui("manifest.json")
    if manifest.exists():
        return FileResponse(manifest, media_type="application/json")
    raise HTTPException(status_code=404, detail="manifest not found")


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
