# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Approval Queue + Patchpack Apply/Rollback.

Patch proposals go into a pending queue.
Apply/rollback is explicit and audited.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from addons.config_ext import get_config


def _queue_path() -> Path:
    cfg = get_config()
    p = Path(cfg.get("approval_queue_file", "addons/data/approval_queue.jsonl"))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _audit(event: str, details: dict) -> None:
    cfg = get_config()
    audit_path = Path(cfg.get("audit_file", "data/audit.jsonl"))
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event,
        "details": details,
    }
    with open(audit_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def submit_patch(description: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    patch_id = str(uuid.uuid4())[:8]
    entry = {
        "patch_id": patch_id,
        "description": description,
        "payload": payload,
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(_queue_path(), "a") as f:
        f.write(json.dumps(entry) + "\n")
    _audit("patch_submitted", {"patch_id": patch_id, "description": description})
    return entry


def list_patches(status: Optional[str] = None) -> List[Dict[str, Any]]:
    patches: List[Dict[str, Any]] = []
    p = _queue_path()
    if p.exists():
        with open(p) as f:
            for line in f:
                if line.strip():
                    e = json.loads(line)
                    if status is None or e.get("status") == status:
                        patches.append(e)
    return patches


def _rewrite_queue(patches: List[Dict[str, Any]]) -> None:
    with open(_queue_path(), "w") as f:
        for p in patches:
            f.write(json.dumps(p) + "\n")


def approve_patch(patch_id: str, operator_key: str) -> Dict[str, Any]:
    cfg = get_config()
    expected = cfg.get("operator_pin", "")
    if expected and operator_key != expected:
        return {"error": "Invalid operator key"}

    patches = list_patches()
    for p in patches:
        if p["patch_id"] == patch_id and p["status"] == "pending":
            p["status"] = "approved"
            p["approved_at"] = datetime.now(timezone.utc).isoformat()
            _rewrite_queue(patches)
            _audit("patch_approved", {"patch_id": patch_id})
            return p
    return {"error": "Patch not found or not pending"}


def apply_patch(patch_id: str) -> Dict[str, Any]:
    patches = list_patches()
    for p in patches:
        if p["patch_id"] == patch_id and p["status"] == "approved":
            p["status"] = "applied"
            p["applied_at"] = datetime.now(timezone.utc).isoformat()
            _rewrite_queue(patches)
            _audit("patch_applied", {"patch_id": patch_id, "payload": p.get("payload")})
            return p
    return {"error": "Patch not found or not approved"}


def rollback_patch(patch_id: str) -> Dict[str, Any]:
    patches = list_patches()
    for p in patches:
        if p["patch_id"] == patch_id and p["status"] == "applied":
            p["status"] = "rolled_back"
            p["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
            _rewrite_queue(patches)
            _audit("patch_rolled_back", {"patch_id": patch_id})
            return p
    return {"error": "Patch not found or not applied"}
