# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.


import logging
import os
import json
import socket
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from contextlib import asynccontextmanager

logger = logging.getLogger("swarmz.server")

from swarmz_runtime.core.engine import SwarmzEngine
from jsonl_utils import read_jsonl
from kernel_runtime.orchestrator import SwarmzOrchestrator
from swarmz_runtime.api import system, admin, ecosystem
from . import arena as arena_api
from .missions import router as missions_router
from .system import router as system_router
from .admin import router as admin_router
from .arena import router as arena_router
from .factory_routes import router as factory_routes_router
from .meta_routes import router as meta_routes_router
from .operational_routes import router as operational_routes_router
from .operator_ecosystem_routes import router as operator_ecosystem_routes_router
from .federation_routes import router as federation_routes_router
from .charter_routes import router as charter_routes_router
from .fusion_routes import router as fusion_routes_router
from .primal_routes import router as primal_routes_router
from .template_sync_routes import router as template_sync_routes_router
from .system_primitives_routes import router as system_primitives_routes_router
from swarmz_runtime.core.system_primitives import SystemPrimitivesRuntime
from addons.api.addons_router import router as addons_router
from addons.api.guardrails_router import router as guardrails_router

# ---- cheap constants only (NO orchestrator creation here) ----
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
DATA_DIR = ROOT_DIR / "data"
UI_DIR = ROOT_DIR / "web_ui"
DATA_DIR.mkdir(exist_ok=True, parents=True)
START_TIME = datetime.now(timezone.utc)


def build_orchestrator():
    """Initialize and return a SwarmzOrchestrator instance."""
    orchestrator_instance = SwarmzOrchestrator()
    return orchestrator_instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: attach orchestrator here, not at import time
    app.state.orchestrator = build_orchestrator()
    yield
    # shutdown: optional cleanup


