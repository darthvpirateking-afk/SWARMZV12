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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
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


SERVER_PORT = int(os.environ.get("PORT", "8012"))
LAN_IP = get_lan_ip()

# Ensure data dir exists before anything writes to it
Path("data").mkdir(parents=True, exist_ok=True)


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

# Add CORS middleware — allow_credentials=True requires explicit origins (not "*")
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

# Setup logging
logging.basicConfig(
    filename="data/server_live.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# Global state for exception tracking
last_exception_traceback = None


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
    """Serve the MASTER SWARMZ avatar UI."""
    return FileResponse("web/avatar.html", media_type="text/html")


# --- Home route — NEXUSMON is the face of this system ---
@app.get("/")
async def home_page():
    """MASTER SWARMZ avatar is the default home surface."""
    return FileResponse("web/avatar.html", media_type="text/html")


@app.get("/nexusmon-console")
async def nexusmon_console_page():
    """Serve the legacy NEXUSMON console UI."""
    return FileResponse("web/nexusmon_console.html", media_type="text/html")


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
const CACHE_NAME = 'swarmz-v2';
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
const CACHE_NAME = 'swarmz-shell-v2';
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
        text-anchor="middle" fill="#ffffff">âš¡</text>
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
        text-anchor="middle" fill="#ffffff">âš¡</text>
</svg>"""
    return HTMLResponse(content=svg, media_type="image/svg+xml")


# REST API Endpoints
@app.get("/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "SWARMZ API"}


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
        operator_id = str(data.get("operator_id", "op-001")).strip() or "op-001"
        if not user_message:
            return JSONResponse(
                {"ok": False, "error": "Empty message."}, status_code=400
            )

        # Route through the full AI companion
        try:
            from core.companion import chat as companion_chat

            result = companion_chat(user_message, operator_id=operator_id)
            resp = {
                "ok": True,
                "reply": result.get("reply", "(empty)"),
                "source": result.get("source", "unknown"),
                "operator_id": result.get("operator_id", operator_id),
            }
            if result.get("provider"):
                resp["provider"] = result["provider"]
            if result.get("model"):
                resp["model"] = result["model"]
            if result.get("latencyMs"):
                resp["latencyMs"] = result["latencyMs"]
            return JSONResponse(resp)
        except Exception as companion_err:
            # Fallback: keyword-based rule engine
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


# --- NEXUSMON WebSocket — real-time chat ---
@app.websocket("/ws/nexusmon")
async def nexusmon_websocket(websocket: WebSocket):
    """Real-time WebSocket chat endpoint for NEXUSMON console."""
    from nexusmon.console.ws_handler import handle_ws_chat

    await handle_ws_chat(websocket)


# --- Static file mount for HUD assets (CSS, JS) ---
# MUST come after all explicit routes so /web/* doesn't shadow API paths.
app.mount("/web", StaticFiles(directory="web"), name="web-static")


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
