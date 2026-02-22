# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Artifact Vault — structured artifact storage, retrieval, indexing.

Artifacts:
  mission   — output of a mission run
  worker    — output of a worker task
  evolution — form/state transitions
  system    — health, logs, snapshots
  operator  — commands, plans, diffs

Storage layout:
  /swarmz/artifacts/
    missions/     — keyed by missionId-timestamp.json
    workers/      — keyed by workerId-timestamp.json
    evolution/    — form-change-timestamp.json
    system/       — health-timestamp.json
    operator/     — command-timestamp.json
    index/        — by-type.json, latest.json
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

ROOT = Path(__file__).resolve().parent.parent
VAULT_DIR = ROOT / "artifacts"

ArtifactType = Literal["mission", "worker", "evolution", "system", "operator"]

_TYPE_DIRS: Dict[ArtifactType, str] = {
    "mission": "missions",
    "worker": "workers",
    "evolution": "evolution",
    "system": "system",
    "operator": "operator",
}


def _ensure_dirs() -> None:
    """Create vault directory structure if it doesn't exist."""
    for sub in list(_TYPE_DIRS.values()) + ["index"]:
        (VAULT_DIR / sub).mkdir(parents=True, exist_ok=True)


def _index_path() -> Path:
    return VAULT_DIR / "index"


def _update_index(artifact_id: str, artifact_type: ArtifactType) -> None:
    """Update by-type and latest index files."""
    idx_dir = _index_path()
    idx_dir.mkdir(parents=True, exist_ok=True)

    # by-type
    by_type_f = idx_dir / "by-type.json"
    by_type: Dict[str, List[str]] = {}
    if by_type_f.exists():
        try:
            by_type = json.loads(by_type_f.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    by_type.setdefault(artifact_type, [])
    by_type[artifact_type].append(artifact_id)
    # Keep only last 500 per type
    for k in by_type:
        by_type[k] = by_type[k][-500:]
    by_type_f.write_text(json.dumps(by_type, indent=2))

    # latest
    latest_f = idx_dir / "latest.json"
    latest: Dict[str, str] = {}
    if latest_f.exists():
        try:
            latest = json.loads(latest_f.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    latest[artifact_type] = artifact_id
    latest_f.write_text(json.dumps(latest, indent=2))


def store(
    artifact_type: ArtifactType,
    payload: Any,
    source: str = "unknown",
    links: Optional[Dict[str, str]] = None,
    artifact_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Store an artifact in the vault.

    Returns the full artifact metadata envelope.
    """
    _ensure_dirs()
    ts = int(time.time() * 1000)
    now = datetime.now(timezone.utc).isoformat()
    aid = artifact_id or f"{source}-{ts}"

    envelope: Dict[str, Any] = {
        "id": aid,
        "type": artifact_type,
        "timestamp": ts,
        "created_at": now,
        "source": source,
        "payload": payload,
        "links": links or {},
    }

    sub_dir = VAULT_DIR / _TYPE_DIRS[artifact_type]
    sub_dir.mkdir(parents=True, exist_ok=True)
    fpath = sub_dir / f"{aid}.json"
    fpath.write_text(json.dumps(envelope, indent=2, default=str), encoding="utf-8")

    _update_index(aid, artifact_type)

    return envelope


def load(artifact_id: str) -> Optional[Dict[str, Any]]:
    """Load a specific artifact by ID (searches all type dirs)."""
    _ensure_dirs()
    for sub in _TYPE_DIRS.values():
        fpath = VAULT_DIR / sub / f"{artifact_id}.json"
        if fpath.exists():
            try:
                return json.loads(fpath.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
    return None


def load_latest(artifact_type: Optional[ArtifactType] = None) -> Optional[Dict[str, Any]]:
    """Load the latest artifact, optionally filtered by type."""
    latest_f = _index_path() / "latest.json"
    if not latest_f.exists():
        return None
    try:
        latest = json.loads(latest_f.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    if artifact_type:
        aid = latest.get(artifact_type)
        return load(aid) if aid else None
    else:
        # Return the most recent across all types
        best_id = None
        best_ts = 0
        for aid in latest.values():
            art = load(aid)
            if art and art.get("timestamp", 0) > best_ts:
                best_ts = art["timestamp"]
                best_id = aid
        return load(best_id) if best_id else None


def list_artifacts(
    artifact_type: Optional[ArtifactType] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """List artifacts, optionally filtered by type. Most recent first."""
    _ensure_dirs()
    results: List[Dict[str, Any]] = []

    dirs = [VAULT_DIR / _TYPE_DIRS[artifact_type]] if artifact_type else [
        VAULT_DIR / sub for sub in _TYPE_DIRS.values()
    ]

    for d in dirs:
        if not d.exists():
            continue
        for fpath in d.glob("*.json"):
            try:
                art = json.loads(fpath.read_text(encoding="utf-8"))
                results.append(art)
            except (json.JSONDecodeError, OSError):
                continue

    # Sort by timestamp desc, limit
    results.sort(key=lambda a: a.get("timestamp", 0), reverse=True)
    return results[:limit]


def search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Simple text search across artifact payloads."""
    _ensure_dirs()
    q = query.lower()
    results: List[Dict[str, Any]] = []

    for sub in _TYPE_DIRS.values():
        d = VAULT_DIR / sub
        if not d.exists():
            continue
        for fpath in d.glob("*.json"):
            try:
                text = fpath.read_text(encoding="utf-8")
                if q in text.lower():
                    results.append(json.loads(text))
            except (json.JSONDecodeError, OSError):
                continue

    results.sort(key=lambda a: a.get("timestamp", 0), reverse=True)
    return results[:limit]


def get_index() -> Dict[str, Any]:
    """Return the full vault index (by-type counts + latest IDs)."""
    _ensure_dirs()
    idx_dir = _index_path()

    by_type: Dict[str, List[str]] = {}
    by_type_f = idx_dir / "by-type.json"
    if by_type_f.exists():
        try:
            by_type = json.loads(by_type_f.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    latest: Dict[str, str] = {}
    latest_f = idx_dir / "latest.json"
    if latest_f.exists():
        try:
            latest = json.loads(latest_f.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    return {
        "counts": {k: len(v) for k, v in by_type.items()},
        "latest": latest,
        "types": list(_TYPE_DIRS.keys()),
    }
