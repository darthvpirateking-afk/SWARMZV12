# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Entropy Budget â€” complexity points.

Weekly cap on complexity additions.  New modules must "pay" complexity
points.  Over-cap triggers merge/delete tasks.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict

from addons.config_ext import get_config

_ENTROPY_FILE = "addons/data/entropy_budget.json"


def _load() -> Dict[str, Any]:
    p = Path(_ENTROPY_FILE)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    cfg = get_config()
    return {
        "weekly_cap": cfg.get("entropy_weekly_cap", 50),
        "current_week_start": _week_start().isoformat(),
        "spent": 0,
        "entries": [],
    }


def _save(state: Dict[str, Any]) -> None:
    p = Path(_ENTROPY_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2))


def _week_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now - timedelta(days=now.weekday())


def _maybe_reset(state: Dict[str, Any]) -> Dict[str, Any]:
    ws = _week_start().isoformat()
    if state.get("current_week_start") != ws:
        state["current_week_start"] = ws
        state["spent"] = 0
        state["entries"] = []
    return state


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


def get_entropy_budget() -> Dict[str, Any]:
    state = _maybe_reset(_load())
    _save(state)
    return {
        "weekly_cap": state["weekly_cap"],
        "spent": state["spent"],
        "remaining": state["weekly_cap"] - state["spent"],
        "week_start": state["current_week_start"],
        "over_cap": state["spent"] > state["weekly_cap"],
    }


def spend_entropy(points: int, label: str) -> Dict[str, Any]:
    state = _maybe_reset(_load())
    remaining = state["weekly_cap"] - state["spent"]
    if points > remaining:
        _audit("entropy_over_cap", {"points": points, "label": label, "remaining": remaining})
        return {
            "error": "Entropy over-cap â€” trigger merge/delete tasks before adding complexity",
            "remaining": remaining,
        }
    state["spent"] += points
    state["entries"].append({
        "points": points,
        "label": label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _save(state)
    _audit("entropy_spent", {"points": points, "label": label, "total": state["spent"]})
    return {"status": "ok", "spent": state["spent"], "remaining": state["weekly_cap"] - state["spent"]}

