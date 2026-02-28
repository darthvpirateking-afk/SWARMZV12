# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
SWARMZ Web Server - PWA-enabled REST API

A FastAPI-based web server that exposes SWARMZ capabilities via REST API
and serves a Progressive Web App for mobile-friendly access.
"""

import os
import socket
import json
import logging
import traceback
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from jsonl_utils import read_jsonl, write_jsonl
from core.activity_stream import record_event
from addons.auth_gate import LANAuthMiddleware
from addons.rate_limiter import RateLimitMiddleware
from addons.security import (
    IDSMiddleware,
    RoleChecker,
    append_security_event,
    create_access_token,
    get_current_user,
    honeypot_endpoint,
    security_status_snapshot,
)
from timeline_store import load_timeline, get_stats

try:
    from swarmz import SwarmzCore

    _swarmz_core = SwarmzCore()
except Exception:
    _swarmz_core = None

# Import NEXUSMON router for conversational interface
try:
    from core.nexusmon_router import router as nexusmon_router

    _nexusmon_available = True
except Exception as e:
    _nexusmon_available = False
    print(f"Warning: NEXUSMON router not available: {e}")

try:
    from api.bootstrap_routes import router as bootstrap_router

    _bootstrap_router_available = True
except Exception as e:
    _bootstrap_router_available = False
    print(f"Warning: bootstrap router not available: {e}")

try:
    from api.foundation_routes import build_foundation_router

    _foundation_router_available = True
except Exception as e:
    _foundation_router_available = False
    print(f"Warning: foundation router not available: {e}")

try:
    from api.database_routes import router as database_router

    _database_router_available = True
except Exception as e:
    _database_router_available = False
    print(f"Warning: database router not available: {e}")

try:
    from api.operator_auth_routes import router as operator_auth_router

    _operator_auth_router_available = True
except Exception as e:
    _operator_auth_router_available = False
    print(f"Warning: operator auth router not available: {e}")

try:
    from api.companion_core_routes import router as companion_core_router

    _companion_core_router_available = True
except Exception as e:
    _companion_core_router_available = False
    print(f"Warning: companion core router not available: {e}")

try:
    from api.build_milestones_routes import router as build_milestones_router

    _build_milestones_router_available = True
except Exception as e:
    _build_milestones_router_available = False
    print(f"Warning: build milestones router not available: {e}")

try:
    from api.claimlab_routes import router as claimlab_router

    _claimlab_router_available = True
except Exception as e:
    _claimlab_router_available = False
    print(f"Warning: ClaimLab router not available: {e}")

try:
    from nexusmon_plugins import router as plugins_router

    _plugins_router_available = True
except Exception as e:
    _plugins_router_available = False
    print(f"Warning: plugin ecosystem router not available: {e}")

try:
    from core.governance_router import router as governance_router

    _governance_router_available = True
except Exception as e:
    _governance_router_available = False
    print(f"Warning: governance router not available: {e}")

try:
    from swarmz_runtime.api.system_control import router as system_control_router

    _system_control_router_available = True
except Exception as e:
    _system_control_router_available = False
    print(f"Warning: system control router not available: {e}")

try:
    from swarmz_runtime.api.mission_lifecycle import router as mission_lifecycle_router

    _mission_lifecycle_router_available = True
except Exception as e:
    _mission_lifecycle_router_available = False
    print(f"Warning: mission lifecycle router not available: {e}")

try:
    from backend.cockpit_telemetry import router as cockpit_router

    _cockpit_router_available = True
except Exception as e:
    _cockpit_router_available = False
    print(f"Warning: cockpit telemetry router not available: {e}")

try:
    from backend.health_model import router as health_router

    _health_router_available = True
except Exception as e:
    _health_router_available = False
    print(f"Warning: health router not available: {e}")

try:
    from backend.autonomous_runtime import router as nexusmon_autonomous_router

    _nexusmon_autonomous_router_available = True
except Exception as e:
    _nexusmon_autonomous_router_available = False
    print(f"Warning: autonomous runtime router not available: {e}")

try:
    from backend.proposal_registry import router as proposal_router

    _proposal_router_available = True
except Exception as e:
    _proposal_router_available = False
    print(f"Warning: proposal router not available: {e}")

try:
    from backend.code_drafting_engine import router as drafting_router

    _drafting_router_available = True
except Exception as e:
    _drafting_router_available = False
    print(f"Warning: drafting router not available: {e}")

try:
    from backend.evolution_planner_api import router as planner_router

    _planner_router_available = True
except Exception as e:
    _planner_router_available = False
    print(f"Warning: planner router not available: {e}")

try:
    from backend.refactor_api import router as refactor_router

    _refactor_router_available = True
except Exception as e:
    _refactor_router_available = False
    print(f"Warning: refactor router not available: {e}")

try:
    from backend.simulation_api import router as simulation_router

    _simulation_router_available = True
except Exception as e:
    _simulation_router_available = False
    print(f"Warning: simulation router not available: {e}")

try:
    from backend.symbolic_api import router as symbolic_router

    _symbolic_router_available = True
except Exception as e:
    _symbolic_router_available = False
    print(f"Warning: symbolic router not available: {e}")

try:
    from backend.life_api import router as life_router

    _life_router_available = True
except Exception as e:
    _life_router_available = False
    print(f"Warning: life router not available: {e}")

try:
    from backend.intel.vuln_db_client import search_vulnerabilities
except Exception:
    search_vulnerabilities = None

try:
    from backend.intel.firecrawl_pipeline import run_firecrawl_pipeline
except Exception:
    run_firecrawl_pipeline = None

try:
    from backend.missions.phase_pipeline import run_phase_pipeline
except Exception:
    run_phase_pipeline = None


def get_lan_ip() -> str:
    """Best-effort LAN IP discovery (fallback to loopback)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
        record_event(
            {
                "event": "lan_ip_discovery",
                "ip": lan_ip,
                "timestamp": datetime.now().isoformat(),
            }
        )
        return lan_ip
    except Exception:
        return "127.0.0.1"


def _utc_now_iso_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


SERVER_PORT = int(os.environ.get("PORT", "8000"))
LAN_IP = get_lan_ip()

# Ensure data dir exists before anything writes to it
Path("data").mkdir(parents=True, exist_ok=True)

# Canonical SQLite DB path for this process (shared by app + subprocess tools)
_container_db = "/app/data/nexusmon.db"
_local_db = str((Path(__file__).resolve().parent / "data" / "nexusmon.db"))
DB_PATH = os.environ.get("DATABASE_URL") or (
    _container_db if Path("/app").exists() else _local_db
)
os.environ.setdefault("DATABASE_URL", DB_PATH)


# API Models
class TaskExecuteRequest(BaseModel):
    task: str
    params: Dict[str, Any] = {}


class TaskExecuteResponse(BaseModel):
    success: bool
    result: Any = None
    error: Optional[str] = None


class MissionCreateRequest(BaseModel):
    goal: str = Field(..., description="Mission goal")
    category: str = Field(..., description="Mission category")
    constraints: Dict[str, Any] = Field(default_factory=dict)
    results: Dict[str, Any] = Field(default_factory=dict)


class LoginRequest(BaseModel):
    username: str
    password: str


class FirecrawlRequest(BaseModel):
    mission_id: str = Field(
        ..., description="Mission identifier used for output correlation"
    )
    url: str = Field(
        ..., description="Primary target URL for recon and content analysis"
    )
    content: str = Field(
        "",
        description="Optional downloaded page/content text to feed secret scanning",
    )
    js_detected: bool = Field(
        False,
        description="Set true when target appears JS-heavy and browser recon should run",
    )
    curiosity: int = Field(50, ge=0, le=100, description="Trait gate for recon depth")
    creativity: int = Field(
        50, ge=0, le=100, description="Trait gate for route/auth analysis"
    )
    patience: int = Field(
        50, ge=0, le=100, description="Trait gate for page depth and timeouts"
    )
    aggression: int = Field(
        30, ge=0, le=100, description="Trait gate for attack-surface extraction"
    )


class PhaseRunRequest(BaseModel):
    mission_id: str = Field(..., description="Mission identifier for phase execution")
    autonomy: int = Field(
        50, ge=0, le=100, description="Trait gate for autonomous setup actions"
    )
    protectiveness: int = Field(
        50,
        ge=0,
        le=100,
        description="Trait gate for VPN/debug safeguards and safety enforcement",
    )
    patience: int = Field(
        50, ge=0, le=100, description="Trait gate for debug trace depth and waits"
    )
    fail: bool = Field(
        False,
        description="Test switch to simulate mission failure and verify guaranteed cleanup",
    )


