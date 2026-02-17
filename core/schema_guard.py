# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
core/schema_guard.py â€” Lightweight schema validation for SWARMZ JSON/JSONL.

No external deps.  Checks required keys and optional type constraints.
Returns (valid: bool, errors: list[str]).
"""

from typing import Any, Dict, List, Optional, Tuple


# â”€â”€ Simple schema definition â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# A schema is a dict of   field_name â†’ expected_type | None
#   None means "any type, just check presence"
#   "str", "int", "float", "bool", "list", "dict" map to Python types

_TYPE_MAP = {
    "str": str,
    "int": int,
    "float": (int, float),
    "bool": bool,
    "list": list,
    "dict": dict,
}


def validate(obj: Dict[str, Any],
             required: Dict[str, Optional[str]],
             optional: Optional[Dict[str, Optional[str]]] = None) -> Tuple[bool, List[str]]:
    """Validate *obj* against a requiredâ€‘fields schema.

    Parameters
    ----------
    obj:       The dict to validate.
    required:  ``{"field": "str"|"int"|"float"|"bool"|"list"|"dict"|None}``.
    optional:  Same format; checked only if the key is present.

    Returns
    -------
    (True, [])  if valid, otherwise (False, [error_message, ...]).
    """
    errors: List[str] = []
    if not isinstance(obj, dict):
        return False, ["root object is not a dict"]

    for key, expected_type in required.items():
        if key not in obj:
            errors.append(f"missing required field '{key}'")
            continue
        if expected_type is not None:
            pytype = _TYPE_MAP.get(expected_type)
            if pytype and not isinstance(obj[key], pytype):
                errors.append(f"field '{key}' expected {expected_type}, got {type(obj[key]).__name__}")

    if optional:
        for key, expected_type in optional.items():
            if key in obj and expected_type is not None:
                pytype = _TYPE_MAP.get(expected_type)
                if pytype and not isinstance(obj[key], pytype):
                    errors.append(f"optional field '{key}' expected {expected_type}, got {type(obj[key]).__name__}")

    return (len(errors) == 0, errors)


# â”€â”€ Preâ€‘defined schemas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

MISSION_SCHEMA = {
    "mission_id": "str",
    "status": "str",
}

PERF_RECORD_SCHEMA = {
    "timestamp": "str",
    "mission_id": "str",
    "runtime_ms": "int",
    "success_bool": "bool",
}

EVOLUTION_RECORD_SCHEMA = {
    "timestamp": "str",
    "mission_type": "str",
    "inputs_hash": "str",
    "strategy_used": "str",
    "record_hash": "str",
}

COMPANION_MEMORY_SCHEMA = {
    "sessionId": "str",
    "summary": "str",
    "mission_outcomes": "list",
}

PHASE_HISTORY_SCHEMA = {
    "timestamp": "str",
    "context_cluster_id": "str",
}

