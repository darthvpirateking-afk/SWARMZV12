# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Strategy Registry + Kill Switches.

Each strategy/template has scope, deps, kill criteria.
Auto-disable on breach; manual seal to re-enable.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from addons.config_ext import get_config

_REGISTRY_FILE = "addons/data/strategy_registry.json"


def _load() -> Dict[str, Any]:
    p = Path(_REGISTRY_FILE)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"strategies": {}}


def _save(state: Dict[str, Any]) -> None:
    p = Path(_REGISTRY_FILE)
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


def register_strategy(
    strategy_id: str,
    scope: str,
    deps: List[str],
    kill_criteria: Dict[str, Any],
) -> Dict[str, Any]:
    state = _load()
    state["strategies"][strategy_id] = {
        "scope": scope,
        "deps": deps,
        "kill_criteria": kill_criteria,
        "enabled": True,
        "sealed": True,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    _save(state)
    _audit("strategy_registered", {"strategy_id": strategy_id, "scope": scope})
    return state["strategies"][strategy_id]


def kill_strategy(strategy_id: str, reason: str) -> Dict[str, Any]:
    state = _load()
    strat = state["strategies"].get(strategy_id)
    if not strat:
        return {"error": "Strategy not found"}
    strat["enabled"] = False
    strat["sealed"] = False
    strat["killed_at"] = datetime.now(timezone.utc).isoformat()
    strat["kill_reason"] = reason
    _save(state)
    _audit("strategy_killed", {"strategy_id": strategy_id, "reason": reason})
    return strat


def seal_strategy(strategy_id: str, operator_key: str) -> Dict[str, Any]:
    cfg = get_config()
    expected = cfg.get("operator_pin", "")
    if expected and operator_key != expected:
        return {"error": "Invalid operator key"}
    state = _load()
    strat = state["strategies"].get(strategy_id)
    if not strat:
        return {"error": "Strategy not found"}
    strat["enabled"] = True
    strat["sealed"] = True
    strat["sealed_at"] = datetime.now(timezone.utc).isoformat()
    _save(state)
    _audit("strategy_sealed", {"strategy_id": strategy_id})
    return strat


def check_kill_criteria(strategy_id: str, metrics: Dict[str, float]) -> Dict[str, Any]:
    """Check whether any kill criteria are breached.  Auto-disable if so."""
    state = _load()
    strat = state["strategies"].get(strategy_id)
    if not strat:
        return {"error": "Strategy not found"}
    if not strat.get("enabled"):
        return {"status": "already_killed"}

    criteria = strat.get("kill_criteria", {})
    for key, threshold in criteria.items():
        if key in metrics and metrics[key] > threshold:
            kill_strategy(strategy_id, f"Auto-kill: {key}={metrics[key]} > {threshold}")
            return {
                "status": "killed",
                "breach": key,
                "value": metrics[key],
                "threshold": threshold,
            }

    return {"status": "ok"}


def list_strategies() -> Dict[str, Any]:
    return _load().get("strategies", {})