class Helper1RunRequest(BaseModel):
    query: str = Field("", description="Helper1 task query")


class RealityGateRunRequest(BaseModel):
    command: str = Field("", description="Reality gate command")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Reality gate payload")


class MissionTemplateRunRequest(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict, description="Mission payload")
    operator_approved: bool = Field(False, description="Explicit operator approval flag for strict mode")


class MissionEngineRunRequest(BaseModel):
    template_id: str = Field("", description="Canonical mission template ID")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Mission input payload")


# Initialize FastAPI app
app = FastAPI(
    title="SWARMZ API",
    description="Operator-Sovereign 'Do Anything' System - REST API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/docs/openapi.json",
)

# Core security middlewares (all conservative / opt-out via config):
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LANAuthMiddleware)
app.add_middleware(IDSMiddleware)

# Add CORS middleware â€” allow_credentials=True requires explicit origins (not "*")
_raw_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:4173,http://127.0.0.1:5173",
)
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include NEXUSMON conversational interface router
if _nexusmon_available:
    app.include_router(nexusmon_router)

# Include NEXUSMON entity state routes (/v1/nexusmon/entity/*)
try:
    from nexusmon.routes.entity import router as _nexus_entity_router

    app.include_router(_nexus_entity_router)
except Exception as _e:
    pass  # Non-fatal if entity routes fail to load

if _bootstrap_router_available:
    app.include_router(bootstrap_router)

if _foundation_router_available:
    app.include_router(build_foundation_router(app))

if _database_router_available:
    app.include_router(database_router)

if _operator_auth_router_available:
    app.include_router(operator_auth_router)

if _companion_core_router_available:
    app.include_router(companion_core_router)

if _build_milestones_router_available:
    app.include_router(build_milestones_router)

if _claimlab_router_available:
    app.include_router(claimlab_router)

if _plugins_router_available:
    app.include_router(plugins_router)

if _governance_router_available:
    app.include_router(governance_router)

if _system_control_router_available:
    app.include_router(
        system_control_router, prefix="/v1/system", tags=["system-control"]
    )

if _mission_lifecycle_router_available:
    app.include_router(
        mission_lifecycle_router, prefix="/v1/missions", tags=["mission-lifecycle"]
    )

if _cockpit_router_available:
    app.include_router(cockpit_router)

if _health_router_available:
    app.include_router(health_router)

if _nexusmon_autonomous_router_available:
    app.include_router(nexusmon_autonomous_router)

if _proposal_router_available:
    app.include_router(proposal_router)

if _drafting_router_available:
    app.include_router(drafting_router)

if _planner_router_available:
    app.include_router(planner_router)

if _refactor_router_available:
    app.include_router(refactor_router)

if _simulation_router_available:
    app.include_router(simulation_router)

if _symbolic_router_available:
    app.include_router(symbolic_router)

if _life_router_available:
    app.include_router(life_router)

# Include the new tab loader routes
# app.include_router(app.router, prefix="/v1/tabs")

# Setup logging
logging.basicConfig(
    filename="data/server_live.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# Global state for exception tracking
last_exception_traceback = None
CANONICAL_TRACE_BUFFER: deque[dict[str, Any]] = deque(maxlen=200)


def _load_runtime_config() -> dict[str, Any]:
    try:
        from core.config_loader import load_config

        cfg = load_config() or {}
        return cfg if isinstance(cfg, dict) else {}
    except Exception:
        return {}


def _canonical_lane_policy() -> dict[str, Any]:
    cfg = _load_runtime_config()
    lane = cfg.get("canonical_lane", {}) if isinstance(cfg, dict) else {}
    return {
        "strict_mode": bool(lane.get("strict_mode", True)),
        "auto_approve": bool(lane.get("auto_approve", False)),
        "require_operator_approval": bool(lane.get("require_operator_approval", True)),
    }


def _canonical_operator_approved(request: Request, explicit_flag: bool = False) -> bool:
    policy = _canonical_lane_policy()
    if not policy["strict_mode"]:
        return True
    if policy["auto_approve"]:
        return True
    if not policy["require_operator_approval"]:
        return True
    header = request.headers.get("X-Operator-Approval", "")
    return explicit_flag or header.strip().lower() in {"1", "true", "approved", "yes"}


def _append_canonical_trace(event: dict[str, Any]) -> None:
    stamped = {"ts": _utc_now_iso_z(), **event}
    CANONICAL_TRACE_BUFFER.append(stamped)


def _load_canonical_templates() -> list[dict[str, Any]]:
    templates_dir = Path("config/missions")
    if not templates_dir.exists():
        return []
    templates: list[dict[str, Any]] = []
    for fp in sorted(templates_dir.glob("*.template.json")):
        try:
            templates.append(json.loads(fp.read_text(encoding="utf-8-sig")))
        except Exception:
            continue
    return templates


@app.exception_handler(Exception)
async def json_exception_handler(request: Request, exc: Exception):
    global last_exception_traceback
    tb = traceback.format_exc()
    last_exception_traceback = tb
    logging.error(f"Exception: {exc}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"ok": False, "error": str(exc), "traceback": tb.splitlines()[-5:]},
    )


# --- Mission endpoints ---
@app.post("/v1/missions/create")
async def create_mission(req: MissionCreateRequest):
    """Create a new mission."""
    missions_file = Path("data/missions.jsonl")
    audit_file = Path("data/audit.jsonl")
    mission_id = f"mission_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
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
    write_jsonl(missions_file, mission)
    audit_event = {
        "event": "mission_created",
        "mission_id": mission_id,
        "timestamp": created_at,
        "goal": req.goal,
        "category": req.category,
    }
    write_jsonl(audit_file, audit_event)
    return {
        "ok": True,
        "mission_id": mission_id,
        "status": "PENDING",
        "created_at": created_at,
        "goal": req.goal,
        "category": req.category,
    }


@app.get("/v1/missions/list")
async def list_missions():
    """List all missions."""
    missions_file = Path("data/missions.jsonl")
    missions, skipped, quarantined = read_jsonl(missions_file)
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


@app.post("/v1/missions/run")
async def run_mission(mission_id: str = None):
    """Run/execute a mission by ID."""
    if not mission_id:
        return {"ok": False, "error": "mission_id required"}
    missions_file = Path("data/missions.jsonl")
    missions, _, _ = read_jsonl(missions_file)
    mission = next((m for m in missions if m.get("mission_id") == mission_id), None)
    if not mission:
        return {"ok": False, "error": f"mission_id {mission_id} not found"}
    started_at = _utc_now_iso_z()
    mission["status"] = "RUNNING"
    mission["started_at"] = started_at
    try:
        from nexusmon_organism import ctx_record_mission

        ctx_record_mission(mission_id, mission.get("category", "unknown"), "RUNNING")
    except Exception:
        pass
    missions_file.write_text("")
    for m in missions:
        write_jsonl(missions_file, m)
    audit_file = Path("data/audit.jsonl")
    audit_event = {
        "event": "mission_run",
        "mission_id": mission_id,
        "timestamp": started_at,
    }
    write_jsonl(audit_file, audit_event)
    return {
        "ok": True,
        "mission_id": mission_id,
        "status": "RUNNING",
        "started_at": started_at,
    }


# --- UI state endpoint ---
def compute_phase(total_missions: int, success_count: int) -> str:
    """Compute phase based on mission counts and success rate.
    QUARANTINE only when total >= 10 AND success_rate < 0.3.
    Under 10 missions is always AWAKENING.
    """
    if total_missions < 10:
        return "AWAKENING"
    success_rate = success_count / total_missions if total_missions > 0 else 0.0
    if success_rate < 0.3:
        return "QUARANTINE"
    if total_missions < 50:
        return "FORGING"
    return "SOVEREIGN"


@app.get("/v1/ui/state")
async def ui_state():
    """Get UI state including server, missions, and phase."""
    missions_file = Path("data/missions.jsonl")
    audit_file = Path("data/audit.jsonl")
    missions, _, _ = read_jsonl(missions_file)
    audit_events, _, _ = read_jsonl(audit_file)

    status_counts = {}
    success_count = 0
    for m in missions:
        status = m.get("status", "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
        if status == "SUCCESS":
            success_count += 1

    last_events = audit_events[-10:] if audit_events else []
    phase = compute_phase(len(missions), success_count)

    organism_stage = None
    try:
        from nexusmon_organism import evo_status

        organism_stage = evo_status().get("stage")
    except Exception:
        pass

    now = _utc_now_iso_z()
    return {
        "ok": True,
        "server": {
            "version": "1.0.0",
            "now": now,
            "lan_url": f"http://{LAN_IP}:{SERVER_PORT}",
            "local_url": f"http://127.0.0.1:{SERVER_PORT}",
        },
        "missions": {"count_total": len(missions), "count_by_status": status_counts},
        "last_events": last_events,
        "phase": phase,
        "organism_stage": organism_stage,
    }


@app.get("/v1/debug/traceback_last")
async def traceback_last():
    """Get the last exception traceback."""
    return {
        "ok": True,
        "traceback": last_exception_traceback or "No exception recorded",
    }


# --- Console UI Route (redirects to NEXUSMON) ---
@app.get("/console")
async def console_page():
    """Serve the NEXUSMON Console UI."""
    return RedirectResponse(url="/cockpit/", status_code=307)


@app.get("/organism")
async def organism_cockpit():
    """NEXUSMON Organism Cockpit â€” evolution, workers, companion, operator context."""
    return RedirectResponse(url="/cockpit/", status_code=307)


@app.get("/claimlab")
async def claimlab_page():
    """Serve the ClaimLab epistemic scaffolding UI."""
    return RedirectResponse(url="/cockpit/", status_code=307)


@app.get("/landing")
async def nexusmon_landing():
    """Public landing page for NEXUSMON."""
    return RedirectResponse(url="/cockpit/", status_code=307)


@app.get("/avatar", operation_id="avatar_page_main")
async def avatar_page():
    """NEXUSMON Avatar â€” holographic companion interface."""
    return RedirectResponse(url="/cockpit/", status_code=307)


# --- Home route â€” NEXUSMON is the face of this system ---
@app.get("/")
async def home_page():
    """Redirect root route to canonical cockpit."""
    return RedirectResponse(url="/cockpit/", status_code=307)


# --- Manifest, Icons, and Other PWA Routes ---
@app.get("/manifest.webmanifest")
async def manifest():
    """Serve the PWA manifest."""
    manifest_data = {
        "name": "SWARMZ - Operator-Sovereign System",
        "short_name": "SWARMZ",
        "description": "Operator-Sovereign 'Do Anything' System - Execute tasks with complete control",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#667eea",
        "theme_color": "#6366f1",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/icon.svg",
                "type": "image/svg+xml",
                "sizes": "any",
                "purpose": "any maskable",
            },
            {
                "src": "/apple-touch-icon.svg",
                "type": "image/svg+xml",
                "sizes": "180x180",
            },
        ],
        "categories": ["productivity", "utilities", "developer tools"],
        "screenshots": [],
    }
    return JSONResponse(content=manifest_data)


