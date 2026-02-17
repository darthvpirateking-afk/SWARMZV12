# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Bucket B â€” Guardrails & Observables.

Enforceable guardrails translated from "unnameables":
  - Counterfactual Baseline Tracking
  - Decision Pressure Mapping
  - Interference / Coupling Graph
  - Template Half-life / Decay
  - Irreversibility Tagging + Delay Window
  - Cheap Falsification First
  - Negative Capability Map
  - Silence-as-Signal
  - Surprise Detector via Shadow Replay
  - Adversarial Input Stability Check
  - Opportunity Cost Shadow / Regret Tracking
  - Saturation Monitor
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from addons.config_ext import get_config

_GUARDRAILS_DIR = "addons/data/guardrails"


def _dir() -> Path:
    d = Path(_GUARDRAILS_DIR)
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


def _load_json(name: str) -> Dict[str, Any]:
    p = _dir() / f"{name}.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_json(name: str, data: Dict[str, Any]) -> None:
    (_dir() / f"{name}.json").write_text(json.dumps(data, indent=2))


def _append_jsonl(name: str, entry: Dict[str, Any]) -> None:
    p = _dir() / f"{name}.jsonl"
    with open(p, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _load_jsonl(name: str) -> List[Dict[str, Any]]:
    p = _dir() / f"{name}.jsonl"
    if not p.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with open(p) as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries


# â”€â”€ 1. Counterfactual Baseline Tracking â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def record_baseline(mission_id: str, expected_baseline: float, observed: float) -> Dict[str, Any]:
    delta = observed - expected_baseline
    entry = {
        "mission_id": mission_id,
        "expected_baseline": expected_baseline,
        "observed": observed,
        "delta": delta,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _append_jsonl("counterfactual_baselines", entry)
    return entry


def get_baselines(limit: int = 50) -> List[Dict[str, Any]]:
    return _load_jsonl("counterfactual_baselines")[-limit:]


# â”€â”€ 2. Decision Pressure Mapping â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def record_pressure(mission_id: str, hesitation_ms: float, approval_delay_ms: float) -> Dict[str, Any]:
    pressure_score = (hesitation_ms + approval_delay_ms) / 2.0
    entry = {
        "mission_id": mission_id,
        "hesitation_ms": hesitation_ms,
        "approval_delay_ms": approval_delay_ms,
        "pressure_score": pressure_score,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _append_jsonl("decision_pressure", entry)
    return entry


def get_pressure_map(limit: int = 50) -> List[Dict[str, Any]]:
    return _load_jsonl("decision_pressure")[-limit:]


# â”€â”€ 3. Interference / Coupling Graph â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def record_interference(source: str, target: str, effect: float) -> Dict[str, Any]:
    graph = _load_json("coupling_graph")
    edges = graph.setdefault("edges", [])
    edges.append({
        "source": source,
        "target": target,
        "effect": effect,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _save_json("coupling_graph", graph)
    return {"source": source, "target": target, "effect": effect}


def get_coupling_graph() -> Dict[str, Any]:
    return _load_json("coupling_graph")


# â”€â”€ 4. Template Half-life / Decay â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def record_template_run(template_id: str, roi: float) -> Dict[str, Any]:
    entry = {
        "template_id": template_id,
        "roi": roi,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _append_jsonl("template_decay", entry)
    return entry


def compute_half_life(template_id: str) -> Dict[str, Any]:
    entries = [e for e in _load_jsonl("template_decay") if e.get("template_id") == template_id]
    if len(entries) < 2:
        return {"template_id": template_id, "half_life_runs": None, "status": "insufficient_data"}
    rois = [e["roi"] for e in entries]
    peak = max(rois)
    half = peak / 2.0
    runs_to_half = None
    for i, r in enumerate(rois):
        if r <= half and i > rois.index(peak):
            runs_to_half = i - rois.index(peak)
            break
    return {"template_id": template_id, "half_life_runs": runs_to_half, "peak_roi": peak}


# â”€â”€ 5. Irreversibility Tagging + Delay Window â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def tag_irreversibility(action_id: str, blast_radius: str, delay_seconds: int = 0) -> Dict[str, Any]:
    cfg = get_config()
    default_delay = cfg.get("irreversibility_delay_seconds", 30)
    if blast_radius == "high" and delay_seconds < default_delay:
        delay_seconds = default_delay
    entry = {
        "action_id": action_id,
        "blast_radius": blast_radius,
        "delay_seconds": delay_seconds,
        "tagged_at": datetime.now(timezone.utc).isoformat(),
    }
    _append_jsonl("irreversibility_tags", entry)
    if blast_radius == "high":
        _audit("irreversibility_high", entry)
    return entry


def get_irreversibility_tags(limit: int = 50) -> List[Dict[str, Any]]:
    return _load_jsonl("irreversibility_tags")[-limit:]


# â”€â”€ 6. Cheap Falsification First â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def submit_falsification(hypothesis: str, test_cost: float, disproved: bool) -> Dict[str, Any]:
    entry = {
        "hypothesis": hypothesis,
        "test_cost": test_cost,
        "disproved": disproved,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _append_jsonl("falsifications", entry)
    return entry


def get_falsifications(limit: int = 50) -> List[Dict[str, Any]]:
    return _load_jsonl("falsifications")[-limit:]


# â”€â”€ 7. Negative Capability Map â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def record_negative_zone(zone: str, failure_count: int) -> Dict[str, Any]:
    data = _load_json("negative_capability")
    zones = data.setdefault("zones", {})
    zones[zone] = {
        "failure_count": failure_count,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_json("negative_capability", data)
    return {"zone": zone, "failure_count": failure_count}


def get_negative_zones() -> Dict[str, Any]:
    return _load_json("negative_capability").get("zones", {})


def should_avoid(zone: str, threshold: int = 3) -> bool:
    zones = get_negative_zones()
    return zones.get(zone, {}).get("failure_count", 0) >= threshold


# â”€â”€ 8. Silence-as-Signal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def record_silence(period: str, metric: str) -> Dict[str, Any]:
    entry = {
        "period": period,
        "metric": metric,
        "signal": "nothing_happened",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _append_jsonl("silence_signals", entry)
    return entry


def get_silence_signals(limit: int = 50) -> List[Dict[str, Any]]:
    return _load_jsonl("silence_signals")[-limit:]


# â”€â”€ 9. Surprise Detector via Shadow Replay â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def shadow_replay(run_id: str, expected_hash: str, actual_hash: str) -> Dict[str, Any]:
    divergence = expected_hash != actual_hash
    entry = {
        "run_id": run_id,
        "expected_hash": expected_hash,
        "actual_hash": actual_hash,
        "divergent": divergence,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _append_jsonl("shadow_replays", entry)
    if divergence:
        _audit("shadow_divergence", entry)
    return entry


def get_shadow_replays(limit: int = 50) -> List[Dict[str, Any]]:
    return _load_jsonl("shadow_replays")[-limit:]


# â”€â”€ 10. Adversarial Input Stability Check â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def stability_check(input_id: str, original_output: Any, perturbed_outputs: List[Any]) -> Dict[str, Any]:
    if not perturbed_outputs:
        return {"input_id": input_id, "stable": True, "variance": 0.0}

    orig_str = json.dumps(original_output, sort_keys=True)
    mismatches = sum(1 for po in perturbed_outputs if json.dumps(po, sort_keys=True) != orig_str)
    variance = mismatches / len(perturbed_outputs)

    entry = {
        "input_id": input_id,
        "stable": variance < 0.3,
        "variance": variance,
        "n_perturbations": len(perturbed_outputs),
        "mismatches": mismatches,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _append_jsonl("stability_checks", entry)
    if not entry["stable"]:
        _audit("input_brittle", entry)
    return entry


def get_stability_checks(limit: int = 50) -> List[Dict[str, Any]]:
    return _load_jsonl("stability_checks")[-limit:]


# â”€â”€ 11. Opportunity Cost Shadow / Regret Tracking â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def record_regret(chosen: str, alternatives: List[str], estimated_regret: float) -> Dict[str, Any]:
    entry = {
        "chosen": chosen,
        "alternatives": alternatives,
        "estimated_regret": estimated_regret,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _append_jsonl("regret_tracking", entry)
    return entry


def get_regret_log(limit: int = 50) -> List[Dict[str, Any]]:
    return _load_jsonl("regret_tracking")[-limit:]


# â”€â”€ 12. Saturation Monitor â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def record_returns(metric: str, value: float) -> Dict[str, Any]:
    entry = {
        "metric": metric,
        "value": value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _append_jsonl("saturation", entry)
    return entry


def detect_saturation(metric: str, window: int = 10) -> Dict[str, Any]:
    entries = [e for e in _load_jsonl("saturation") if e.get("metric") == metric]
    if len(entries) < window:
        return {"metric": metric, "saturated": False, "status": "insufficient_data"}
    recent = [e["value"] for e in entries[-window:]]
    if len(recent) < 2:
        return {"metric": metric, "saturated": False}
    # Simple: check if slope of recent values is near zero
    n = len(recent)
    x_mean = (n - 1) / 2.0
    y_mean = sum(recent) / n
    num = sum((i - x_mean) * (recent[i] - y_mean) for i in range(n))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / den if den > 1e-9 else 0.0
    saturated = abs(slope) < 0.01
    return {
        "metric": metric,
        "saturated": saturated,
        "slope": round(slope, 6),
        "window": window,
        "last_value": recent[-1],
    }