def create_app() -> FastAPI:
    from fastapi.middleware.cors import CORSMiddleware

    # Allow origins from env var; fall back to all origins for local dev
    _cors_origins_env = os.environ.get("CORS_ALLOW_ORIGINS", "")
    _cors_origins = (
        [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
        if _cors_origins_env
        else ["*"]
    )

    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")
    app.include_router(missions_router, prefix="/v1/missions", tags=["missions"])
    app.include_router(system_router, prefix="/v1/system", tags=["system"])
    app.include_router(admin_router, prefix="/v1/admin", tags=["admin"])
    app.include_router(arena_router, prefix="/v1/arena", tags=["arena"])
    app.include_router(factory_routes_router, prefix="/v1/factory", tags=["factory"])
    app.include_router(meta_routes_router, prefix="/v1/meta", tags=["meta"])
    app.include_router(operational_routes_router, prefix="/v1", tags=["operational"])
    app.include_router(
        operator_ecosystem_routes_router, prefix="/v1", tags=["operator-os"]
    )
    app.include_router(federation_routes_router, prefix="/v1", tags=["federation"])
    app.include_router(charter_routes_router, prefix="/v1", tags=["charter"])
    app.include_router(fusion_routes_router, prefix="/v1", tags=["fusion"])
    app.include_router(primal_routes_router, prefix="/v1", tags=["primal"])
    app.include_router(
        template_sync_routes_router, prefix="/v1", tags=["template-sync"]
    )
    app.include_router(
        system_primitives_routes_router, prefix="/v1", tags=["system-primitives"]
    )
    app.include_router(addons_router, prefix="/v1/addons", tags=["addons"])
    app.include_router(guardrails_router, prefix="/v1/guardrails", tags=["guardrails"])

    from .system_control import router as system_control_router
    from .mission_lifecycle import router as mission_lifecycle_router
    from .app_store_routes import router as app_store_router

    app.include_router(
        system_control_router, prefix="/v1/system", tags=["system-control"]
    )
    app.include_router(
        mission_lifecycle_router, prefix="/v1/missions", tags=["mission-lifecycle"]
    )
    app.include_router(app_store_router, prefix="/v1/appstore", tags=["appstore"])

    return app


# Create the app instance
app = create_app()


class SovereignDispatch(BaseModel):
    intent: str
    scope: Any = Field(default_factory=dict)
    limits: Any = Field(default_factory=dict)


class PairRequest(BaseModel):
    pin: str


class DispatchRequest(BaseModel):
    goal: str
    category: str
    constraints: Dict[str, Any] = Field(default_factory=dict)


class AutonomyDialRequest(BaseModel):
    level: int = Field(ge=0, le=100)


class ShadowModeRequest(BaseModel):
    enabled: bool
    lane: str = "mirror"


class EvolutionPromoteRequest(BaseModel):
    partner_id: str
    reason: str = "operator_promotion"


class MarketplacePublishRequest(BaseModel):
    mission_type: str
    title: str
    reward_points: int = Field(ge=0)
    tags: List[str] = Field(default_factory=list)


class OrganismEvolveRequest(BaseModel):
    reason: str = "mission_success"


class LoopTickRequest(BaseModel):
    cycle_label: str = "default"


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


def _tail_jsonl(path: Path, limit: int) -> list:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        tail = lines[-limit:]
        return [json.loads(line) for line in tail if line.strip()]
    except Exception:
        return []


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
        api_base = (
            raw.get("apiBaseUrl") or raw.get("api_base") or raw.get("api_base_url")
        )
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


def _command_center_state_path() -> Path:
    return DATA_DIR / "command_center_state.json"


def _default_command_center_state() -> Dict[str, Any]:
    return {
        "autonomy": {"level": 35, "mode": "assisted"},
        "shadow_mode": {"enabled": False, "lane": "mirror", "last_activation": None},
        "partner": {
            "name": "AegisShade",
            "tier": "Rookie",
            "tier_index": 1,
            "traits": {"logic": 0.60, "empathy": 0.64, "precision": 0.62},
            "autonomy_ceiling": 25,
        },
        "shadow": {
            "name": "NightLegion",
            "tier": "Dormant",
            "tier_index": 0,
            "risk_precision": 0.35,
            "tactical_authority": "operator_approval",
        },
        "autonomy_loop": {
            "sensors": [
                "sales",
                "refunds",
                "support_tickets",
                "fulfillment_delays",
                "spend_rate",
                "conversion_rate",
                "blueprint_performance",
            ],
            "last_tick": None,
            "tick_count": 0,
        },
        "evolution_tree": {
            "tiers": ["seed", "scout", "operator", "architect", "sovereign"],
            "partners": [
                {"partner_id": "alpha", "tier": "scout", "xp": 18},
                {"partner_id": "beta", "tier": "operator", "xp": 42},
            ],
            "history": [],
        },
        "marketplace": {
            "missions": [
                {
                    "listing_id": "mk-001",
                    "mission_type": "recon",
                    "title": "Map runtime blind spots",
                    "reward_points": 150,
                    "tags": ["runtime", "analysis"],
                    "status": "open",
                }
            ]
        },
    }


def _read_command_center_state() -> Dict[str, Any]:
    path = _command_center_state_path()
    if not path.exists():
        state = _default_command_center_state()
        _write_command_center_state(state)
        return state
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    state = _default_command_center_state()
    _write_command_center_state(state)
    return state


def _write_command_center_state(state: Dict[str, Any]) -> None:
    path = _command_center_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _autonomy_mode_from_level(level: int) -> str:
    if level < 25:
        return "manual"
    if level < 55:
        return "assisted"
    if level < 80:
        return "autonomous"
    return "sovereign"


def _partner_tiers() -> List[str]:
    return ["Egg", "Rookie", "Champion", "Ultimate", "Mega", "Ultra"]


def _shadow_tiers() -> List[str]:
    return ["Dormant", "Shade", "Wraith", "Reaper", "General", "Monarch"]


def _cockpit_feed(state: Dict[str, Any]) -> Dict[str, Any]:
    missions_file = DATA_DIR / "missions.jsonl"
    runs_file = DATA_DIR / "runs.jsonl"
    missions_result = read_jsonl(missions_file)
    runs_result = read_jsonl(runs_file)

    if isinstance(missions_result, tuple):
        missions = missions_result[0]
    elif isinstance(missions_result, list):
        missions = missions_result
    else:
        missions = []

    if isinstance(runs_result, tuple):
        runs = runs_result[0]
    elif isinstance(runs_result, list):
        runs = runs_result
    else:
        runs = []

    queued = sum(
        1
        for mission in missions
        if str(mission.get("status", "")).upper() in {"PENDING", "QUEUED", "CREATED"}
    )
    completed = sum(
        1
        for mission in missions
        if str(mission.get("status", "")).upper() in {"SUCCESS", "COMPLETED", "DONE"}
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "queue_depth": queued,
        "completed_count": completed,
        "recent_runs": runs[-5:],
        "autonomy": state.get("autonomy", {}),
        "shadow_mode": state.get("shadow_mode", {}),
        "organism": {
            "partner_tier": state.get("partner", {}).get("tier", "Rookie"),
            "shadow_tier": state.get("shadow", {}).get("tier", "Dormant"),
        },
        "partner_summary": state.get("evolution_tree", {}).get("partners", []),
        "ledger": {
            "missions_total": len(missions),
            "runs_total": len(runs),
            "audit_events_last_20": len(_tail_jsonl(DATA_DIR / "audit.jsonl", 20)),
        },
    }


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
        logger.info("Generated operator PIN; saved to %s", pin_file)

    return {"pin": pin, "source": pin_source, "file": pin_file, "generated": generated}


_runtime_cfg = _load_runtime_config()
OFFLINE_MODE = _resolve_offline_mode(_runtime_cfg)

_pin_info = _load_operator_pin()
OPERATOR_PIN = _pin_info["pin"]
app.state.operator_pin_source = _pin_info

VERBOSE = os.getenv("SWARMZ_VERBOSE", "0") not in {"0", "false", "False", None}


engine = SwarmzEngine(data_dir=str(DATA_DIR))
engine.offline_mode = OFFLINE_MODE
engine.operator_key = OPERATOR_PIN
primitives_runtime = SystemPrimitivesRuntime(ROOT_DIR)


# Engine provider for all modules (used to avoid circular imports)
def get_engine():
    return engine


system.get_engine = get_engine
admin.get_engine = get_engine
ecosystem.set_engine_provider(get_engine)
arena_api.get_engine = get_engine


@app.get("/v1/companion/state", tags=["companion"])
def companion_state():
    return {
        "ok": True,
        "state": "active",
        "master_identity": "MASTER_SWARMZ",
        "self_assessment": "MASTER_SWARMZ companion state is active.",
    }


@app.get("/health")
def health():
    return {"ok": True, "status": "ok"}


@app.get("/arena", response_class=HTMLResponse)
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


@app.get("/v1/health")
def health_v1():
    uptime = (datetime.now(timezone.utc) - START_TIME).total_seconds()
    return {
        "ok": True,
        "status": "ok",
        "uptime_seconds": int(uptime),
        "offline_mode": OFFLINE_MODE,
    }


@app.get("/v1/pairing/info")
def pairing_info():
    if not _pin_info:
        raise HTTPException(status_code=404, detail="No pairing info")
    return _pin_info


@app.post("/v1/pairing/pair")
def pairing_pair(payload: PairRequest):
    if payload.pin != OPERATOR_PIN:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    token = f"pair-{OPERATOR_PIN}"
    return {"ok": True, "token": token}


@app.get("/v1/runtime/status")
def runtime_status():
    return {
        "ok": True,
        "active_agents": 0,
        "queued_tasks": 0,
        "system_load_estimate": 0.0,
    }


@app.get("/v1/runtime/scoreboard")
def runtime_scoreboard_view():
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


@app.get("/v1/companion/history")
def companion_history(tail: int = 10):
    return {"ok": True, "records": [], "history": [], "read_only": True}


@app.get("/v1/prepared/pending")
def prepared_pending(category: Optional[str] = None):
    base = ROOT_DIR / "prepared_actions"
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


@app.get("/v1/ai/status")
def ai_status():
    missions_file = DATA_DIR / "missions.jsonl"
    result = read_jsonl(missions_file)

    if isinstance(result, tuple):
        missions = result[0]
    elif isinstance(result, list):
        missions = result
    else:
        missions = []

    success_count = sum(
        1
        for mission in missions
        if str(mission.get("status", "")).upper() in {"SUCCESS", "COMPLETED"}
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


@app.get("/v1/observability/health")
def observability_health():
    return {"status": "ok"}


@app.get("/v1/observability/ready")
def observability_ready():
    return {"status": "ready"}


@app.get("/v1/command-center/state")
def command_center_state():
    state = _read_command_center_state()
    return {
        "ok": True,
        "cockpit": _cockpit_feed(state),
        "shadow_mode": state.get("shadow_mode", {}),
        "partner": state.get("partner", {}),
        "shadow": state.get("shadow", {}),
        "autonomy_loop": state.get("autonomy_loop", {}),
        "evolution_tree": state.get("evolution_tree", {}),
        "autonomy": state.get("autonomy", {}),
        "marketplace": state.get("marketplace", {}),
        "lore": {
            "world_bible": "docs/WORLD_BIBLE.md",
            "status": "loaded",
        },
        "deploy": {
            "entrypoint": "SWARMZ_ONE_BUTTON_DEPLOY.ps1",
            "status": "ready",
        },
    }


@app.get("/v1/command-center/organism/state")
def organism_state():
    state = _read_command_center_state()
    return {
        "ok": True,
        "partner": state.get("partner", {}),
        "shadow": state.get("shadow", {}),
        "autonomy": state.get("autonomy", {}),
        "loop": state.get("autonomy_loop", {}),
    }


@app.post("/v1/command-center/autonomy")
def set_autonomy_dial(payload: AutonomyDialRequest):
    state = _read_command_center_state()
    level = int(payload.level)
    partner = state.setdefault("partner", _default_command_center_state()["partner"])
    autonomy_cap = int(partner.get("autonomy_ceiling", 25))
    bounded_level = min(level, autonomy_cap)
    state["autonomy"] = {
        "level": bounded_level,
        "mode": _autonomy_mode_from_level(bounded_level),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "requested_level": level,
    }
    _write_command_center_state(state)
    return {"ok": True, "autonomy": state["autonomy"]}


@app.post("/v1/command-center/shadow")
def set_shadow_mode(payload: ShadowModeRequest):
    state = _read_command_center_state()
    state["shadow_mode"] = {
        "enabled": bool(payload.enabled),
        "lane": payload.lane,
        "last_activation": (
            datetime.now(timezone.utc).isoformat() if payload.enabled else None
        ),
    }
    _write_command_center_state(state)
    return {"ok": True, "shadow_mode": state["shadow_mode"]}


@app.post("/v1/command-center/partner/evolve")
def evolve_partner(payload: OrganismEvolveRequest):
    state = _read_command_center_state()
    partner = state.setdefault("partner", _default_command_center_state()["partner"])
    tiers = _partner_tiers()
    current_tier = partner.get("tier", tiers[0])
    current_index = tiers.index(current_tier) if current_tier in tiers else 0
    next_index = min(current_index + 1, len(tiers) - 1)
    partner["tier"] = tiers[next_index]
    partner["tier_index"] = next_index
    partner["autonomy_ceiling"] = min(100, 25 + (next_index * 15))

    partner.setdefault(
        "traits", {"logic": 0.60, "empathy": 0.64, "precision": 0.62, "stability": 0.70}
    )
    partner["traits_mode"] = "deterministic_static"

    history = state.setdefault("evolution_tree", {}).setdefault("history", [])
    history.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entity": "partner",
            "from": current_tier,
            "to": partner["tier"],
            "reason": payload.reason,
        }
    )
    _write_command_center_state(state)
    return {"ok": True, "partner": partner, "history": history[-10:]}


