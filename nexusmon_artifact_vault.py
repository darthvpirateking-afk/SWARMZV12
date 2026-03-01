# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
NEXUSMON Artifact Vault
───────────────────────
Versioned artifact storage. Every worker/mission output is stored,
reviewed, and replayable.

Wire into swarmz_server.py after fuse_cognition:

    try:
        from nexusmon_artifact_vault import fuse_artifact_vault
        fuse_artifact_vault(app)
    except Exception as e:
        print(f"Warning: artifact vault failed: {e}")
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# STORAGE HELPERS  (mirror nexusmon_organism.py exactly)
# ══════════════════════════════════════════════════════════════

def _data_dir() -> Path:
    db = os.environ.get("DATABASE_URL", "data/nexusmon.db")
    d = Path(db).parent
    d.mkdir(parents=True, exist_ok=True)
    return d


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def _append_jsonl(path: Path, record: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _rewrite_jsonl(path: Path, records: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


# ══════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════

_ARTIFACTS_FILE = "artifacts.jsonl"

VALID_TYPES    = {"TEXT", "CODE", "DATA", "REPORT", "ANALYSIS", "DECISION", "LOG"}
VALID_STATUSES = {"PENDING_REVIEW", "APPROVED", "REJECTED", "ARCHIVED"}


# ══════════════════════════════════════════════════════════════
# ARTIFACT CRUD
# ══════════════════════════════════════════════════════════════

def _artifacts_path() -> Path:
    return _data_dir() / _ARTIFACTS_FILE


def _load_artifacts() -> List[Dict]:
    return _load_jsonl(_artifacts_path())


def _save_artifact(artifact: Dict) -> None:
    artifacts = _load_artifacts()
    idx = next((i for i, a in enumerate(artifacts) if a["id"] == artifact["id"]), None)
    if idx is not None:
        artifacts[idx] = artifact
        _rewrite_jsonl(_artifacts_path(), artifacts)
    else:
        _append_jsonl(_artifacts_path(), artifact)


# ══════════════════════════════════════════════════════════════
# PUBLIC FUNCTIONS
# ══════════════════════════════════════════════════════════════

def store_artifact(
    mission_id: str,
    task_id: str,
    type: str,
    title: str,
    content: Any,
    input_snapshot: Optional[Dict] = None,
) -> Dict:
    """Store a new artifact (or a new version of an existing one by title+mission)."""
    artifact_type = str(type).upper()
    if artifact_type not in VALID_TYPES:
        artifact_type = "LOG"

    # Check for existing artifact with same title+mission to version it
    existing = [
        a for a in _load_artifacts()
        if a.get("mission_id") == mission_id and a.get("title") == title
    ]
    version = len(existing) + 1
    prev_id = existing[-1]["id"] if existing else ""

    artifact: Dict[str, Any] = {
        "id": str(uuid4()),
        "version": version,
        "mission_id": mission_id,
        "task_id": task_id,
        "type": artifact_type,
        "title": title,
        "content": content,
        "input_snapshot": input_snapshot or {},
        "status": "PENDING_REVIEW",
        "operator_notes": "",
        "created_at": _utc(),
        "reviewed_at": "",
        "reviewed_by": "",
        "previous_version_id": prev_id,
    }
    _append_jsonl(_artifacts_path(), artifact)
    logger.debug("Artifact stored: %s (v%d) type=%s", artifact["id"], version, artifact_type)
    return artifact


def approve_artifact(artifact_id: str, notes: str = "") -> Dict:
    artifact = get_artifact(artifact_id)
    if not artifact:
        raise ValueError(f"Artifact not found: {artifact_id}")
    artifact["status"] = "APPROVED"
    artifact["operator_notes"] = notes
    artifact["reviewed_at"] = _utc()
    artifact["reviewed_by"] = "operator"
    _save_artifact(artifact)
    try:
        from nexusmon_operator_rank import award_xp as _rank_xp
        _rank_xp("approve_artifact", detail=artifact_id)
    except Exception:
        pass
    return artifact


def reject_artifact(artifact_id: str, notes: str = "") -> Dict:
    artifact = get_artifact(artifact_id)
    if not artifact:
        raise ValueError(f"Artifact not found: {artifact_id}")
    artifact["status"] = "REJECTED"
    artifact["operator_notes"] = notes
    artifact["reviewed_at"] = _utc()
    artifact["reviewed_by"] = "operator"
    _save_artifact(artifact)
    try:
        from nexusmon_operator_rank import award_xp as _rank_xp
        _rank_xp("reject_artifact", detail=artifact_id)
    except Exception:
        pass
    return artifact


def get_artifact(artifact_id: str) -> Optional[Dict]:
    return next((a for a in _load_artifacts() if a["id"] == artifact_id), None)


def list_artifacts(
    mission_id: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    artifacts = _load_artifacts()
    if mission_id:
        artifacts = [a for a in artifacts if a.get("mission_id") == mission_id]
    if status:
        artifacts = [a for a in artifacts if a.get("status") == status.upper()]
    if type:
        artifacts = [a for a in artifacts if a.get("type") == type.upper()]
    return artifacts[-limit:]


def get_artifact_history(artifact_id: str) -> List[Dict]:
    """Return all versions of an artifact, oldest first."""
    target = get_artifact(artifact_id)
    if not target:
        return []

    mission_id = target.get("mission_id")
    title = target.get("title")

    return [
        a for a in _load_artifacts()
        if a.get("mission_id") == mission_id and a.get("title") == title
    ]


# ══════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ══════════════════════════════════════════════════════════════

class ArtifactCreate(BaseModel):
    mission_id: str
    task_id: str = ""
    type: str = Field("LOG", pattern="^(TEXT|CODE|DATA|REPORT|ANALYSIS|DECISION|LOG)$")
    title: str = Field(..., min_length=1)
    content: Any = None
    input_snapshot: Dict[str, Any] = Field(default_factory=dict)


class ReviewPayload(BaseModel):
    notes: str = ""


# ══════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════

router = APIRouter(prefix="/v1/vault", tags=["artifact-vault"])


@router.get("/stats")
@router.get("/artifacts/stats")
def get_stats():
    artifacts = _load_artifacts()
    total = len(artifacts)
    by_status: Dict[str, int] = {}
    by_type: Dict[str, int] = {}
    for a in artifacts:
        s = a.get("status", "PENDING_REVIEW")
        by_status[s] = by_status.get(s, 0) + 1
        t = a.get("type", "LOG")
        by_type[t] = by_type.get(t, 0) + 1
    return {
        "ok": True,
        "total": total,
        "pending_review": by_status.get("PENDING_REVIEW", 0),
        "by_status": by_status,
        "by_type": by_type,
    }


@router.post("/artifacts")
def store_artifact_endpoint(payload: ArtifactCreate):
    try:
        artifact = store_artifact(
            mission_id=payload.mission_id,
            task_id=payload.task_id,
            type=payload.type,
            title=payload.title,
            content=payload.content,
            input_snapshot=payload.input_snapshot,
        )
        return {"ok": True, "artifact": artifact}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/artifacts")
def list_artifacts_endpoint(
    mission_id: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 100,
):
    artifacts = list_artifacts(mission_id=mission_id, status=status, type=type, limit=limit)
    return {"ok": True, "artifacts": artifacts, "count": len(artifacts)}


@router.get("/artifacts/{artifact_id}/history")
def get_history_endpoint(artifact_id: str):
    history = get_artifact_history(artifact_id)
    if not history:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"ok": True, "history": history, "versions": len(history)}


@router.post("/artifacts/{artifact_id}/approve")
def approve_endpoint(artifact_id: str, payload: ReviewPayload = ReviewPayload()):
    try:
        artifact = approve_artifact(artifact_id, payload.notes)
        return {"ok": True, "artifact": artifact}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/artifacts/{artifact_id}/reject")
def reject_endpoint(artifact_id: str, payload: ReviewPayload = ReviewPayload()):
    try:
        artifact = reject_artifact(artifact_id, payload.notes)
        return {"ok": True, "artifact": artifact}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/artifacts/{artifact_id}")
def get_artifact_endpoint(artifact_id: str):
    artifact = get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"ok": True, "artifact": artifact}


@router.get("/missions/{mission_id}/artifacts")
def get_mission_artifacts(mission_id: str):
    artifacts = list_artifacts(mission_id=mission_id)
    return {"ok": True, "artifacts": artifacts, "count": len(artifacts)}


# ══════════════════════════════════════════════════════════════
# FUSE
# ══════════════════════════════════════════════════════════════

def fuse_artifact_vault(app: FastAPI) -> None:
    """Wire artifact vault routes into the FastAPI app."""
    app.include_router(router)
    total = len(_load_artifacts())
    pending = sum(1 for a in _load_artifacts() if a.get("status") == "PENDING_REVIEW")
    logger.info("Artifact vault fused. %d artifacts on disk (%d pending review)", total, pending)
