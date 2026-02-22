# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Pinterest Integration Bridge (v1.0)

Provides Pinterest API v5 integration endpoints:
  GET  /v1/pinterest/boards  — Lists user's boards
  POST /v1/pinterest/sync    — Syncs pins from boards with optional auto-apply
  GET  /v1/pinterest/status  — Returns sync status and last sync time

Append-only JSONL logs in data/pinterest/.
Fail-open: never crashes the runtime.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel


# ── paths ──────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _ROOT / "config" / "runtime.json"
_PINTEREST_DIR = _ROOT / "data" / "pinterest"
_SYNC_LOG = _PINTEREST_DIR / "sync.jsonl"

# ── in-memory dedupe (simple TTL map) ──────────────────────────────────────
_DEDUPE: Dict[str, float] = {}
_DEDUPE_TTL = 600  # 10 minutes

# ── sync state ─────────────────────────────────────────────────────────────
_SYNC_STATE: Dict[str, Any] = {
    "last_sync": None,
    "total_pins_synced": 0,
    "boards_synced": [],
    "status": "idle",
}

# Pinterest API v5 base URL
_PINTEREST_API_BASE = "https://api.pinterest.com/v5"


# ── helpers ────────────────────────────────────────────────────────────────


def _load_pinterest_config() -> Dict[str, Any]:
    """Load the integrations.pinterest block from config/runtime.json."""
    try:
        cfg = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        return cfg.get("integrations", {}).get("pinterest", {})
    except Exception:
        return {}


def _get_pinterest_token() -> Optional[str]:
    """Get Pinterest API token from environment variable."""
    return os.environ.get("PINTEREST_API_TOKEN")


def _append_log(path: Path, obj: Dict[str, Any]) -> None:
    """Append one JSON line (fail-silent)."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, separators=(",", ":")) + "\n")
    except Exception:
        pass  # fail-open


def _prune_dedupe() -> None:
    """Remove expired dedupe keys."""
    now = time.time()
    expired = [k for k, ts in _DEDUPE.items() if now - ts > _DEDUPE_TTL]
    for k in expired:
        _DEDUPE.pop(k, None)


def _dedupe_pins(pins: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prevents duplicate processing using in-memory TTL map.
    Returns only pins that haven't been processed recently.
    """
    _prune_dedupe()
    unique_pins: List[Dict[str, Any]] = []
    now = time.time()

    for pin in pins:
        pin_id = pin.get("id", "")
        if pin_id and pin_id not in _DEDUPE:
            _DEDUPE[pin_id] = now
            unique_pins.append(pin)

    return unique_pins


