# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Event-sourced replay â€” rebuild state from audit.jsonl.

Deterministic tool: reads the audit log and re-derives system state
for debugging and recovery.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from addons.config_ext import get_config


def load_audit_entries(audit_path: str | None = None) -> List[Dict[str, Any]]:
    cfg = get_config()
    path = Path(audit_path or cfg.get("audit_file", "data/audit.jsonl"))
    entries: List[Dict[str, Any]] = []
    if path.exists():
        with open(path) as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    return entries


def replay_state(audit_path: str | None = None) -> Dict[str, Any]:
    """Replay audit log and derive a summary state snapshot."""
    entries = load_audit_entries(audit_path)

    missions_created = 0
    missions_completed = 0
    missions_failed = 0
    missions_blocked = 0
    schema_migrations: List[str] = []
    backups_exported = 0
    backups_imported = 0
    auth_denials = 0
    quarantine_events = 0

    for e in entries:
        et = e.get("event_type", "")
        if et == "mission_created":
            missions_created += 1
        elif et == "mission_completed":
            missions_completed += 1
        elif et == "mission_failed":
            missions_failed += 1
        elif et == "mission_blocked":
            missions_blocked += 1
        elif et == "schema_migration":
            schema_migrations.append(e.get("details", {}).get("label", "?"))
        elif et == "backup_exported":
            backups_exported += 1
        elif et == "backup_imported":
            backups_imported += 1
        elif et == "lan_auth_denied":
            auth_denials += 1
        elif et == "quarantine_entered":
            quarantine_events += 1

    return {
        "total_events": len(entries),
        "missions_created": missions_created,
        "missions_completed": missions_completed,
        "missions_failed": missions_failed,
        "missions_blocked": missions_blocked,
        "schema_migrations": schema_migrations,
        "backups_exported": backups_exported,
        "backups_imported": backups_imported,
        "auth_denials": auth_denials,
        "quarantine_events": quarantine_events,
        "replayed_at": datetime.now(timezone.utc).isoformat(),
    }
