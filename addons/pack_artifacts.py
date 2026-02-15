"""
Pack Artifact Retrieval — list packs, download as ZIP, verify by mission_id.
"""

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from addons.config_ext import get_config


def _packs_dir() -> Path:
    cfg = get_config()
    d = Path(cfg.get("packs_dir", "addons/data/packs"))
    d.mkdir(parents=True, exist_ok=True)
    return d


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


def store_pack(mission_id: str, artifacts: Dict[str, str]) -> Dict[str, Any]:
    """Store a pack of artifacts for a mission.  artifacts = {filename: content}."""
    pack_dir = _packs_dir() / mission_id
    pack_dir.mkdir(parents=True, exist_ok=True)
    for fname, content in artifacts.items():
        (pack_dir / fname).write_text(content)
    meta = {
        "mission_id": mission_id,
        "files": list(artifacts.keys()),
        "stored_at": datetime.now(timezone.utc).isoformat(),
    }
    (pack_dir / "_meta.json").write_text(json.dumps(meta, indent=2))
    _audit("pack_stored", {"mission_id": mission_id, "files": list(artifacts.keys())})
    return meta


def list_packs() -> List[Dict[str, Any]]:
    packs: List[Dict[str, Any]] = []
    for d in sorted(_packs_dir().iterdir()):
        if d.is_dir():
            meta_f = d / "_meta.json"
            if meta_f.exists():
                try:
                    packs.append(json.loads(meta_f.read_text()))
                except (json.JSONDecodeError, OSError):
                    pass
    return packs


def download_pack(mission_id: str) -> Optional[bytes]:
    pack_dir = _packs_dir() / mission_id
    if not pack_dir.exists():
        return None
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath in sorted(pack_dir.rglob("*")):
            if fpath.is_file():
                zf.write(fpath, fpath.relative_to(pack_dir))
    _audit("pack_downloaded", {"mission_id": mission_id})
    return buf.getvalue()


def verify_pack(mission_id: str) -> Dict[str, Any]:
    pack_dir = _packs_dir() / mission_id
    if not pack_dir.exists():
        return {"valid": False, "error": "Pack not found"}
    meta_f = pack_dir / "_meta.json"
    if not meta_f.exists():
        return {"valid": False, "error": "No metadata found"}
    meta = json.loads(meta_f.read_text())
    expected = set(meta.get("files", []))
    actual = {f.name for f in pack_dir.iterdir() if f.is_file() and f.name != "_meta.json"}
    missing = expected - actual
    extra = actual - expected
    return {
        "valid": len(missing) == 0,
        "mission_id": mission_id,
        "expected_files": sorted(expected),
        "actual_files": sorted(actual),
        "missing": sorted(missing),
        "extra": sorted(extra),
    }