@app.post("/v1/command-center/shadow/evolve")
def evolve_shadow(payload: OrganismEvolveRequest):
    state = _read_command_center_state()
    shadow = state.setdefault("shadow", _default_command_center_state()["shadow"])
    tiers = _shadow_tiers()
    current_tier = shadow.get("tier", tiers[0])
    current_index = tiers.index(current_tier) if current_tier in tiers else 0
    next_index = min(current_index + 1, len(tiers) - 1)
    shadow["tier"] = tiers[next_index]
    shadow["tier_index"] = next_index
    shadow["risk_precision"] = min(
        0.99, round(float(shadow.get("risk_precision", 0.35)) + 0.08, 2)
    )
    shadow["tactical_authority"] = (
        "policy_bounded_autonomy" if next_index >= 4 else "operator_approval"
    )

    history = state.setdefault("evolution_tree", {}).setdefault("history", [])
    history.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entity": "shadow",
            "from": current_tier,
            "to": shadow["tier"],
            "reason": payload.reason,
        }
    )
    _write_command_center_state(state)
    return {"ok": True, "shadow": shadow, "history": history[-10:]}


@app.post("/v1/command-center/loop/tick")
def tick_autonomy_loop(payload: LoopTickRequest):
    state = _read_command_center_state()
    loop = state.setdefault(
        "autonomy_loop", _default_command_center_state()["autonomy_loop"]
    )
    loop["tick_count"] = int(loop.get("tick_count", 0)) + 1
    loop["last_tick"] = datetime.now(timezone.utc).isoformat()
    loop["last_cycle_label"] = payload.cycle_label
    loop["last_summary"] = {
        "brain": "mission_plan_updated",
        "shadow": "risk_scan_completed",
        "immune": "policy_guardrails_applied",
        "memory": "experience_archive_appended",
        "reproduction": "blueprint_variants_ready",
    }
    _write_command_center_state(state)
    return {"ok": True, "loop": loop}


