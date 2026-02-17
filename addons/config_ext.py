# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Extended configuration loader for SWARMZ addons.

Reads from config.json + environment variables.  Never overwrites existing keys.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

_DEFAULTS: Dict[str, Any] = {
    "schema_version": 1,
    "operator_pin": "",
    "encryption_key": "",
    "rate_limit_per_minute": 120,
    "budget_hard_cap": 10000.0,
    "entropy_weekly_cap": 50,
    "quarantine_on_governance_failure": True,
    "drift_threshold": 0.25,
    "irreversibility_delay_seconds": 30,
    "backup_dir": "addons/data/backups",
    "memory_dir": "addons/data/memory",
    "contracts_dir": "addons/data/contracts",
    "packs_dir": "addons/data/packs",
    "approval_queue_file": "addons/data/approval_queue.jsonl",
    "audit_file": "data/audit.jsonl",
    "lan_auth_enabled": True,
    # Infra orchestrator feature flags (all opt-in)
    "infra_orchestrator_enabled": False,
    "infra_security_enabled": False,
    "infra_billing_enabled": False,
    "infra_blockchain_enabled": False,
}

_ENV_PREFIX = "SWARMZ_"


def load_addon_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Return merged config: file defaults â†’ config.json 'addons' section â†’ env vars."""
    cfg: Dict[str, Any] = dict(_DEFAULTS)

    # Layer 1: config.json  (addons section only)
    p = Path(config_path)
    if p.exists():
        try:
            with open(p) as f:
                data = json.load(f)
            if "addons" in data and isinstance(data["addons"], dict):
                cfg.update(data["addons"])
        except (json.JSONDecodeError, OSError):
            pass

    # Layer 2: environment overrides
    for key in list(_DEFAULTS):
        env_key = _ENV_PREFIX + key.upper()
        val = os.environ.get(env_key)
        if val is not None:
            # coerce type to match default
            default = _DEFAULTS[key]
            if isinstance(default, bool):
                cfg[key] = val.lower() in ("1", "true", "yes")
            elif isinstance(default, int):
                cfg[key] = int(val)
            elif isinstance(default, float):
                cfg[key] = float(val)
            else:
                cfg[key] = val

    return cfg


# Singleton
_cached: Dict[str, Any] | None = None


def get_config() -> Dict[str, Any]:
    global _cached
    if _cached is None:
        _cached = load_addon_config()
    return _cached


def reload_config() -> Dict[str, Any]:
    global _cached
    _cached = load_addon_config()
    return _cached