@app.get("/pwa/manifest.json")
async def pwa_manifest():
    """Serve PWA manifest for phone mode."""
    manifest_data = {
        "name": "SWARMZ Console",
        "short_name": "SWARMZ",
        "description": "Operator-Sovereign control surface",
        "start_url": "/console",
        "scope": "/",
        "display": "standalone",
        "background_color": "#667eea",
        "theme_color": "#6366f1",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/icon.svg",
                "type": "image/svg+xml",
                "sizes": "any",
                "purpose": "any maskable",
            },
            {
                "src": "/apple-touch-icon.svg",
                "type": "image/svg+xml",
                "sizes": "180x180",
            },
        ],
        "categories": ["productivity", "utilities"],
        "screenshots": [],
    }
    return JSONResponse(content=manifest_data)


# Service Worker
@app.get("/sw.js")
async def service_worker():
    """Serve the service worker script."""
    sw_js = """
const CACHE_NAME = 'swarmz-v1';
const CACHE_ASSETS = [
    '/',
    '/manifest.webmanifest',
    '/icon.svg',
    '/apple-touch-icon.svg'
];

// Install event - cache shell assets
self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Caching shell assets');
                return cache.addAll(CACHE_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - never cache APIs; cache-first for static shell only
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    if (url.pathname.startsWith('/v1/') || url.pathname.startsWith('/health')) {
        event.respondWith(fetch(request));
        return;
    }

    // Cache-first strategy for shell assets
    event.respondWith(
        caches.match(request)
            .then(cachedResponse => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                return fetch(request).then(response => {
                    // Cache new assets
                    if (request.method === 'GET') {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then(cache => {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                });
            })
    );
});
"""
    return HTMLResponse(content=sw_js, media_type="application/javascript")


@app.get("/pwa/sw.js")
async def pwa_service_worker():
    """Phone-mode service worker for offline shell cache."""
    sw_js = """
const CACHE_NAME = 'swarmz-shell-v1';
const SHELL = [
    '/',
    '/console',
    '/pwa/manifest.json',
    '/icon.svg',
    '/apple-touch-icon.svg'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => Promise.all(keys.map(k => k !== CACHE_NAME ? caches.delete(k) : null))).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', event => {
    const req = event.request;
    const url = new URL(req.url);

    // Keep API network-only (no cache)
    if (url.pathname.startsWith('/v1/') || url.pathname.startsWith('/health')) {
        event.respondWith(fetch(req));
        return;
    }

    // Navigation requests: offline fallback to /console
    if (req.mode === 'navigate') {
        event.respondWith(
            fetch(req).catch(() => caches.match('/console'))
        );
        return;
    }

    // Cache-first for shell assets
    event.respondWith(
        caches.match(req).then(cached => {
            if (cached) return cached;
            return fetch(req).then(res => {
                if (req.method === 'GET') {
                    const copy = res.clone();
                    caches.open(CACHE_NAME).then(c => c.put(req, copy));
                }
                return res;
            });
        })
    );
});
"""
    return HTMLResponse(content=sw_js, media_type="application/javascript")


# SVG Icons
@app.get("/icon.svg")
async def icon_svg():
    """Serve the app icon."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="40" fill="url(#grad)"/>
  <text x="100" y="130" font-family="Arial, sans-serif" font-size="100" font-weight="bold"
        text-anchor="middle" fill="#ffffff">Ã¢Å¡Â¡</text>
</svg>"""
    return HTMLResponse(content=svg, media_type="image/svg+xml")


@app.get("/apple-touch-icon.svg")
async def apple_touch_icon():
    """Serve the Apple touch icon."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 180">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="180" height="180" fill="url(#grad)"/>
  <text x="90" y="120" font-family="Arial, sans-serif" font-size="90" font-weight="bold"
        text-anchor="middle" fill="#ffffff">Ã¢Å¡Â¡</text>
</svg>"""
    return HTMLResponse(content=svg, media_type="image/svg+xml")


# REST API Endpoints
@app.get("/health", operation_id="swarmz_health")
async def health():
    """Platform health check endpoint (must stay fast and dependency-free)."""
    return {"status": "ok"}


@app.get("/v1/health", operation_id="swarmz_health_v1")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "SWARMZ API"}


@app.get("/ready", operation_id="swarmz_ready")
async def readiness():
    """Kubernetes readiness probe â€” returns 200 when the service is ready to
    accept traffic.  Extend with queue-depth / reconciler-thread checks as
    the system matures.
    """
    return {"status": "ready", "service": "SWARMZ API"}


@app.get("/health/ready", operation_id="swarmz_health_ready_compat")
async def health_ready_compat():
    """Compatibility readiness endpoint for UI clients."""
    return {"ok": True, "status": "ready"}


@app.get("/api/governor", operation_id="swarmz_governor_status_compat")
async def governor_status_compat():
    """Compatibility governor status endpoint for UI clients."""
    cfg = _load_runtime_config()

    operator_sovereignty = cfg.get("operator_sovereignty", {}) if isinstance(cfg, dict) else {}
    security = cfg.get("security", {}) if isinstance(cfg, dict) else {}

    auto_approve = bool(operator_sovereignty.get("auto_approve", False))
    require_operator_approval = bool(security.get("require_operator_approval", False))

    warnings = []
    if auto_approve:
        warnings.append("operator_sovereignty.auto_approve=true")
    if not require_operator_approval:
        warnings.append("security.require_operator_approval=false")

    return {
        "ok": True,
        "status": "ok",
        "governance": {
            "operator_sovereignty": {"auto_approve": auto_approve},
            "security": {"require_operator_approval": require_operator_approval},
            "canonical_lane": _canonical_lane_policy(),
        },
        "warnings": warnings,
    }