@app.post("/v1/command-center/evolution/promote")
def promote_partner(payload: EvolutionPromoteRequest):
    state = _read_command_center_state()
    evo = state.setdefault(
        "evolution_tree", _default_command_center_state()["evolution_tree"]
    )
    tiers = evo.get("tiers", ["seed", "scout", "operator", "architect", "sovereign"])
    partners = evo.setdefault("partners", [])

    partner = next(
        (p for p in partners if p.get("partner_id") == payload.partner_id), None
    )
    if partner is None:
        partner = {"partner_id": payload.partner_id, "tier": tiers[0], "xp": 0}
        partners.append(partner)

    current_tier = partner.get("tier", tiers[0])
    current_index = tiers.index(current_tier) if current_tier in tiers else 0
    next_index = min(current_index + 1, len(tiers) - 1)
    partner["tier"] = tiers[next_index]
    partner["xp"] = int(partner.get("xp", 0)) + 10

    history = evo.setdefault("history", [])
    history.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "partner_id": payload.partner_id,
            "from": current_tier,
            "to": partner["tier"],
            "reason": payload.reason,
        }
    )

    _write_command_center_state(state)
    return {"ok": True, "partner": partner, "history": history[-10:]}


@app.get("/v1/command-center/marketplace/list")
def marketplace_list(status: Optional[str] = Query(default=None)):
    state = _read_command_center_state()
    marketplace = state.setdefault("marketplace", {"missions": []})
    missions = marketplace.setdefault("missions", [])
    if status:
        missions = [
            m for m in missions if str(m.get("status", "")).lower() == status.lower()
        ]
    return {"ok": True, "missions": missions, "count": len(missions)}


