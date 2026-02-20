# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Budget Envelope + Burn Simulator.

Hard caps on time/attention/capital.  Simulates worst-case burn
pre-execution and blocks missions that would breach the envelope.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from addons.config_ext import get_config

_BUDGET_FILE = "addons/data/budget_state.json"


def _load() -> Dict[str, Any]:
    p = Path(_BUDGET_FILE)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    cfg = get_config()
    return {
        "hard_cap": cfg.get("budget_hard_cap", 10000.0),
        "spent": 0.0,
        "reserved": 0.0,
        "history": [],
    }


def _save(state: Dict[str, Any]) -> None:
    p = Path(_BUDGET_FILE)
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


def get_budget() -> Dict[str, Any]:
    return _load()


def simulate_burn(cost: float) -> Dict[str, Any]:
    """Simulate a burn and report whether it would breach the cap."""
    state = _load()
    remaining = state["hard_cap"] - state["spent"] - state["reserved"]
    would_breach = cost > remaining
    return {
        "cost": cost,
        "remaining_before": remaining,
        "remaining_after": remaining - cost if not would_breach else remaining,
        "would_breach": would_breach,
    }


def spend(amount: float, label: str) -> Dict[str, Any]:
    """Record a spend.  Blocks if it would breach the hard cap."""
    state = _load()
    remaining = state["hard_cap"] - state["spent"] - state["reserved"]
    if amount > remaining:
        _audit("budget_breach_blocked", {"amount": amount, "remaining": remaining, "label": label})
        return {"error": "Budget breach â€” spend blocked", "remaining": remaining}
    state["spent"] += amount
    state["history"].append({
        "amount": amount,
        "label": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _save(state)
    _audit("budget_spent", {"amount": amount, "label": label, "total_spent": state["spent"]})
    return {"status": "ok", "total_spent": state["spent"], "remaining": state["hard_cap"] - state["spent"] - state["reserved"]}


def reserve(amount: float, label: str) -> Dict[str, Any]:
    state = _load()
    remaining = state["hard_cap"] - state["spent"] - state["reserved"]
    if amount > remaining:
        return {"error": "Budget breach â€” reserve blocked", "remaining": remaining}
    state["reserved"] += amount
    _save(state)
    return {"status": "reserved", "reserved": state["reserved"]}


def reset_budget(hard_cap: Optional[float] = None) -> Dict[str, Any]:
    cfg = get_config()
    state = {
        "hard_cap": hard_cap or cfg.get("budget_hard_cap", 10000.0),
        "spent": 0.0,
        "reserved": 0.0,
        "history": [],
    }
    _save(state)
    _audit("budget_reset", {"hard_cap": state["hard_cap"]})
    return state

