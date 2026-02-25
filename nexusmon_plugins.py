#!/usr/bin/env python3
"""
Plugin Management Routes — FastAPI router for plugin ecosystem.
Endpoints:
  GET /v1/plugins              — installed + unlockable plugins
  GET /v1/plugins/community    — community registry (local manifests)
  POST /v1/plugins/install     — install from URL
  POST /v1/plugins/unlock      — unlock gated plugin
  GET /v1/timeline             — organism evolution timeline
"""

import os
import json
import tempfile
import shutil
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from timeline_store import load_timeline, get_stats
from event_hooks import on_plugin_installed, on_plugin_unlocked
from event_hooks import get_event_buffer, clear_event_buffer

router = APIRouter()

# ─────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────

class PluginRecord(BaseModel):
    id: str
    type: str
    version: str
    trust: str
    sandbox: str
    granted_caps: List[str]
    state: str


class InstallRequest(BaseModel):
    url: str


class UnlockRequest(BaseModel):
    id: str


# ─────────────────────────────────────────────────────────────
# GET /v1/plugins — Installed + Unlockable
# ─────────────────────────────────────────────────────────────

@router.get("/v1/plugins")
async def list_plugins() -> Dict[str, Any]:
    """
    List all installed and unlockable plugins.
    """

    # Fetch installed from local loader or registry
    # For now, mock data; replace with real registry.get_all()
    installed = [
        {
            "id": "scout-worker",
            "type": "worker",
            "version": "1.2.0",
            "trust": "community",
            "sandbox": "subprocess",
            "granted_caps": ["artifact.read", "bus.emit"],
            "state": "active"
        },
        {
            "id": "cosmic-skin",
            "type": "skin",
            "version": "2.1.0",
            "trust": "community",
            "sandbox": "none",
            "granted_caps": ["artifact.read"],
            "state": "active"
        }
    ]

    # Unlockable: gated by rank/XP
    # Mock data; replace with real unlock policy engine
    unlockable = [
        {
            "id": "parallel-node-v2",
            "type": "worker",
            "version": "2.0.0",
            "requires": {
                "rank": "C",
                "xp": 500
            }
        },
        {
            "id": "evolution-burst",
            "type": "mission",
            "version": "1.5.0",
            "requires": {
                "rank": "B",
                "xp": 1200
            }
        }
    ]

    return {
        "installed": installed,
        "unlockable": unlockable
    }


# ─────────────────────────────────────────────────────────────
# GET /v1/plugins/community — Community Registry
# ─────────────────────────────────────────────────────────────

@router.get("/v1/plugins/community")
async def get_community_registry() -> Dict[str, Any]:
    """
    Load community plugin registry from local manifest files.
    Phase 1: reads from plugins/*.manifest.json
    Phase 2: remote registry + caching
    """

    registry = {
        "registry_version": "1.0.0",
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "plugins": []
    }

    # Scan plugins/ for manifest.json files
    plugins_dir = "plugins"
    if os.path.isdir(plugins_dir):
        for item in os.listdir(plugins_dir):
            manifest_path = os.path.join(plugins_dir, item, "manifest.json")
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r") as f:
                        manifest = json.load(f)

                    registry["plugins"].append({
                        "id": manifest.get("id"),
                        "type": manifest.get("type"),
                        "version": manifest.get("version"),
                        "trust": manifest.get("trust", "unsigned"),
                        "description": manifest.get("manifest", {}).get("description", ""),
                        "dependencies": [d.get("id") for d in manifest.get("dependencies", [])],
                        "sandbox": manifest.get("sandbox", "subprocess"),
                        "repo": f"file://{os.path.abspath(manifest_path)}"
                    })
                except Exception as e:
                    # Skip malformed manifests
                    pass

    return registry


# ─────────────────────────────────────────────────────────────
# POST /v1/plugins/install — Install from URL
# ─────────────────────────────────────────────────────────────