def _pinterest_api(
    endpoint: str,
    method: str = "GET",
    body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Makes authenticated requests to Pinterest API v5.
    
    Args:
        endpoint: API endpoint (e.g., "/boards", "/pins")
        method: HTTP method (GET, POST, etc.)
        body: Optional request body for POST/PUT requests
    
    Returns:
        Parsed JSON response or error dict
    """
    token = _get_pinterest_token()
    if not token:
        return {"error": "PINTEREST_API_TOKEN not set", "items": []}

    url = f"{_PINTEREST_API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        data = json.dumps(body).encode("utf-8") if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            response_body = resp.read().decode("utf-8")
            return json.loads(response_body) if response_body else {}
            
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")[:500]
        except Exception:
            pass
        return {"error": f"HTTP {e.code}: {error_body}", "items": []}
    except Exception as exc:
        return {"error": str(exc)[:300], "items": []}


def _store_pin_artifact(pin: Dict[str, Any]) -> bool:
    """
    Store a pin as artifact via ArtifactVault.
    Returns True if successful, False otherwise.
    """
    try:
        from core.artifact_vault import ArtifactVault
        vault = ArtifactVault()
        vault.store("pinterest", pin, source="pinterest")
        return True
    except ImportError:
        # ArtifactVault not available, log to file instead
        _append_log(
            _PINTEREST_DIR / "artifacts.jsonl",
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "type": "pinterest_pin",
                "pin": pin,
            },
        )
        return True
    except Exception:
        return False


def _apply_pin_mission(pin: Dict[str, Any]) -> bool:
    """
    Create a mission for a pin via MissionEngine.
    Returns True if successful, False otherwise.
    """
    try:
        from core.mission_engine import MissionEngine
        engine = MissionEngine()
        engine.run_mission("apply pinterest idea", {"pin": pin})
        return True
    except ImportError:
        # MissionEngine not available, try backend path
        try:
            from backend.runtime.core.engine import MissionEngine
            engine = MissionEngine()
            engine.add_mission({
                "goal": "apply pinterest idea",
                "context": {"pin": pin},
            })
            return True
        except Exception:
            return False
    except Exception:
        return False


# ── request models ─────────────────────────────────────────────────────────


class PinterestSyncBody(BaseModel):
    """Request body for Pinterest sync endpoint."""
    board: str = "all"  # "all" or specific board_id
    auto_apply: bool = False


# ── registration ───────────────────────────────────────────────────────────


def register_pinterest_bridge(app: FastAPI) -> None:
    """
    Mount Pinterest endpoints on FastAPI app.
    Fail-open design — errors are logged but never crash the server.
    """

    # ── GET /v1/pinterest/boards ───────────────────────────────────────────
    @app.get("/v1/pinterest/boards")
    async def pinterest_boards(request: Request):
        """
        Lists user's boards from Pinterest API.
        
        Returns:
            {"ok": bool, "boards": [...], "error": str|null}
        """
        pcfg = _load_pinterest_config()
        now = datetime.now(timezone.utc).isoformat()

        # Check if integration is disabled
        if not pcfg.get("enabled", True):
            return {"ok": False, "boards": [], "error": "pinterest integration disabled"}

        # Check for token
        if not _get_pinterest_token():
            _append_log(
                _SYNC_LOG,
                {
                    "ts": now,
                    "action": "list_boards",
                    "ok": False,
                    "error": "PINTEREST_API_TOKEN not set",
                },
            )
            return {"ok": False, "boards": [], "error": "PINTEREST_API_TOKEN not set"}

        # Fetch boards from Pinterest API
        response = _pinterest_api("/boards")
        
        if "error" in response and response.get("error"):
            _append_log(
                _SYNC_LOG,
                {
                    "ts": now,
                    "action": "list_boards",
                    "ok": False,
                    "error": response.get("error"),
                },
            )
            return {"ok": False, "boards": [], "error": response.get("error")}

        boards = response.get("items", [])
        
        _append_log(
            _SYNC_LOG,
            {
                "ts": now,
                "action": "list_boards",
                "ok": True,
                "board_count": len(boards),
            },
        )

        return {"ok": True, "boards": boards, "error": None}

    # ── POST /v1/pinterest/sync ────────────────────────────────────────────
    @app.post("/v1/pinterest/sync")
    async def pinterest_sync(body: PinterestSyncBody, request: Request):
        """
        Syncs pins from boards.
        
        Accepts:
            {"board": "all" | board_id, "auto_apply": true}
        
        Returns:
            {"ok": bool, "pin_count": N, "boards_synced": [...], "auto_applied": bool}
        """
        global _SYNC_STATE
        
        pcfg = _load_pinterest_config()
        now = datetime.now(timezone.utc).isoformat()

        # Check if integration is disabled
        if not pcfg.get("enabled", True):
            return {
                "ok": False,
                "pin_count": 0,
                "boards_synced": [],
                "auto_applied": False,
                "error": "pinterest integration disabled",
            }

        # Check for token
        if not _get_pinterest_token():
            _append_log(
                _SYNC_LOG,
                {
                    "ts": now,
                    "action": "sync",
                    "ok": False,
                    "error": "PINTEREST_API_TOKEN not set",
                },
            )
            return {
                "ok": False,
                "pin_count": 0,
                "boards_synced": [],
                "auto_applied": False,
                "error": "PINTEREST_API_TOKEN not set",
            }

        _SYNC_STATE["status"] = "syncing"
        boards_to_sync: List[Dict[str, Any]] = []
        all_pins: List[Dict[str, Any]] = []
        boards_synced: List[str] = []
        error_msg: Optional[str] = None

        try:
            # Determine which boards to sync
            if body.board == "all":
                boards_response = _pinterest_api("/boards")
                if "error" in boards_response and boards_response.get("error"):
                    error_msg = boards_response.get("error")
                else:
                    boards_to_sync = boards_response.get("items", [])
            else:
                # Single board specified
                boards_to_sync = [{"id": body.board, "name": body.board}]

            # Fetch pins from each board
            for board in boards_to_sync:
                board_id = board.get("id", "")
                if not board_id:
                    continue

                pins_response = _pinterest_api(f"/boards/{board_id}/pins")
                
                if "error" not in pins_response or not pins_response.get("error"):
                    board_pins = pins_response.get("items", [])
                    all_pins.extend(board_pins)
                    boards_synced.append(board_id)

            # Dedupe pins
            unique_pins = _dedupe_pins(all_pins)

            # Store each pin as artifact
            stored_count = 0
            applied_count = 0
            
            for pin in unique_pins:
                pin_payload = {
                    "id": pin.get("id"),
                    "title": pin.get("title", ""),
                    "description": pin.get("description", ""),
                    "link": pin.get("link", ""),
                    "media": pin.get("media", {}),
                    "created_at": pin.get("created_at", ""),
                    "synced_at": now,
                }
                
                if _store_pin_artifact(pin_payload):
                    stored_count += 1

                # Auto-apply if requested
                if body.auto_apply:
                    if _apply_pin_mission(pin_payload):
                        applied_count += 1

            # Update sync state
            _SYNC_STATE["last_sync"] = now
            _SYNC_STATE["total_pins_synced"] += stored_count
            _SYNC_STATE["boards_synced"] = boards_synced
            _SYNC_STATE["status"] = "idle"

            _append_log(
                _SYNC_LOG,
                {
                    "ts": now,
                    "action": "sync",
                    "ok": True,
                    "pin_count": stored_count,
                    "boards_synced": boards_synced,
                    "auto_applied": body.auto_apply,
                    "applied_count": applied_count,
                },
            )

            return {
                "ok": True,
                "pin_count": stored_count,
                "boards_synced": boards_synced,
                "auto_applied": body.auto_apply,
            }

        except Exception as exc:
            _SYNC_STATE["status"] = "error"
            error_msg = str(exc)[:300]
            
            _append_log(
                _SYNC_LOG,
                {
                    "ts": now,
                    "action": "sync",
                    "ok": False,
                    "error": error_msg,
                },
            )

            return {
                "ok": False,
                "pin_count": 0,
                "boards_synced": [],
                "auto_applied": False,
                "error": error_msg,
            }

    # ── GET /v1/pinterest/status ───────────────────────────────────────────
    @app.get("/v1/pinterest/status")
    async def pinterest_status(request: Request):
        """
        Returns sync status and last sync time.
        
        Returns:
            {
                "ok": bool,
                "status": "idle" | "syncing" | "error",
                "last_sync": str | null,
                "total_pins_synced": int,
                "boards_synced": [...]
            }
        """
        pcfg = _load_pinterest_config()

        # Check if integration is disabled
        if not pcfg.get("enabled", True):
            return {
                "ok": False,
                "status": "disabled",
                "last_sync": None,
                "total_pins_synced": 0,
                "boards_synced": [],
                "error": "pinterest integration disabled",
            }

        return {
            "ok": True,
            "status": _SYNC_STATE["status"],
            "last_sync": _SYNC_STATE["last_sync"],
            "total_pins_synced": _SYNC_STATE["total_pins_synced"],
            "boards_synced": _SYNC_STATE["boards_synced"],
        }
