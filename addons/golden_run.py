"""
Golden-Run / Determinism Harness.

Record decision inputs + state hash.  Replay must match outputs or flag nondeterminism.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from addons.config_ext import get_config

_GOLDEN_FILE = "addons/data/golden_runs.jsonl"


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


def _state_hash(state: Any) -> str:
    blob = json.dumps(state, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def record_golden_run(
    run_id: str,
    inputs: Dict[str, Any],
    state_before: Any,
    outputs: Dict[str, Any],
    state_after: Any,
) -> Dict[str, Any]:
    p = Path(_GOLDEN_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "run_id": run_id,
        "inputs": inputs,
        "state_hash_before": _state_hash(state_before),
        "outputs": outputs,
        "state_hash_after": _state_hash(state_after),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(p, "a") as f:
        f.write(json.dumps(entry) + "\n")
    _audit("golden_run_recorded", {"run_id": run_id})
    return entry


def replay_and_verify(
    run_id: str,
    replay_outputs: Dict[str, Any],
    replay_state_after: Any,
) -> Dict[str, Any]:
    """Compare replay outputs against the golden record."""
    entries = _load_runs()
    golden = None
    for e in entries:
        if e.get("run_id") == run_id:
            golden = e
            break
    if golden is None:
        return {"error": "Golden run not found"}

    replay_hash = _state_hash(replay_state_after)
    outputs_match = json.dumps(golden["outputs"], sort_keys=True) == json.dumps(replay_outputs, sort_keys=True)
    state_match = golden["state_hash_after"] == replay_hash

    result = {
        "run_id": run_id,
        "deterministic": outputs_match and state_match,
        "outputs_match": outputs_match,
        "state_match": state_match,
        "golden_state_hash": golden["state_hash_after"],
        "replay_state_hash": replay_hash,
    }

    if not result["deterministic"]:
        _audit("nondeterminism_detected", result)

    return result


def _load_runs() -> List[Dict[str, Any]]:
    p = Path(_GOLDEN_FILE)
    if not p.exists():
        return []
    runs: List[Dict[str, Any]] = []
    with open(p) as f:
        for line in f:
            if line.strip():
                runs.append(json.loads(line))
    return runs


def list_golden_runs() -> List[Dict[str, Any]]:
    return _load_runs()
