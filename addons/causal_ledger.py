# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Causal Ledger â€” Single Lever Rule.

Every run must declare exactly "what changed" as a precise diff.
Reject runs without a declared lever.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from addons.config_ext import get_config

_LEDGER_FILE = "addons/data/causal_ledger.jsonl"


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


def declare_lever(mission_id: str, lever: str, diff_summary: str) -> Dict[str, Any]:
    """Declare what single lever this run changes."""
    p = Path(_LEDGER_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "mission_id": mission_id,
        "lever": lever,
        "diff_summary": diff_summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(p, "a") as f:
        f.write(json.dumps(entry) + "\n")
    _audit("lever_declared", entry)
    return {"status": "declared", "entry": entry}


def validate_lever(mission_id: str) -> Dict[str, Any]:
    """Check whether a mission has a declared lever.  Reject if missing."""
    entries = load_ledger()
    for e in reversed(entries):
        if e.get("mission_id") == mission_id:
            return {"valid": True, "lever": e.get("lever")}
    return {"valid": False, "error": "No lever declared for this mission â€” run rejected"}


def load_ledger() -> List[Dict[str, Any]]:
    p = Path(_LEDGER_FILE)
    if not p.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with open(p) as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries

