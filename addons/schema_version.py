# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Schema versioning and boot-time migration.

Stores a ``schema_version`` integer in data/system_state.json.
On boot, runs any pending forward migrations.  Each migration creates
a reversible backup of the data directory first.
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

from addons.config_ext import get_config

CURRENT_SCHEMA_VERSION = 6

# Registry: version â†’ callable(data_dir)
_MIGRATIONS: Dict[int, Callable[[Path], None]] = {}


def register_migration(version: int, fn: Callable[[Path], None]) -> None:
    _MIGRATIONS[version] = fn


def _read_version(state_file: Path) -> int:
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text())
            return int(data.get("schema_version", 0))
        except (json.JSONDecodeError, ValueError):
            pass
    return 0


def _write_version(state_file: Path, version: int) -> None:
    data: Dict[str, Any] = {}
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text())
        except (json.JSONDecodeError, ValueError):
            pass
    data["schema_version"] = version
    state_file.write_text(json.dumps(data, indent=2))


def _backup_data(data_dir: Path, label: str) -> Path:
    cfg = get_config()
    backup_root = Path(cfg.get("backup_dir", "addons/data/backups"))
    backup_root.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = backup_root / f"pre_migration_{label}_{ts}"
    shutil.copytree(data_dir, dest, dirs_exist_ok=False)
    return dest


def _append_audit(event: str, details: dict, data_dir: Path) -> None:
    audit_path = data_dir / "audit.jsonl"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event,
        "details": details,
    }
    with open(audit_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def run_migrations(data_dir: str = "data") -> List[str]:
    """Run pending migrations.  Returns list of applied migration labels."""
    dp = Path(data_dir)
    dp.mkdir(exist_ok=True)
    state_file = dp / "system_state.json"

    current = _read_version(state_file)
    applied: List[str] = []

    for ver in sorted(_MIGRATIONS):
        if ver > current:
            label = f"v{current}_to_v{ver}"
            _backup_data(dp, label)
            _MIGRATIONS[ver](dp)
            _write_version(state_file, ver)
            _append_audit("schema_migration", {"from": current, "to": ver, "label": label}, dp)
            current = ver
            applied.append(label)

    # Ensure version is at least CURRENT_SCHEMA_VERSION even with no migrations
    if current < CURRENT_SCHEMA_VERSION:
        _write_version(state_file, CURRENT_SCHEMA_VERSION)

    return applied


# ---- v1 migration stub (no-op; establishes baseline) ----
def _migrate_v1(data_dir: Path) -> None:
    """Initial schema â€” no structural changes, just stamps version."""
    pass


register_migration(1, _migrate_v1)


def _migrate_v2(data_dir: Path) -> None:
    bootstrap_file = data_dir / "bootstrap_state.json"
    if bootstrap_file.exists():
        return
    payload = {
        "initialized": True,
        "profile": "default",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    bootstrap_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


register_migration(2, _migrate_v2)


def _migrate_v3(data_dir: Path) -> None:
    foundation_file = data_dir / "api_foundation_state.json"
    if foundation_file.exists():
        return
    payload = {
        "version": 1,
        "domains": [
            "cyber",
            "security",
            "defense",
            "science",
            "military",
            "space",
            "engineering",
            "architecture",
        ],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    foundation_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


register_migration(3, _migrate_v3)


def _migrate_v4(data_dir: Path) -> None:
    db_layer_file = data_dir / "database_layer_state.json"
    if db_layer_file.exists():
        return
    payload = {
        "version": 1,
        "engine": "jsonl",
        "collections": ["missions", "audit", "runes", "state", "bad_rows"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db_layer_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


register_migration(4, _migrate_v4)


def _migrate_v5(data_dir: Path) -> None:
    auth_file = data_dir / "operator_auth_state.json"
    if auth_file.exists():
        return
    payload = {
        "version": 1,
        "auth_mode": "operator-key",
        "key_configured": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    auth_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


register_migration(5, _migrate_v5)


def _migrate_v6(data_dir: Path) -> None:
    companion_file = data_dir / "companion_core_state.json"
    if not companion_file.exists():
        companion_payload = {
            "version": 1,
            "source": "core.companion",
            "enabled": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        companion_file.write_text(json.dumps(companion_payload, indent=2), encoding="utf-8")

    milestones_file = data_dir / "build_milestones_state.json"
    if not milestones_file.exists():
        stages = []
        for stage in range(1, 31):
            stages.append(
                {
                    "stage": stage,
                    "title": f"BUILD {stage}",
                    "status": "implemented" if stage <= 5 else "pending",
                }
            )
        history = []
        for stage in range(1, 6):
            history.append(
                {
                    "stage": stage,
                    "title": f"BUILD {stage}",
                    "status": "implemented",
                    "executed_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        milestones_payload = {
            "current_stage": 5,
            "target_stage": 5,
            "stages": stages,
            "history": history,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        milestones_file.write_text(json.dumps(milestones_payload, indent=2), encoding="utf-8")


register_migration(6, _migrate_v6)