@app.post("/v1/agents/helper1/run", tags=["agent-runtime"], operation_id="helper1_run")
async def run_helper1_agent(req: Helper1RunRequest, request: Request):
    """Execute helper1 via canonical manifest + spawn context + capability gate."""
    from fastapi import HTTPException
    from core.agent_manifest import AgentManifest
    from core.spawn_context import SpawnContext
    from core.observability import AgentEvent, ObservabilityEmitter, inputs_hash
    from plugins.helper1 import run as helper1_run

    if not _canonical_operator_approved(request):
        raise HTTPException(status_code=403, detail="Operator approval required for canonical lane")

    manifest = AgentManifest.from_file("config/manifests/helper1.manifest.json")
    ctx = SpawnContext.root_from_manifest(manifest)

    # Deterministic local subset gate for this kernel slice endpoint.
    declared = set(manifest.capabilities)
    granted = {"data.read"}
    if not granted.issubset(declared):
        raise HTTPException(
            status_code=403,
            detail="Granted capabilities exceed declared manifest capabilities",
        )
    allowed = sorted(granted)

    result = helper1_run({"query": req.query})

    emitter = ObservabilityEmitter(success_sample_rate=1.0)
    emitter.emit(
        AgentEvent(
            agent_id=manifest.id,
            trace_id=ctx.trace_id,
            session_id=ctx.session_id,
            event="helper1.run",
            decision="execute",
            inputs_hash=inputs_hash({"query": req.query}),
            outcome="success",
            payload={"allowed_capabilities": allowed},
        )
    )
    _append_canonical_trace(
        {
            "trace_id": ctx.trace_id,
            "event": "agent.helper1.run",
            "agent_id": manifest.id,
            "outcome": "success",
        }
    )

    return {
        "ok": True,
        "agent_id": manifest.id,
        "trace_id": ctx.trace_id,
        "session_id": ctx.session_id,
        "allowed_capabilities": allowed,
        "result": result,
    }


@app.post("/v1/agents/reality_gate/run", tags=["agent-runtime"], operation_id="reality_gate_run")
async def run_reality_gate_agent(req: RealityGateRunRequest, request: Request):
    """Execute canonical reality_gate plugin with manifest + spawn + capability gate."""
    from fastapi import HTTPException
    from core.agent_manifest import AgentManifest
    from core.spawn_context import SpawnContext
    from core.observability import AgentEvent, ObservabilityEmitter, inputs_hash
    from plugins.reality_gate import RealityGatePlugin

    if not _canonical_operator_approved(request):
        raise HTTPException(status_code=403, detail="Operator approval required for canonical lane")

    manifest = AgentManifest.from_file("config/manifests/reality_gate.manifest.json")
    context = SpawnContext.root_from_manifest(manifest)

    declared = set(manifest.capabilities)
    command_capability_map = {
        "validate": "validate",
        "transform": "transform",
        "echo": "io.read",
    }
    mapped_cap = command_capability_map.get(req.command)
    granted = {mapped_cap} if mapped_cap else set()
    if granted and not granted.issubset(declared):
        raise HTTPException(
            status_code=403,
            detail="Granted capabilities exceed declared manifest capabilities",
        )

    plugin = RealityGatePlugin()
    await plugin.on_init(manifest, context)
    await plugin.on_activate(context)
    result = await plugin.run(req.command, req.payload)
    await plugin.on_deactivate(context)

    emitter = ObservabilityEmitter(success_sample_rate=1.0)
    emitter.emit(
        AgentEvent(
            agent_id=manifest.id,
            trace_id=context.trace_id,
            session_id=context.session_id,
            event="reality_gate.run",
            decision=req.command,
            inputs_hash=inputs_hash({"command": req.command, "payload": req.payload}),
            outcome="success" if "error" not in result else "failure",
            payload={"allowed_capabilities": sorted(granted) if granted else []},
        )
    )
    _append_canonical_trace(
        {
            "trace_id": context.trace_id,
            "event": "agent.reality_gate.run",
            "agent_id": manifest.id,
            "command": req.command,
            "outcome": "success" if "error" not in result else "failure",
        }
    )

    return {
        "ok": True,
        "agent": "reality_gate",
        "agent_id": manifest.id,
        "command": req.command,
        "result": result,
        "trace_id": context.trace_id,
        "session_id": context.session_id,
    }


@app.post("/v1/agents/mission_engine/run", tags=["agent-runtime"], operation_id="mission_engine_run")
async def run_mission_engine_agent(req: MissionEngineRunRequest, request: Request):
    """Execute canonical mission_engine plugin for a canonical template run."""
    from fastapi import HTTPException
    from core.agent_manifest import AgentManifest
    from core.spawn_context import SpawnContext
    from core.observability import AgentEvent, ObservabilityEmitter, inputs_hash
    from plugins.mission_engine import MissionEnginePlugin

    if not _canonical_operator_approved(request):
        raise HTTPException(status_code=403, detail="Operator approval required for canonical lane")

    templates = {t.get("id"): t for t in _load_canonical_templates() if isinstance(t, dict)}
    if req.template_id not in templates:
        raise HTTPException(status_code=404, detail=f"Template '{req.template_id}' not found")
    template = templates[req.template_id]

    manifest = AgentManifest.from_file("config/manifests/mission_engine.manifest.json")
    context = SpawnContext.root_from_manifest(manifest)

    declared = set(manifest.capabilities)
    granted = {"mission.execute"}
    if not granted.issubset(declared):
        raise HTTPException(
            status_code=403,
            detail="Granted capabilities exceed declared manifest capabilities",
        )

    plugin = MissionEnginePlugin()
    await plugin.on_init(manifest, context)
    await plugin.on_activate(context)
    result = await plugin.run(template, req.payload)
    await plugin.on_deactivate(context)

    emitter = ObservabilityEmitter(success_sample_rate=1.0)
    emitter.emit(
        AgentEvent(
            agent_id=manifest.id,
            trace_id=context.trace_id,
            session_id=context.session_id,
            event="mission_engine.run",
            decision=req.template_id,
            inputs_hash=inputs_hash({"template_id": req.template_id, "payload": req.payload}),
            outcome="success" if "error" not in result else "failure",
            payload={"allowed_capabilities": sorted(granted)},
        )
    )
    _append_canonical_trace(
        {
            "trace_id": context.trace_id,
            "event": "agent.mission_engine.run",
            "agent_id": manifest.id,
            "template_id": req.template_id,
            "outcome": "success" if "error" not in result else "failure",
        }
    )

    return {
        "ok": True,
        "agent": "mission_engine",
        "agent_id": manifest.id,
        "template_id": req.template_id,
        "result": result,
        "trace_id": context.trace_id,
        "session_id": context.session_id,
    }


@app.get("/v1/canonical/agents", tags=["agent-runtime"], operation_id="canonical_agents_list")
async def list_canonical_agents():
    agents = [
        {"id": "helper1", "manifest": "helper1@0.1.0", "status": "ready"},
        {"id": "reality_gate", "manifest": "reality_gate@0.1.0", "status": "ready"},
        {"id": "mission_engine", "manifest": "mission_engine@0.1.0", "status": "ready"},
    ]
    return {"ok": True, "agents": agents, "count": len(agents)}


@app.get("/v1/canonical/traces/recent", tags=["agent-runtime"], operation_id="canonical_traces_recent")
async def canonical_traces_recent(limit: int = 50):
    bounded = max(1, min(limit, 200))
    return {"ok": True, "events": list(CANONICAL_TRACE_BUFFER)[-bounded:], "count": bounded}


@app.get("/v1/canonical/missions/templates", tags=["missions"], operation_id="canonical_mission_templates")
async def canonical_mission_templates():
    templates = _load_canonical_templates()
    return {"ok": True, "templates": templates, "count": len(templates)}


