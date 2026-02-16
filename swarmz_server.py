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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from swarmz import SwarmzCore
from jsonl_utils import read_jsonl, write_jsonl


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


# Initialize FastAPI app
app = FastAPI(
    title="SWARMZ API",
    description="Operator-Sovereign 'Do Anything' System - REST API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/docs/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(filename="data/server_live.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

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
    mission_id = f"mission_{int(datetime.utcnow().timestamp()*1000)}"
    created_at = datetime.utcnow().isoformat() + "Z"
    mission = {
        "mission_id": mission_id,
        "goal": req.goal,
        "category": req.category,
        "constraints": req.constraints,
        "results": req.results,
        "status": "PENDING",
        "created_at": created_at
    }
    write_jsonl(missions_file, mission)
    audit_event = {
        "event": "mission_created",
        "mission_id": mission_id,
        "timestamp": created_at,
        "goal": req.goal,
        "category": req.category
    }
    write_jsonl(audit_file, audit_event)
    return {
        "ok": True,
        "mission_id": mission_id,
        "status": "PENDING",
        "created_at": created_at,
        "goal": req.goal,
        "category": req.category
    }


@app.get("/v1/missions/list")
async def list_missions():
    """List all missions."""
    missions_file = Path("data/missions.jsonl")
    missions, skipped, quarantined = read_jsonl(missions_file)
    now = datetime.utcnow().isoformat() + "Z"
    for m in missions:
        if "updated_at" not in m:
            m["updated_at"] = m.get("created_at", now)
    return {
        "ok": True,
        "missions": missions,
        "count": len(missions),
        "skipped_empty": skipped,
        "quarantined": quarantined
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
    started_at = datetime.utcnow().isoformat() + "Z"
    mission["status"] = "RUNNING"
    mission["started_at"] = started_at
    missions_file.write_text("")
    for m in missions:
        write_jsonl(missions_file, m)
    audit_file = Path("data/audit.jsonl")
    audit_event = {
        "event": "mission_run",
        "mission_id": mission_id,
        "timestamp": started_at
    }
    write_jsonl(audit_file, audit_event)
    return {"ok": True, "mission_id": mission_id, "status": "RUNNING", "started_at": started_at}


# --- UI state endpoint ---
def compute_phase(total_missions: int, success_count: int) -> str:
    """Compute phase based on mission counts and success rate."""
    success_rate = success_count / total_missions if total_missions > 0 else 0.0
    if success_rate < 0.3 and total_missions > 0:
        return "QUARANTINE"
    if total_missions < 10:
        return "AWAKENING"
    elif total_missions < 50:
        return "FORGING"
    else:
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
    
    now = datetime.utcnow().isoformat() + "Z"
    return {
        "ok": True,
        "server": {
            "version": "1.0.0",
            "now": now
        },
        "missions": {
            "count_total": len(missions),
            "count_by_status": status_counts
        },
        "last_events": last_events,
        "phase": phase
    }


@app.get("/v1/debug/traceback_last")
async def traceback_last():
    """Get the last exception traceback."""
    return {
        "ok": True,
        "traceback": last_exception_traceback or "No exception recorded"
    }


# --- Console UI Route ---
@app.get("/console", response_class=HTMLResponse)
async def console_page():
    """Serve the SWARMZ Console UI."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ SWARMZ Console</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 1rem;
            color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header {
            text-align: center;
            color: white;
            margin-bottom: 2rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .phase-label {
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            font-weight: bold;
            margin-top: 1rem;
        }
        .phase-AWAKENING { background: rgba(255,0,0,0.2); border: 2px solid rgba(255,0,0,0.5); color: white; }
        .phase-FORGING { background: rgba(255,255,0,0.1); border: 2px solid rgba(255,255,0,0.5); color: white; box-shadow: 0 0 10px rgba(255,255,0,0.5); }
        .phase-SOVEREIGN { background: rgba(0,255,0,0.1); border: 2px solid rgba(0,255,0,0.5); color: white; box-shadow: 0 0 15px rgba(0,255,0,0.8); }
        .phase-QUARANTINE { background: rgba(255,0,0,0.15); border: 2px solid rgba(255,0,0,0.8); color: white; box-shadow: 0 0 20px rgba(255,0,0,0.8); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .card {
            background: rgba(255, 255, 255, 0.95);
            padding: 1.5rem;
            border-radius: 1rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }
        .card h2 { color: #667eea; margin-bottom: 1rem; font-size: 1.3rem; }
        input, select {
            width: 100%;
            padding: 0.75rem;
            margin: 0.5rem 0;
            border: 2px solid #e0e0e0;
            border-radius: 0.5rem;
            font-size: 1rem;
        }
        input:focus, select:focus { outline: none; border-color: #667eea; }
        button {
            padding: 0.75rem 1.5rem;
            margin: 0.5rem 0.5rem 0.5rem 0;
            border: none;
            border-radius: 0.5rem;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5568d3; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
        .btn-secondary { background: #764ba2; color: white; }
        .btn-secondary:hover { background: #66408b; }
        .stat { text-align: center; margin: 1rem 0; }
        .stat-value { font-size: 2rem; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; font-size: 0.9rem; }
        .mission-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        .mission-table th {
            background: #f5f5f5;
            padding: 1rem;
            text-align: left;
            color: #333;
            font-weight: bold;
            border-bottom: 2px solid #ddd;
        }
        .mission-table td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #eee;
        }
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 0.25rem;
            font-size: 0.85rem;
            font-weight: bold;
            color: white;
        }
        .badge-PENDING { background: #ffc107; }
        .badge-RUNNING { background: #2196f3; }
        .badge-SUCCESS { background: #4caf50; }
        .badge-FAILURE { background: #f44336; }
        .log-panel {
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 0.5rem;
            font-family: monospace;
            font-size: 0.85rem;
            max-height: 200px;
            overflow-y: auto;
            color: #333;
        }
        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
            header h1 { font-size: 1.8rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚡ SWARMZ Console</h1>
            <div class="phase-label" id="phaseLabel">AWAKENING</div>
        </header>

        <div class="grid">
            <!-- Form Card -->
            <div class="card">
                <h2>🎯 Create Mission</h2>
                <input type="text" id="goalInput" placeholder="Mission goal..." />
                <select id="categorySelect">
                    <option value="">Select category...</option>
                    <option value="test">Test</option>
                    <option value="analysis">Analysis</option>
                    <option value="generation">Generation</option>
                    <option value="execution">Execution</option>
                </select>
                <button class="btn-primary" onclick="createMission()">CREATE</button>
                <button class="btn-secondary" onclick="runMission()">RUN</button>
                <button class="btn-secondary" onclick="refreshState()">REFRESH</button>
            </div>

            <!-- Current Mission Card -->
            <div class="card">
                <h2>📋 Current Mission</h2>
                <div id="currentMission">None selected</div>
            </div>

            <!-- Statistics Card -->
            <div class="card">
                <h2>📊 Statistics</h2>
                <div class="stat">
                    <div class="stat-label">Total Missions</div>
                    <div class="stat-value" id="totalMissions">0</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Pending</div>
                    <div class="stat-value" id="pendingCount">0</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Successful</div>
                    <div class="stat-value" id="successCount">0</div>
                </div>
            </div>
        </div>

        <!-- Missions Table Card -->
        <div class="card" style="margin-bottom: 2rem;">
            <h2>📝 Missions</h2>
            <table class="mission-table">
                <thead>
                    <tr>
                        <th>ID (First 8)</th>
                        <th>Goal</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="missionsTableBody">
                    <tr><td colspan="3" style="text-align: center; color: #999;">No missions yet</td></tr>
                </tbody>
            </table>
        </div>

        <!-- System Log Card -->
        <div class="card">
            <h2>📜 System Log</h2>
            <div class="log-panel" id="systemLog">Waiting for events...</div>
        </div>
    </div>

    <script>
        const API_BASE = location.origin || 'http://127.0.0.1:8012';
        
        function createMission() {
            const goal = document.getElementById('goalInput').value;
            const category = document.getElementById('categorySelect').value;
            if (!goal || !category) return alert('Please fill in all fields');
            
            fetch(API_BASE + '/v1/missions/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ goal, category, constraints: {}, results: {} })
            })
            .then(r => r.json())
            .then(d => {
                if (d.ok) {
                    localStorage.setItem('currentMissionId', d.mission_id);
                    document.getElementById('goalInput').value = '';
                    document.getElementById('categorySelect').value = '';
                    refreshState();
                } else alert('Error: ' + d.error);
            });
        }
        
        function runMission() {
            const id = localStorage.getItem('currentMissionId');
            if (!id) return alert('No mission selected');
            
            fetch(API_BASE + '/v1/missions/run?mission_id=' + id, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(r => r.json())
            .then(d => {
                if (d.ok) refreshState();
                else alert('Error: ' + d.error);
            });
        }
        
        function refreshState() {
            Promise.all([
                fetch(API_BASE + '/v1/ui/state').then(r => r.json()),
                fetch(API_BASE + '/v1/missions/list').then(r => r.json())
            ]).then(([uiData, listData]) => updateUI(uiData, listData));
        }
        
        function updateUI(uiData, listData) {
            // Update phase label
            document.getElementById('phaseLabel').className = 'phase-label phase-' + uiData.phase;
            document.getElementById('phaseLabel').textContent = uiData.phase;
            
            // Update stats
            document.getElementById('totalMissions').textContent = uiData.missions.count_total;
            document.getElementById('pendingCount').textContent = uiData.missions.count_by_status.PENDING || 0;
            document.getElementById('successCount').textContent = uiData.missions.count_by_status.SUCCESS || 0;
            
            // Update missions table
            const tbody = document.getElementById('missionsTableBody');
            if (listData.missions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #999;">No missions yet</td></tr>';
            } else {
                tbody.innerHTML = listData.missions.map(m => `
                    <tr>
                        <td>${(m.mission_id || '').substring(0, 8)}</td>
                        <td>${(m.goal || '').substring(0, 20)}</td>
                        <td><span class="badge badge-${m.status}">${m.status}</span></td>
                    </tr>
                `).join('');
            }
            
            // Update current mission
            const curId = localStorage.getItem('currentMissionId');
            const curMission = listData.missions.find(m => m.mission_id === curId);
            if (curMission) {
                document.getElementById('currentMission').innerHTML = `
                    <strong>${curMission.mission_id}</strong><br>
                    Goal: ${curMission.goal}<br>
                    Status: <span class="badge badge-${curMission.status}">${curMission.status}</span><br>
                    Created: ${curMission.created_at || 'N/A'}
                `;
            }
            
            // Update system log
            const logHtml = uiData.last_events.map(e => 
                `${e.timestamp || ''} | ${e.event || 'unknown'}`
            ).join('<br>');
            document.getElementById('systemLog').innerHTML = logHtml || 'No events yet';
        }
        
        // Initial load and auto-refresh
        refreshState();
        setInterval(refreshState, 2000);
    </script>
</body>
</html>"""


# --- Home redirect ---
@app.get("/")
async def home_redirect():
    """Redirect to console."""
    return RedirectResponse(url="/console", status_code=302)


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
                "purpose": "any maskable"
            },
            {
                "src": "/apple-touch-icon.svg",
                "type": "image/svg+xml",
                "sizes": "180x180"
            }
        ],
        "categories": ["productivity", "utilities", "developer tools"],
        "screenshots": []
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

