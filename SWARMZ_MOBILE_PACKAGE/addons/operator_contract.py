# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Operator Contract Files â€” human-readable config defining:
  allowed actions, forbidden domains, approval rules, envelopes.

Versioned + requires seal.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from addons.config_ext import get_config

_DEFAULT_CONTRACT = {
    "version": 1,
    "sealed": False,
    "allowed_actions": [
        "create_mission",
        "run_mission",
        "list_missions",
        "export_backup",
    ],
    "forbidden_domains": [],
    "approval_rules": {
        "require_approval_above_cost": 100.0,
        "require_approval_categories": ["sanctuary"],
    },
    "envelopes": {
        "max_concurrent_missions": 3,
        "max_daily_spend": 1000.0,
    },
}


def _contracts_dir() -> Path:
    cfg = get_config()
    d = Path(cfg.get("contracts_dir", "addons/data/contracts"))
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


def get_active_contract() -> Dict[str, Any]:
    p = _contracts_dir() / "active_contract.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_DEFAULT_CONTRACT)


def save_contract(contract: Dict[str, Any]) -> Dict[str, Any]:
    contract["sealed"] = False
    contract["updated_at"] = datetime.now(timezone.utc).isoformat()
    p = _contracts_dir() / "active_contract.json"
    p.write_text(json.dumps(contract, indent=2))
    _audit("contract_updated", {"version": contract.get("version")})
    return contract


def seal_contract(operator_key: str) -> Dict[str, Any]:
    cfg = get_config()
    expected = cfg.get("operator_pin", "")
    if expected and operator_key != expected:
        return {"error": "Invalid operator key"}
    contract = get_active_contract()
    contract["sealed"] = True
    contract["sealed_at"] = datetime.now(timezone.utc).isoformat()
    p = _contracts_dir() / "active_contract.json"
    p.write_text(json.dumps(contract, indent=2))
    _audit("contract_sealed", {"version": contract.get("version")})
    return contract


def validate_action(action: str) -> Dict[str, Any]:
    contract = get_active_contract()
    allowed = contract.get("allowed_actions", [])
    forbidden = contract.get("forbidden_domains", [])
    if allowed and action not in allowed:
        return {"allowed": False, "reason": f"Action '{action}' not in allowed list"}
    for domain in forbidden:
        if domain in action:
            return {
                "allowed": False,
                "reason": f"Action touches forbidden domain '{domain}'",
            }
    return {"allowed": True}