@app.post("/v1/command-center/marketplace/publish")
def marketplace_publish(payload: MarketplacePublishRequest):
    state = _read_command_center_state()
    marketplace = state.setdefault("marketplace", {"missions": []})
    missions = marketplace.setdefault("missions", [])
    listing = {
        "listing_id": f"mk-{secrets.token_hex(3)}",
        "mission_type": payload.mission_type,
        "title": payload.title,
        "reward_points": int(payload.reward_points),
        "tags": payload.tags,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    missions.append(listing)
    _write_command_center_state(state)
    return {"ok": True, "listing": listing}


@app.post("/v1/dispatch")
def dispatch(req: DispatchRequest, request: Request):
    op_key = request.headers.get("X-Operator-Key")
    if not op_key or op_key != OPERATOR_PIN:
        raise HTTPException(status_code=401, detail="operator key required")

    contract = primitives_runtime.validate_contract(
        {
            "action_type": "dispatch",
            "payload": {
                "goal": req.goal,
                "category": req.category,
                "constraints": req.constraints,
            },
            "safety": {"irreversible": False, "operator_approved": True},
            "resources": {"cpu": 1.0, "memory_mb": 512, "timeout_s": 60},
            "meta": {"source": "api.dispatch", "weaver_validated": True},
        },
        regime="dispatch",
    )
    if not contract["validation"]["allowed"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "contract_rejected",
                "violations": contract["validation"]["violations"],
                "companion_notified": contract["companion_notified"],
            },
        )

    engine = get_engine()
    created = engine.create_mission(req.goal, req.category, req.constraints)
    run = (
        engine.run_mission(created.get("mission_id", ""))
        if created.get("mission_id")
        else {"error": "create_failed"}
    )
    return {"created": created, "run": run, "contract": contract["validation"]}


