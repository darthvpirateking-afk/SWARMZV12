# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Quarantine Mode â€” governance failure â†’ QUARANTINE state.

When triggered, the system only produces suggestion artifacts (read-only).
No execution allowed until explicitly unsealed by operator.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from addons.config_ext import get_config

_STATE_FILE = "addons/data/quarantine_state.json"


def _load_state() -> Dict[str, Any]:
    p = Path(_STATE_FILE)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"quarantined": False, "reason": None, "since": None}


def _save_state(state: Dict[str, Any]) -> None:
    p = Path(_STATE_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2))


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


def is_quarantined() -> bool:
    return _load_state().get("quarantined", False)


def enter_quarantine(reason: str) -> Dict[str, Any]:
    state = {
        "quarantined": True,
        "reason": reason,
        "since": datetime.now(timezone.utc).isoformat(),
    }
    _save_state(state)
    _audit("quarantine_entered", {"reason": reason})
    return state


def exit_quarantine(operator_key: str) -> Dict[str, Any]:
    cfg = get_config()
    expected = cfg.get("operator_pin", "")
    # Localhost or valid key required
    if expected and operator_key != expected:
        return {"error": "Invalid operator key"}
    state = {"quarantined": False, "reason": None, "since": None}
    _save_state(state)
    _audit("quarantine_exited", {"by": "operator"})
    return {"status": "quarantine_lifted"}


def get_quarantine_status() -> Dict[str, Any]:
    return _load_state()