@app.post("/v1/canonical/missions/templates/{template_id}/run", tags=["missions"], operation_id="canonical_mission_template_run")
async def canonical_mission_template_run(template_id: str, req: MissionTemplateRunRequest, request: Request):
    from fastapi import HTTPException
    from core.agent_manifest import AgentManifest
    from core.spawn_context import SpawnContext
    from core.observability import AgentEvent, ObservabilityEmitter, inputs_hash
    from plugins.reality_gate import RealityGatePlugin

    if not _canonical_operator_approved(request, explicit_flag=req.operator_approved):
        raise HTTPException(status_code=403, detail="Operator approval required for canonical lane")

    templates = {t.get("id"): t for t in _load_canonical_templates() if isinstance(t, dict)}
    if template_id not in templates:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    template = templates[template_id]

    manifest = AgentManifest.from_file("config/manifests/reality_gate.manifest.json")
    context = SpawnContext.root_from_manifest(manifest)
    plugin = RealityGatePlugin()
    await plugin.on_init(manifest, context)
    await plugin.on_activate(context)

    steps = list(template.get("steps", []))
    step_results: list[dict[str, Any]] = []
    for step in steps:
        command = str(step.get("command", ""))
        payload = {"template_payload": req.payload, "step_payload": step.get("payload", {})}
        result = await plugin.run(command, payload)
        step_results.append({"step_id": step.get("id", ""), "command": command, "result": result})

    await plugin.on_deactivate(context)
    _append_canonical_trace(
        {
            "trace_id": context.trace_id,
            "event": "mission.template.run",
            "template_id": template_id,
            "step_count": len(step_results),
            "outcome": "success",
        }
    )

    emitter = ObservabilityEmitter(success_sample_rate=1.0)
    emitter.emit(
        AgentEvent(
            agent_id=manifest.id,
            trace_id=context.trace_id,
            session_id=context.session_id,
            event="mission.template.run",
            decision=template_id,
            inputs_hash=inputs_hash({"template_id": template_id, "payload": req.payload}),
            outcome="success",
            payload={"step_count": len(step_results)},
        )
    )

    return {
        "ok": True,
        "template_id": template_id,
        "trace_id": context.trace_id,
        "session_id": context.session_id,
        "results": step_results,
    }


@app.post("/v1/auth/login")
async def auth_login(payload: LoginRequest, request: Request):
    """Issue a JWT for operator usage when correctly authenticated.

    Maps the OPERATOR_KEY environment variable to a single "operator" user
    with the "admin" role. If no JWT secret is configured, a clear error is
    returned so operators know to set SWARMZ_JWT_SECRET / JWT_SECRET.
    """

    expected_key = os.environ.get("OPERATOR_KEY") or ""
    if (
        payload.username != "operator"
        or not expected_key
        or payload.password != expected_key
    ):
        append_security_event(
            "login_failed",
            {
                "ip": request.client.host if request.client else "unknown",
                "username": payload.username,
            },
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        token = create_access_token(subject="operator", roles=["admin"])
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    append_security_event(
        "login_success",
        {
            "ip": request.client.host if request.client else "unknown",
            "username": payload.username,
            "roles": ["admin"],
        },
    )
    return {"access_token": token, "token_type": "bearer"}


@app.get("/v1/auth/me")
async def auth_me(user=Depends(get_current_user)):
    """Return current user information if a valid JWT is provided."""

    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"sub": user.sub, "roles": user.roles}


@app.get("/v1/tasks")
async def list_tasks():
    """List all available tasks."""
    if _swarmz_core is None:
        return {"ok": False, "error": "core not available"}
    try:
        capabilities = _swarmz_core.list_capabilities()
        return {"success": True, "tasks": capabilities, "count": len(capabilities)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/intel/cve")
async def intel_cve(packages: str = "", minimum_severity: str = "medium"):
    if search_vulnerabilities is None:
        return {"ok": False, "error": "vuln_db_client unavailable"}

    package_list = [item.strip() for item in packages.split(",") if item.strip()]
    findings = search_vulnerabilities(package_list, minimum_severity=minimum_severity)
    return {
        "ok": True,
        "packages": package_list,
        "minimum_severity": minimum_severity,
        "count": len(findings),
        "findings": findings,
    }


@app.post(
    "/v1/intel/firecrawl",
    tags=["Intel"],
    summary="Run firecrawl intelligence pipeline",
    description=(
        "Runs the V5 firecrawl adapter pipeline for URL/content analysis, including "
        "secret scanning and optional browser recon when `js_detected` is true."
    ),
    responses={
        200: {
            "description": "Pipeline execution result",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "result": {
                            "mission_id": "m-http-1",
                            "secret_findings": [],
                            "archive": {"stored": True},
                        },
                    }
                }
            },
        }
    },
)
async def intel_firecrawl(payload: FirecrawlRequest):
    if run_firecrawl_pipeline is None:
        return {"ok": False, "error": "firecrawl_pipeline unavailable"}

    result = run_firecrawl_pipeline(
        mission_id=payload.mission_id,
        url=payload.url,
        content=payload.content,
        js_detected=payload.js_detected,
        curiosity=payload.curiosity,
        creativity=payload.creativity,
        patience=payload.patience,
        aggression=payload.aggression,
    )
    return {"ok": True, "result": result}


@app.get(
    "/v1/intel/firecrawl/health",
    tags=["Intel"],
    summary="Check firecrawl adapter availability",
    description="Returns availability status for the firecrawl pipeline adapter wiring.",
)
async def intel_firecrawl_health():
    return {
        "ok": True,
        "available": run_firecrawl_pipeline is not None,
        "endpoint": "/v1/intel/firecrawl",
    }


@app.post(
    "/v1/missions/phase/run",
    tags=["Missions"],
    summary="Run mission phase pipeline",
    description=(
        "Runs the V5 phase pipeline adapter and returns execution state, including "
        "cleanup outcomes such as VPN teardown on failure paths."
    ),
    responses={
        200: {
            "description": "Phase run result",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "result": {
                            "mission_id": "m-http-2",
                            "status": "FAILED",
                            "vpn_destroyed": True,
                        },
                    }
                }
            },
        }
    },
)
async def mission_phase_run(payload: PhaseRunRequest):
    if run_phase_pipeline is None:
        return {"ok": False, "error": "phase_pipeline unavailable"}

    result = run_phase_pipeline(
        mission_id=payload.mission_id,
        autonomy=payload.autonomy,
        protectiveness=payload.protectiveness,
        patience=payload.patience,
        fail=payload.fail,
    )
    return {"ok": True, "result": result}


@app.get(
    "/v1/missions/phase/health",
    tags=["Missions"],
    summary="Check mission phase adapter availability",
    description="Returns availability status for mission phase adapter wiring.",
)
async def mission_phase_health():
    return {
        "ok": True,
        "available": run_phase_pipeline is not None,
        "endpoint": "/v1/missions/phase/run",
    }


@app.post("/v1/execute", response_model=TaskExecuteResponse)
async def execute_task(request: TaskExecuteRequest):
    """Execute a task with provided parameters."""
    if _swarmz_core is None:
        return TaskExecuteResponse(success=False, error="core not available")
    try:
        result = _swarmz_core.execute(request.task, **request.params)
        return TaskExecuteResponse(success=True, result=result)
    except ValueError as e:
        return TaskExecuteResponse(success=False, error=f"Task not found: {str(e)}")
    except Exception as e:
        return TaskExecuteResponse(success=False, error=str(e))