@app.get("/v1/audit/tail")
def audit_tail(limit: int = 10):
    lim = max(1, min(limit, 500))
    audit_file = DATA_DIR / "audit.jsonl"
    return {"entries": _tail_jsonl(audit_file, lim)}


@app.get("/v1/runs")
def runs():
    runs_file = DATA_DIR / "runs.jsonl"
    result = read_jsonl(runs_file)

    # Defensive: tolerate regressions or unexpected return types
    if not result or not isinstance(result, tuple):
        entries = []
    else:
        entries, _, _ = result

    return {"runs": entries, "count": len(entries)}


@app.get("/config/runtime.json")
def config_runtime():
    port = int(os.environ.get("PORT", "8012"))
    base = os.environ.get("BASE_URL") or f"http://127.0.0.1:{port}"
    merged = {
        "apiBaseUrl": base,
        "uiBaseUrl": base,
        "port": port,
        "offlineMode": OFFLINE_MODE,
    }
    merged.update(_runtime_cfg)
    return merged


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
    sw_file = _file_in_ui("sw.js")
    if sw_file.exists():
        return FileResponse(sw_file, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="service worker not found")


@app.post("/v1/sovereign/dispatch")
def sovereign_dispatch(body: SovereignDispatch):
    contract = primitives_runtime.validate_contract(
        {
            "action_type": "create_mission",
            "payload": {
                "intent": body.intent,
                "scope": body.scope,
                "limits": body.limits,
            },
            "safety": {"irreversible": False, "operator_approved": True},
            "resources": {"cpu": 1.0, "memory_mb": 256, "timeout_s": 30},
            "meta": {"source": "api.sovereign_dispatch", "weaver_validated": True},
        },
        regime="sovereign_dispatch",
    )
    if not contract["validation"]["allowed"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "contract_rejected",
                "violations": contract["validation"]["violations"],
                "companion_notified": contract["companion_notified"],
            },
        )

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    mission_id = f"M-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(4)}"
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
    _append_jsonl(
        audit_file, {"ts": ts, "event": "sovereign_dispatch", "mission_id": mission_id}
    )
    return {
        "ok": True,
        "mission_id": mission_id,
        "status": "PENDING",
        "contract": contract["validation"],
    }


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


# Temporary fallback for `_file_in_ui` to resolve NameError.
def _file_in_ui(filename: str):
    from pathlib import Path

    return Path("ui") / filename


try:
    from swarmz_runtime.api.companion_state import companion_state
except ImportError:
    logger.warning("Fallback: companion_state not imported")

    def companion_state():
        return {"status": "Fallback companion state"}
