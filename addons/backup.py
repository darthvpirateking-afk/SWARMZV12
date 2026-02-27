# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Export / Import Backups â€” migrate state between devices.

export â†’ ZIP of data/ directory (optionally encrypted).
import â†’ unpack ZIP, verify, replace data/, log audit entry.
"""

import io
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from addons.config_ext import get_config


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


def export_backup(data_dir: str = "data") -> bytes:
    """Create a ZIP archive of the data directory and return bytes."""
    buf = io.BytesIO()
    dp = Path(data_dir)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath in sorted(dp.rglob("*")):
            if fpath.is_file():
                zf.write(fpath, fpath.relative_to(dp))
    _audit("backup_exported", {"data_dir": data_dir, "size_bytes": buf.tell()})
    return buf.getvalue()


def import_backup(zip_bytes: bytes, data_dir: str = "data") -> Dict[str, Any]:
    """Import a ZIP backup.  Backs up current data first (rollback support)."""
    dp = Path(data_dir)
    cfg = get_config()
    backup_root = Path(cfg.get("backup_dir", "addons/data/backups"))
    backup_root.mkdir(parents=True, exist_ok=True)

    # Reversible: snapshot current
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rollback_path = backup_root / f"pre_import_{ts}"
    if dp.exists():
        shutil.copytree(dp, rollback_path)

    # Unpack
    buf = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(buf, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            return {"error": f"Corrupt file in archive: {bad}"}
        zf.extractall(dp)

    _audit("backup_imported", {"rollback_path": str(rollback_path)})
    return {"status": "imported", "rollback_path": str(rollback_path)}


def rollback_import(rollback_path: str, data_dir: str = "data") -> Dict[str, Any]:
    """Restore data from a previous backup snapshot."""
    rp = Path(rollback_path)
    dp = Path(data_dir)
    if not rp.exists():
        return {"error": "Rollback path not found"}
    if dp.exists():
        shutil.rmtree(dp)
    shutil.copytree(rp, dp)
    _audit("backup_rollback", {"restored_from": rollback_path})
    return {"status": "rolled_back", "restored_from": rollback_path}