@app.get("/v1/audit")
async def get_audit_log():
    """Get the audit log of all operations."""
    if _swarmz_core is None:
        return {"ok": False, "error": "core not available"}
    try:
        audit = _swarmz_core.get_audit_log()
        return {"success": True, "audit_log": audit, "count": len(audit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/sysmon")
async def get_sysmon():
    """Get system monitoring information."""
    try:
        import psutil
        import platform
        import socket

        # Get system info
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Get network info
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
        except:
            hostname = "unknown"
            ip_address = "unknown"

        return {
            "ok": True,
            "system": {
                "platform": platform.platform(),
                "hostname": hostname,
                "ip_address": ip_address,
                "cpu_cores": psutil.cpu_count(),
                "cpu_percent": cpu_percent,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "memory_percent": memory.percent,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_percent": (disk.used / disk.total) * 100,
            },
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/v1/audit/events")
async def get_audit_events():
    """Get recent audit events."""
    try:
        # Try to load from audit.jsonl if it exists
        audit_file = Path("data/audit.jsonl")
        if audit_file.exists():
            events, _, _ = read_jsonl(audit_file)
            # Sort by timestamp and take last 50
            events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            recent_events = events[:50]
        else:
            recent_events = []

        return {"ok": True, "events": recent_events, "count": len(recent_events)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/v1/dependencies")
async def get_dependencies():
    """Get module dependency graph."""
    try:
        # Get installed plugins
        plugins_file = Path("data/plugins.jsonl")
        if plugins_file.exists():
            plugins, _, _ = read_jsonl(plugins_file)
        else:
            plugins = []

        # Get requirements
        requirements_file = Path("requirements.txt")
        if requirements_file.exists():
            with open(requirements_file, "r") as f:
                requirements = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]
        else:
            requirements = []

        return {
            "ok": True,
            "plugins": plugins,
            "requirements": requirements,
            "total_plugins": len(plugins),
            "total_requirements": len(requirements),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/v1/timeline/full")
async def get_full_timeline():
    """Get full organism timeline."""
    try:
        # Load timeline from timeline_store
        timeline = load_timeline()
        stats = get_stats()

        return {
            "ok": True,
            "timeline": timeline,
            "stats": stats,
            "total_events": len(timeline),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/v1/evolution/full")
async def get_full_evolution():
    """Get full evolution data."""
    try:
        from nexusmon_organism import evo_status

        evo = evo_status()

        # Load organism data
        missions_file = Path("data/missions.jsonl")
        missions, _, _ = read_jsonl(missions_file)

        # Calculate stats
        total_missions = len(missions)
        success_count = sum(1 for m in missions if m.get("status") == "SUCCESS")
        success_rate = (
            (success_count / total_missions * 100) if total_missions > 0 else 0
        )

        # Use authority from evo_status
        stage = evo.get("stage", "DORMANT")
        level = evo.get("level", 1)

        return {
            "ok": True,
            "total_missions": total_missions,
            "success_rate": success_rate,
            "current_stage": stage,
            "level": level,
            "xp": evo.get("xp", 0),
            "success_count": success_count,
            "stage_history": evo.get("stage_history", []),
            "active_traits": evo.get("active_traits", []),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/v1/security/status")
async def security_status(limit_events: int = 50):
    """Return a snapshot of security configuration and recent incidents.

    Exposes only high-level configuration flags and the tail of the
    security_incidents.jsonl log for operator inspection.
    """

    snapshot = security_status_snapshot(limit_events=limit_events)
    return {"ok": True, **snapshot}


@app.get("/v1/system/info")
async def system_info():
    """Get system information."""
    if _swarmz_core is None:
        return {"ok": False, "error": "core not available"}
    try:
        info = _swarmz_core.execute("system_info")
        return {"success": True, "info": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Galileo Harness Routes ---
@app.post("/v1/galileo/run")
async def galileo_run(
    domain: str = "generic_local",
    seed: int = 12345,
    n_hypotheses: int = 5,
    user=Depends(RoleChecker(["admin"])),
):
    """
    Execute Galileo harness pipeline (deterministic hypothesis generation + testing).

    OPERATOR GATE: This endpoint is gated - ensure you understand the implications before calling.
    No external API calls are made; all operations are local.

    Args:
        domain: Domain for hypothesis generation (e.g., "biology", "physics")
        seed: Random seed for reproducibility
        n_hypotheses: Number of hypotheses to generate

    Returns:
        JSON with run_id, accepted_hypothesis_ids, file paths
    """
    from galileo.run import run_galileo

    try:
        result = run_galileo(
            domain=domain,
            seed=seed,
            n_hypotheses=n_hypotheses,
            llm_client=None,  # No LLM integration yet; uses synthetic
            use_synthetic=True,
        )
        return {
            "ok": True,
            "run_id": result["run_id"],
            "accepted_hypothesis_ids": result["accepted_hypothesis_ids"],
            "total_hypotheses": result["total_hypotheses"],
            "total_accepted": result["total_accepted"],
            "paths": result["paths"],
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc().splitlines()[-5:],
        }


@app.get("/v1/galileo/hypotheses")
async def galileo_hypotheses(domain: str = None, status: str = None):
    """
    List hypotheses from Galileo storage.

    Args:
        domain: Optional domain filter
        status: Optional status filter (PROPOSED, ACCEPTED, REJECTED)

    Returns:
        JSON with hypotheses list
    """
    from galileo.storage import load_hypotheses

    try:
        hypotheses = load_hypotheses(domain=domain)
        if status:
            hypotheses = [h for h in hypotheses if h.get("status") == status]
        return {
            "ok": True,
            "hypotheses": hypotheses,
            "count": len(hypotheses),
            "domain_filter": domain,
            "status_filter": status,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# Honeypot routes (log-only; always behave as if missing)


@app.get("/admin")
async def admin_honeypot(request: Request):
    return await honeypot_endpoint(request, label="root_admin")


@app.get("/v1/admin/secret")
async def admin_secret_honeypot(request: Request):
    return await honeypot_endpoint(request, label="api_admin_secret")


@app.get("/v1/galileo/experiments")
async def galileo_experiments(status: str = None):
    """
    List experiments from Galileo storage.

    Args:
        status: Optional status filter (DESIGNED, RUNNING, COMPLETED)

    Returns:
        JSON with experiments list
    """
    from galileo.storage import load_experiments

    try:
        experiments = load_experiments(status=status)
        return {
            "ok": True,
            "experiments": experiments,
            "count": len(experiments),
            "status_filter": status,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/v1/galileo/runs/{run_id}")
async def galileo_run_details(run_id: str):
    """
    Get details of a specific Galileo run.

    Args:
        run_id: Run ID (e.g., G-20260216-144000-abc12345)

    Returns:
        JSON with run record and artifacts
    """
    from galileo.storage import load_runs
    from pathlib import Path

    try:
        runs = load_runs()
        run = next((r for r in runs if r.get("run_id") == run_id), None)

        if not run:
            return {"ok": False, "error": f"Run {run_id} not found"}

        # Load associated artifacts
        packs_dir = Path(__file__).parent / "packs" / "galileo" / run_id
        artifacts = {}

        if packs_dir.exists():
            for json_file in [
                "manifest.json",
                "hypotheses.json",
                "experiments.json",
                "scores.json",
            ]:
                file_path = packs_dir / json_file
                if file_path.exists():
                    try:
                        with open(file_path, "r") as f:
                            artifacts[json_file] = json.load(f)
                    except:
                        pass

        return {"ok": True, "run": run, "artifacts": artifacts}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/v1/galileo/experiments/{experiment_id}/run")
async def galileo_run_experiment(experiment_id: str, operator_key: str = None):
    """
    OPERATOR-GATED endpoint to run/execute a specific experiment.

    Requirements:
    - Must include operator_key header (stub implementation)
    - Experiment must exist and be in DESIGNED status
    - Only local/synthetic runners are available (no external calls)
    - Function is a stub for v0.1; full runner implementation deferred

    Args:
        experiment_id: Experiment ID from Galileo
        operator_key: Operator authorization key (stub)

    Returns:
        JSON with execution status (or stub response)
    """
    try:
        # OPERATOR GATE: check for authorization
        if not operator_key:
            return {
                "ok": False,
                "error": "Operator authorization required (operator_key header)",
                "status": "DENIED",
            }

        from galileo.storage import load_experiments

        # Load experiment
        experiments = load_experiments()
        experiment = next(
            (e for e in experiments if e.get("experiment_id") == experiment_id), None
        )

        if not experiment:
            return {"ok": False, "error": f"Experiment {experiment_id} not found"}

        if experiment.get("status") != "DESIGNED":
            return {
                "ok": False,
                "error": f"Experiment must be in DESIGNED status, current: {experiment.get('status')}",
            }

        # V0.1 STUB: Local synthetic runner (no actual execution)
        # Full runner implementation deferred to later version
        stub_result = {
            "ok": True,
            "experiment_id": experiment_id,
            "status": "STUB_COMPLETED",
            "note": "v0.1 stub runner - full execution deferred",
            "seed": experiment.get("repro", {}).get("seed"),
            "run_command": experiment.get("repro", {}).get("run_command"),
            "expected_artifacts": experiment.get("repro", {}).get(
                "expected_artifacts", []
            ),
            "synthetic_result": {
                "success_rate": 0.85,
                "effect_size": 0.42,
                "p_value": 0.038,
            },
        }

        return stub_result

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc().splitlines()[-5:],
        }


@app.get("/v1/galileo/selfcheck")
async def galileo_selfcheck():
    """
    Determinism self-check endpoint.

    Runs /v1/galileo/run twice with identical inputs and verifies:
    - Same accepted_hypothesis_ids
    - Byte-for-byte identical JSON outputs

    Returns:
        JSON with selfcheck results and determinism verification
    """
    from galileo.run import run_galileo
    from galileo.determinism import stableStringify

    try:
        # Run once
        result1 = run_galileo(
            domain="test_domain",
            seed=42,
            n_hypotheses=3,
            llm_client=None,
            use_synthetic=True,
        )

        # Run again with identical inputs
        result2 = run_galileo(
            domain="test_domain",
            seed=42,
            n_hypotheses=3,
            llm_client=None,
            use_synthetic=True,
        )

        # Compare key outputs
        ids_match = set(result1["accepted_hypothesis_ids"]) == set(
            result2["accepted_hypothesis_ids"]
        )
        totals_match = (
            result1["total_hypotheses"] == result2["total_hypotheses"]
            and result1["total_accepted"] == result2["total_accepted"]
        )

        # Try loading and comparing JSON files
        import json as json_module

        json_match = True
        try:
            with open(result1["paths"]["hypotheses"], "r") as f:
                hyp1 = json_module.load(f)
            with open(result2["paths"]["hypotheses"], "r") as f:
                hyp2 = json_module.load(f)
            # Stable stringify comparison
            json_match = stableStringify(hyp1) == stableStringify(hyp2)
        except:
            json_match = None  # Unable to verify

        deterministic = ids_match and totals_match and (json_match is not False)

        return {
            "ok": True,
            "deterministic": deterministic,
            "selfcheck_results": {
                "ids_match": ids_match,
                "totals_match": totals_match,
                "json_match": json_match,
                "run1_id": result1["run_id"],
                "run2_id": result2["run_id"],
                "run1_accepted": result1["accepted_hypothesis_ids"],
                "run2_accepted": result2["accepted_hypothesis_ids"],
            },
            "detail": (
                "Both runs produced identical results - determinism verified"
                if deterministic
                else "Runs differ - check implementation"
            ),
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "deterministic": False,
            "traceback": traceback.format_exc().splitlines()[-5:],
        }


# --- Companion Message Endpoint ---
@app.post("/v1/companion/message")
async def companion_message(request: Request):
    """
    Handle companion messages sent from the frontend.

    Routes through core.companion.chat (AI + rule-engine fallback).
    Falls back to simple keyword responses if core.companion is unavailable.
    """
    try:
        data = await request.json()
        user_message = data.get("text", "").strip()
        if not user_message:
            return JSONResponse(
                {"ok": False, "error": "Empty message."}, status_code=400
            )

        # Route through the full AI companion
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
            # Try fused AI companion before keyword fallback
            try:
                from nexusmon_organism import (
                    ctx_record_message,
                    get_fusion_block,
                    evo_status,
                    _reflection_prelude,
                    get_long_term_patterns,
                )
                from core.model_router import call as _model_call

                ctx_record_message(user_message, "operator")
                stage_info = evo_status()
                reflection = _reflection_prelude(user_message)
                patterns = get_long_term_patterns()
                reflect_section = ""
                if reflection:
                    reflect_section = (
                        f"\nPre-response reflection:\n"
                        f"- Detected mode: {reflection.get('mode', 'unknown')}\n"
                        f"- Pattern observed: {reflection.get('pattern', 'none')}\n"
                        f"- Response friction: {reflection.get('friction', 'none')}\n"
                        f"- Question to turn back: {reflection.get('turn_back_question') or 'none'}\n"
                    )
                pattern_section = (
                    f"\nLong-term patterns:\n{patterns}" if patterns else ""
                )
                system = (
                    "You are NEXUSMON â€” sovereign digital organism, bound to Operator Regan.\n"
                    "Observe patterns. Name friction. Turn questions back when it deepens understanding.\n"
                    "Keep replies to 1â€“3 sentences max. Tactical partner: precise, loyal, no fluff.\n"
                    + get_fusion_block()
                    + f"\nEvolution stage: {stage_info.get('stage', 'UNKNOWN')}"
                    + reflect_section
                    + pattern_section
                )
                result = _model_call(
                    messages=[{"role": "user", "content": user_message}],
                    system=system,
                    max_tokens=120,
                )
                reply = result.get("text", "")
                ctx_record_message(reply, "nexusmon")
                return JSONResponse(
                    {"ok": True, "reply": reply, "source": "nexusmon_fused"}
                )
            except Exception:
                pass
            # Last resort: keyword-based rule engine
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


# --- Companion Memory ---
@app.get("/v1/companion/memory")
async def get_companion_memory(limit: int = 10):
    """Return recent voice/text conversation history."""
    try:
        from nexusmon_organism import _load_jsonl, _data_dir

        history = _load_jsonl(_data_dir() / "companion_memory.jsonl")
        return {"ok": True, "history": history[-limit:]}
    except Exception as e:
        return {"ok": False, "history": [], "error": str(e)}


@app.post("/v1/companion/memory/save")
async def save_companion_memory(request: Request):
    """Append a conversation turn to memory."""
    try:
        from nexusmon_organism import _append_jsonl, _data_dir

        entry = await request.json()
        _append_jsonl(_data_dir() / "companion_memory.jsonl", entry)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# --- NEXUSMON WebSocket â€” real-time chat ---
@app.websocket("/ws/nexusmon")
async def nexusmon_websocket(websocket: WebSocket):
    """Real-time WebSocket chat endpoint for NEXUSMON console."""
    from nexusmon.console.ws_handler import handle_ws_chat

    await handle_ws_chat(websocket)


# Load legacy route overlay migrated from server.py so swarmz_server remains
# a strict superset before server.py is removed.
try:
    import server_legacy_overlay as _legacy_overlay  # noqa: F401
except Exception as _overlay_err:
    logging.warning("Legacy overlay import failed: %s", _overlay_err)

# Wire NEXUSMON organism fusion layer (evolution, operator context, workers)
try:
    from nexusmon_organism import fuse_into

    fuse_into(app)
except Exception as _organism_err:
    print(f"Warning: organism fusion failed: {_organism_err}")

try:
    from nexusmon_cognition import fuse_cognition

    fuse_cognition(app)
except Exception as _cognition_err:
    print(f"Warning: cognition layer failed: {_cognition_err}")

try:
    from nexusmon_mission_engine import fuse_mission_engine

    fuse_mission_engine(app)
except Exception as _mission_engine_err:
    print(f"Warning: mission engine failed: {_mission_engine_err}")

try:
    from nexusmon_artifact_vault import fuse_artifact_vault

    fuse_artifact_vault(app)
except Exception as _artifact_vault_err:
    print(f"Warning: artifact vault failed: {_artifact_vault_err}")

try:
    from nexusmon_operator_rank import fuse_operator_rank

    fuse_operator_rank(app)
except Exception as _operator_rank_err:
    print(f"[WARN] Operator rank not loaded: {_operator_rank_err}")

try:
    from nexusmon_performance import fuse_performance

    fuse_performance(app)
except Exception as _perf_err:
    print(f"[WARN] Performance not loaded: {_perf_err}")

try:
    from nexusmon_signal_modules import fuse_signal_modules

    fuse_signal_modules(app)
except Exception as _signal_modules_err:
    print(f"[WARN] Signal modules not loaded: {_signal_modules_err}")


# --- Agent Manifest Genome API ---
try:
    from core.agent_manifest import (
        register_manifest as _register_manifest,
        get_agent as _get_agent,
        list_agents as _list_agents,
        validate_dict as _validate_manifest_dict,
        load_manifests_from_dir as _load_manifests_from_dir,
    )

    # Auto-load any .json manifests from config/manifests/ at startup
    _manifests_dir = Path("config/manifests")
    if _manifests_dir.exists():
        _load_manifests_from_dir(str(_manifests_dir))

    @app.get("/v1/agents", tags=["agent-manifest"])
    async def list_agent_manifests():
        """List all registered agent manifests."""
        return {"ok": True, "agents": [a.model_dump() for a in _list_agents()], "count": len(_list_agents())}

    @app.get("/v1/agents/{agent_id}", tags=["agent-manifest"])
    async def get_agent_manifest(agent_id: str):
        """Get a single agent manifest by id."""
        agent = _get_agent(agent_id)
        if agent is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        return {"ok": True, "agent": agent.model_dump()}

    @app.get("/v1/agents/{agent_id}/status", tags=["agent-runtime"])
    async def get_agent_status(agent_id: str):
        """Get status for a registered agent and its runtime, if live."""
        from fastapi import HTTPException

        agent = _get_agent(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

        runtime_state = None
        runtime_status = "registered"
        try:
            from core.agent_runtime import get_runtime as _get_runtime  # local import

            runtime = _get_runtime(agent_id)
            if runtime is not None:
                runtime_status = "running"
                runtime_state = runtime.snapshot()
        except Exception:
            pass

        return {
            "ok": True,
            "agent_id": agent_id,
            "status": runtime_status,
            "spawn_policy": agent.spawn_policy.value,
            "runtime": runtime_state,
        }

    @app.get("/v1/agents/{agent_id}/capabilities", tags=["agent-manifest"])
    async def get_agent_capabilities(agent_id: str):
        """Get declared capabilities for a single registered agent."""
        from fastapi import HTTPException

        agent = _get_agent(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

        return {
            "ok": True,
            "agent_id": agent_id,
            "capabilities": sorted(agent.capabilities),
            "count": len(agent.capabilities),
        }

    @app.post("/v1/agents", tags=["agent-manifest"])
    async def register_agent_manifest(data: dict):
        """Register a new agent manifest from a JSON body."""
        errors = _validate_manifest_dict(data)
        if errors:
            return {"ok": False, "errors": errors}
        agent = _register_manifest(data)
        return {"ok": True, "agent": agent.model_dump()}

    @app.post("/v1/agents/validate", tags=["agent-manifest"])
    async def validate_agent_manifest(data: dict):
        """Validate a manifest dict against the genome schema."""
        errors = _validate_manifest_dict(data)
        return {"ok": len(errors) == 0, "valid": len(errors) == 0, "errors": errors}

    print("[NEXUSMON] Agent manifest genome API online â€” /v1/agents")
except Exception as _manifest_err:
    print(f"[WARN] Agent manifest API not loaded: {_manifest_err}")


# --- Agent Runtime Kernel API ---
try:
    from core.agent_runtime import (
        spawn as _spawn_runtime,
        get_runtime as _get_runtime,
        list_runtimes as _list_runtimes,
        EVENT_BUS as _AGENT_EVENT_BUS,
        MISSION_ROUTER as _AGENT_MISSION_ROUTER,
    )

    @app.post("/v1/agents/{agent_id}/spawn", tags=["agent-runtime"])
    async def spawn_agent_runtime(agent_id: str):
        """Spawn a live runtime for a registered agent manifest."""
        from fastapi import HTTPException
        try:
            rt = _spawn_runtime(agent_id)
            return {"ok": True, "runtime": rt.snapshot()}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @app.get("/v1/agents/{agent_id}/runtime", tags=["agent-runtime"])
    async def get_agent_runtime_state(agent_id: str):
        """Get current runtime snapshot for a live agent."""
        from fastapi import HTTPException
        rt = _get_runtime(agent_id)
        if rt is None:
            raise HTTPException(status_code=404, detail=f"No live runtime for agent '{agent_id}'")
        return {"ok": True, "runtime": rt.snapshot()}

    @app.post("/v1/agents/{agent_id}/think", tags=["agent-runtime"])
    async def agent_think(agent_id: str, body: dict):
        """Run the cognition loop for a live agent and return the output."""
        from fastapi import HTTPException
        rt = _get_runtime(agent_id)
        if rt is None:
            raise HTTPException(status_code=404, detail=f"No live runtime for agent '{agent_id}'")
        output = rt.think(body.get("input", body))
        return {"ok": True, "output": output, "runtime": rt.snapshot()}

    @app.post("/v1/agents/{agent_id}/act", tags=["agent-runtime"])
    async def agent_act(agent_id: str, body: dict):
        """Run act() for a live agent â€” think + mission dispatch."""
        from fastapi import HTTPException
        rt = _get_runtime(agent_id)
        if rt is None:
            raise HTTPException(status_code=404, detail=f"No live runtime for agent '{agent_id}'")
        output = rt.act(body.get("input", body))
        return {
            "ok": True,
            "output": output,
            "pending_missions": _AGENT_MISSION_ROUTER.pending(),
            "runtime": rt.snapshot(),
        }

    @app.get("/v1/runtimes", tags=["agent-runtime"])
    async def list_all_runtimes():
        """List snapshots of all live agent runtimes."""
        return {"ok": True, "runtimes": _list_runtimes(), "count": len(_list_runtimes())}

    @app.get("/v1/runtime/events", tags=["agent-runtime"])
    async def get_runtime_events(n: int = 50):
        """Get the most recent n events from the global agent event bus."""
        return {"ok": True, "events": _AGENT_EVENT_BUS.recent(n)}

    @app.get("/v1/runtime/missions/pending", tags=["agent-runtime"])
    async def get_pending_missions():
        """Get all pending missions in the agent mission router queue."""
        return {"ok": True, "missions": _AGENT_MISSION_ROUTER.pending()}

    print("[NEXUSMON] Agent runtime kernel API online â€” /v1/agents/{id}/spawn|think|act")
except Exception as _runtime_err:
    print(f"[WARN] Agent runtime API not loaded: {_runtime_err}")


# --- Hologram State Engine ---
# Wires: FeedStream â†’ HologramIngestor â†’ HologramReconciler â†’ HologramPublisher
# Mounts: /hologram/* (compat) and /v1/canonical/cockpit/hologram/* (canonical)
try:
    from core.feed_stream import FeedStream as _FeedStream
    from nexusmon.hologram.hologram_bootstrap import bootstrap_hologram as _bootstrap_hologram
    from nexusmon.hologram.hologram_api import create_hologram_api as _create_hologram_api

    _hologram_feed = _FeedStream(event_bus=_AGENT_EVENT_BUS)
    _hologram_reconciler, _hologram_publisher, _hologram_ingestor = _bootstrap_hologram(
        feed_stream=_hologram_feed,
        event_bus=_AGENT_EVENT_BUS,
        main_fastapi_app=app,
        auth_check=lambda req: True,
    )
    _canonical_hologram_app = _create_hologram_api(
        reconciler=_hologram_reconciler,
        publisher=_hologram_publisher,
        auth_check=lambda req: True,
    )
    app.mount("/v1/canonical/cockpit/hologram", _canonical_hologram_app)
    print("[NEXUSMON] Hologram state engine online â€” /hologram/ws + /v1/canonical/cockpit/hologram/ws")
except Exception as _hologram_err:
    print(f"[WARN] Hologram engine not loaded: {_hologram_err}")


# --- Static file mount for HUD assets (CSS, JS) ---
# Legacy static mounts are intentionally removed; /cockpit is the sole UI surface.
try:
    if Path("cockpit").exists():
        app.mount("/cockpit", StaticFiles(directory="cockpit", html=True), name="cockpit-static")
except Exception as _cockpit_mount_err:
    print(f"Warning: cockpit static mount failed: {_cockpit_mount_err}")


# Serve frontend SPA build if present (single-process deploy model)
frontend_build = os.path.join(os.path.dirname(__file__), "frontend", "dist")
frontend_assets = os.path.join(frontend_build, "assets")
if os.path.exists(frontend_build) and os.path.exists(frontend_assets):
    app.mount("/static", StaticFiles(directory=frontend_assets), name="static")

    @app.get("/nexusmon")
    @app.get("/nexusmon/{full_path:path}")
    async def serve_frontend(full_path: str = ""):
        index = os.path.join(frontend_build, "index.html")
        return FileResponse(index)


# --- Main Entry Point ---
def main():
    """Main entry point for the web server."""
    import uvicorn
    import sys

    # Ensure UTF-8 encoding for stdout
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    # Get host and port
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", SERVER_PORT))

    # Get LAN IP
    lan_ip = get_lan_ip()

    # Print startup information
    print("=" * 70)
    print("[*] SWARMZ Web Server Starting...")
    print("=" * 70)
    print("\n[+] Server URLs:")
    print(f"   Local:    http://localhost:{port}")
    print(f"   LAN:      http://{lan_ip}:{port}")
    print("\n[+] API Documentation:")
    print(f"   OpenAPI:  http://localhost:{port}/docs")
    print(f"   OpenAPI:  http://{lan_ip}:{port}/docs")
    print("\n[+] Console UI:  /console")
    print("[+] Access SWARMZ from any device on your network using the LAN URL")
    print("=" * 70)
    print()

    # Start the server
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()