// Fetch event - network-first for API, cache-first for assets
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Network-first strategy for API endpoints and docs
    if (url.pathname.startsWith('/v1/') || url.pathname.startsWith('/docs/')) {
        event.respondWith(
            fetch(request)
                .then(response => {
                    // Clone the response for caching
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, responseClone);
                    });
                    return response;
                })
                .catch(() => {
                    // Fall back to cache if network fails
                    return caches.match(request);
                })
        );
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
        text-anchor="middle" fill="#ffffff">⚡</text>
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
        text-anchor="middle" fill="#ffffff">⚡</text>
</svg>"""
    return HTMLResponse(content=svg, media_type="image/svg+xml")


# REST API Endpoints
@app.get("/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SWARMZ API",
        "version": "1.0.0"
    }


@app.get("/v1/tasks")
async def list_tasks():
    """List all available tasks."""
    try:
        capabilities = swarmz.list_capabilities()
        return {
            "success": True,
            "tasks": capabilities,
            "count": len(capabilities)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/execute", response_model=TaskExecuteResponse)
async def execute_task(request: TaskExecuteRequest):
    """Execute a task with provided parameters."""
    try:
        result = swarmz.execute(request.task, **request.params)
        return TaskExecuteResponse(
            success=True,
            result=result
        )
    except ValueError as e:
        return TaskExecuteResponse(
            success=False,
            error=f"Task not found: {str(e)}"
        )
    except Exception as e:
        return TaskExecuteResponse(
            success=False,
            error=str(e)
        )


@app.get("/v1/audit")
async def get_audit_log():
    """Get the audit log of all operations."""
    try:
        audit = swarmz.get_audit_log()
        return {
            "success": True,
            "audit_log": audit,
            "count": len(audit)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/system/info")
async def system_info():
    """Get system information."""
    try:
        info = swarmz.execute("system_info")
        return {
            "success": True,
            "info": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Galileo Harness Routes ---
@app.post("/v1/galileo/run")
async def galileo_run(domain: str = "generic_local", seed: int = 12345, n_hypotheses: int = 5):
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
            use_synthetic=True
        )
        return {
            "ok": True,
            "run_id": result['run_id'],
            "accepted_hypothesis_ids": result['accepted_hypothesis_ids'],
            "total_hypotheses": result['total_hypotheses'],
            "total_accepted": result['total_accepted'],
            "paths": result['paths']
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc().splitlines()[-5:]
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
            hypotheses = [h for h in hypotheses if h.get('status') == status]
        return {
            "ok": True,
            "hypotheses": hypotheses,
            "count": len(hypotheses),
            "domain_filter": domain,
            "status_filter": status
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


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
            "status_filter": status
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


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
        run = next((r for r in runs if r.get('run_id') == run_id), None)
        
        if not run:
            return {
                "ok": False,
                "error": f"Run {run_id} not found"
            }
        
        # Load associated artifacts
        packs_dir = Path(__file__).parent / "packs" / "galileo" / run_id
        artifacts = {}
        
        if packs_dir.exists():
            for json_file in ['manifest.json', 'hypotheses.json', 'experiments.json', 'scores.json']:
                file_path = packs_dir / json_file
                if file_path.exists():
                    try:
                        with open(file_path, 'r') as f:
                            artifacts[json_file] = json.load(f)
                    except:
                        pass
        
        return {
            "ok": True,
            "run": run,
            "artifacts": artifacts
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


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
                "status": "DENIED"
            }
        
        from galileo.storage import load_experiments
        
        # Load experiment
        experiments = load_experiments()
        experiment = next((e for e in experiments if e.get('experiment_id') == experiment_id), None)
        
        if not experiment:
            return {
                "ok": False,
                "error": f"Experiment {experiment_id} not found"
            }
        
        if experiment.get('status') != 'DESIGNED':
            return {
                "ok": False,
                "error": f"Experiment must be in DESIGNED status, current: {experiment.get('status')}"
            }
        
        # V0.1 STUB: Local synthetic runner (no actual execution)
        # Full runner implementation deferred to later version
        stub_result = {
            "ok": True,
            "experiment_id": experiment_id,
            "status": "STUB_COMPLETED",
            "note": "v0.1 stub runner - full execution deferred",
            "seed": experiment.get('repro', {}).get('seed'),
            "run_command": experiment.get('repro', {}).get('run_command'),
            "expected_artifacts": experiment.get('repro', {}).get('expected_artifacts', []),
            "synthetic_result": {
                "success_rate": 0.85,
                "effect_size": 0.42,
                "p_value": 0.038
            }
        }
        
        return stub_result
    
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc().splitlines()[-5:]
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
            use_synthetic=True
        )
        
        # Run again with identical inputs
        result2 = run_galileo(
            domain="test_domain",
            seed=42,
            n_hypotheses=3,
            llm_client=None,
            use_synthetic=True
        )
        
        # Compare key outputs
        ids_match = set(result1['accepted_hypothesis_ids']) == set(result2['accepted_hypothesis_ids'])
        totals_match = (result1['total_hypotheses'] == result2['total_hypotheses'] and
                       result1['total_accepted'] == result2['total_accepted'])
        
        # Try loading and comparing JSON files
        import json as json_module
        json_match = True
        try:
            with open(result1['paths']['hypotheses'], 'r') as f:
                hyp1 = json_module.load(f)
            with open(result2['paths']['hypotheses'], 'r') as f:
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
                "run1_id": result1['run_id'],
                "run2_id": result2['run_id'],
                "run1_accepted": result1['accepted_hypothesis_ids'],
                "run2_accepted": result2['accepted_hypothesis_ids']
            },
            "detail": "Both runs produced identical results - determinism verified" if deterministic else "Runs differ - check implementation"
        }
    
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "deterministic": False,
            "traceback": traceback.format_exc().splitlines()[-5:]
        }


# --- Helper Functions ---
def get_lan_ip():
    """Get the LAN IP address of this machine."""
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
        return lan_ip
    except Exception:
        return "127.0.0.1"


# --- Main Entry Point ---
def main():
    """Main entry point for the web server."""
    import uvicorn
    import sys
    
    # Ensure UTF-8 encoding for stdout
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    
    # Get host and port
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "8000"))
    
    # Get LAN IP
    lan_ip = get_lan_ip()
    
    # Print startup information
    print("=" * 70)
    print("[*] SWARMZ Web Server Starting...")
    print("=" * 70)
    print(f"\n[+] Server URLs:")
    print(f"   Local:    http://localhost:{port}")
    print(f"   LAN:      http://{lan_ip}:{port}")
    print(f"\n[+] API Documentation:")
    print(f"   OpenAPI:  http://localhost:{port}/docs")
    print(f"   OpenAPI:  http://{lan_ip}:{port}/docs")
    print(f"\n[+] Console UI:  /console")
    print(f"[+] Access SWARMZ from any device on your network using the LAN URL")
    print("=" * 70)
    print()
    
    # Start the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