@router.post("/v1/plugins/install")
async def install_plugin(payload: InstallRequest) -> Dict[str, Any]:
    """
    Clone plugin from GitHub URL and ingest into loader.
    Phase 1: simple git clone + validation
    Phase 2: signature validation, sandbox tests, feature flags
    """

    url = payload.url
    if not url:
        raise HTTPException(400, "Missing URL in plugin install request")

    # Sanitize: only allow github.com URLs in phase 1
    if "github.com" not in url.lower():
        raise HTTPException(400, "Phase 1 supports github.com URLs only")

    tmp_dir = tempfile.mkdtemp(prefix="plugin_install_")

    try:
        # Clone repo
        subprocess.run(
            ["git", "clone", url, tmp_dir],
            check=True,
            capture_output=True,
            timeout=30
        )

        # Validate manifest.json exists
        manifest_path = os.path.join(tmp_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            raise HTTPException(400, "No manifest.json found in repo root")

        # Load and validate manifest
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        plugin_id = manifest.get("id")
        if not plugin_id:
            raise HTTPException(400, "Manifest missing 'id' field")

        # Move to controlled plugin path
        dest_dir = os.path.join("plugins", plugin_id)
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        shutil.move(tmp_dir, dest_dir)

        # Fire event hook — logs to timeline + notification buffer
        on_plugin_installed(plugin_id, url, dest_dir)

        return {
            "status": "ok",
            "plugin_id": plugin_id,
            "version": manifest.get("version"),
            "message": f"Installed {plugin_id} successfully"
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(500, "Git clone timed out")
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, f"Git clone failed: {e.stderr.decode()}")
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid manifest.json (not valid JSON)")
    except Exception as e:
        raise HTTPException(500, f"Install failed: {str(e)}")
    finally:
        # Cleanup temp dir if it still exists
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)


# ─────────────────────────────────────────────────────────────
# POST /v1/plugins/unlock — Unlock Gated Plugin
# ─────────────────────────────────────────────────────────────

@router.post("/v1/plugins/unlock")
async def unlock_plugin(payload: UnlockRequest) -> Dict[str, Any]:
    """
    Unlock a rank/XP-gated plugin.
    Phase 1: mock policy check + operator approval
    Phase 2: real rank/XP engine from organism profile
    """

    plugin_id = payload.id
    if not plugin_id:
        raise HTTPException(400, "Missing plugin id")

    # Policy check (mock for phase 1)
    # Replace with real calls to:
    # - organism.get_operator_rank()
    # - organism.get_operator_xp()
    # - operator_approval_required(plugin_id)

    operator_rank = "C"  # Mock
    operator_xp = 600   # Mock

    requirement_rank = {
        "parallel-node-v2": "C",
        "evolution-burst": "B"
    }.get(plugin_id)

    requirement_xp = {
        "parallel-node-v2": 500,
        "evolution-burst": 1200
    }.get(plugin_id)

    if not requirement_rank:
        raise HTTPException(404, f"Plugin {plugin_id} not found in unlockable list")

    # Check rank (simplified; replace with proper comparison)
    rank_order = {"A": 0, "B": 1, "C": 2, "D": 3}
    if rank_order.get(operator_rank, 99) > rank_order.get(requirement_rank, 99):
        raise HTTPException(
            403,
            f"Rank requirement not met: need {requirement_rank}, have {operator_rank}"
        )

    # Check XP
    if operator_xp < requirement_xp:
        raise HTTPException(
            403,
            f"XP requirement not met: need {requirement_xp}, have {operator_xp}"
        )

    # Fire event hook — logs to timeline + notification buffer
    on_plugin_unlocked(plugin_id, operator_rank, operator_xp)

    return {
        "status": "ok",
        "plugin_id": plugin_id,
        "message": f"Unlocked {plugin_id}"
    }


# ─────────────────────────────────────────────────────────────
# GET /v1/timeline — Evolution Timeline
# ─────────────────────────────────────────────────────────────

@router.get("/v1/timeline")
async def get_timeline(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Retrieve organism evolution timeline.
    """
    timeline = load_timeline()

    # Filter by type if specified
    if event_type:
        timeline = [e for e in timeline if e.get("type") == event_type]

    # Sort by timestamp (most recent first)
    timeline.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    # Paginate
    paginated = timeline[offset : offset + limit]

    return {
        "timeline": paginated,
        "total": len(timeline),
        "limit": limit,
        "offset": offset,
        "stats": get_stats()
    }


# ─────────────────────────────────────────────────────────────
# GET /v1/timeline/stats — Quick organism stats
# ─────────────────────────────────────────────────────────────

@router.get("/v1/timeline/stats")
async def timeline_stats() -> Dict[str, Any]:
    """
    Quick summary of organism evolution.
    """
    return get_stats()

# ─────────────────────────────────────────────────────────────
# GET /v1/notifications — Real-time notification feed
# ─────────────────────────────────────────────────────────────

@router.get("/v1/notifications")
async def get_notifications(limit: int = Query(20, ge=1, le=100)) -> Dict[str, Any]:
    """
    Retrieve recent events for notification display.
    This polls the event buffer from event_hooks.py
    """
    buffer = get_event_buffer()
    recent = buffer[-limit:] if buffer else []
    
    return {
        "events": recent,
        "total": len(buffer),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
