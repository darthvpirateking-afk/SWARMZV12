"""
scoring.py – Deterministic action scoring with global lambdas.

Score = Benefit − (λ_risk * Risk + λ_coupling * CouplingDamage
                 + λ_irr * Irreversibility + λ_uncertainty * Uncertainty)

Tie-breakers (in order for equal Score):
  1) higher min-confidence of expected_effects
  2) lower irreversibility_cost
  3) smaller numeric magnitude (if parseable)
  4) lexical by action id

If best_score <= 0 OR no eligible actions → NO_ACTION.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .expression_eval import evaluate_comparison


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _normalize_delta(delta: float, target_range: float) -> float:
    if target_range == 0:
        return 0.0
    return _clamp(delta / target_range, -1.0, 1.0)


def _magnitude_value(action: dict) -> float:
    """Try to extract numeric magnitude for tie-breaking."""
    try:
        return abs(float(action["magnitude"]["value"]))
    except (KeyError, TypeError, ValueError):
        return float("inf")


def check_constraints(action: dict, state_values: Dict[str, Any]) -> bool:
    """Return True if all action constraints are satisfied by current state."""
    for c in action.get("constraints", []):
        var = c["variable"]
        if var not in state_values:
            return False  # unknown variable → constraint fails
        if not evaluate_comparison(c["op"], state_values[var], c["value"]):
            return False
    return True


def check_guardrails(guardrails: list, state_values: Dict[str, Any]) -> bool:
    """Return True if all guardrails are satisfied."""
    for g in guardrails:
        var = g["variable"]
        if var not in state_values:
            return False
        if not evaluate_comparison(g["op"], state_values[var], g["value"]):
            return False
    return True


def compute_benefit(
    action: dict, active_objectives: List[dict], target_ranges: Dict[str, float]
) -> float:
    """Compute normalized Benefit from active objective weights."""
    total = 0.0
    for obj in active_objectives:
        weights = obj.get("weights", {})
        for eff in action.get("expected_effects", []):
            var = eff["variable"]
            w = weights.get(var, 0.0)
            if w <= 0:
                continue
            tr = target_ranges.get(var, 1.0)
            nd = _normalize_delta(eff["delta"], tr)
            if nd > 0:
                total += w * nd
    return _clamp(total, 0.0, 1.0)


def compute_risk(action: dict) -> float:
    """Risk = 1 − min_confidence(expected_effects)."""
    confs = [e.get("confidence", 0.5) for e in action.get("expected_effects", [])]
    if not confs:
        return 1.0
    return 1.0 - min(confs)


def compute_coupling_damage(
    action: dict, edges: List[dict], target_ranges: Dict[str, float], target_vars: set
) -> float:
    """Propagate expected effects through 1-2 hops of coupling edges.

    Only penalize negative impacts on non-target variables.
    """
    # Build adjacency: from_var → list of edges
    adj: Dict[str, List[dict]] = {}
    for e in edges:
        adj.setdefault(e["from_variable"], []).append(e)

    damage = 0.0
    # Track propagated deltas: variable → delta
    hop1: Dict[str, float] = {}

    for eff in action.get("expected_effects", []):
        var = eff["variable"]
        delta = eff["delta"]
        for edge in adj.get(var, []):
            to_var = edge["to_variable"]
            prop = delta * edge["sign"] * edge["strength"] * edge["confidence"]
            hop1[to_var] = hop1.get(to_var, 0.0) + prop

    # Hop 2
    hop2: Dict[str, float] = {}
    for var, delta in hop1.items():
        for edge in adj.get(var, []):
            to_var = edge["to_variable"]
            prop = delta * edge["sign"] * edge["strength"] * edge["confidence"]
            hop2[to_var] = hop2.get(to_var, 0.0) + prop

    # Merge hops
    all_impacts: Dict[str, float] = {}
    for var, d in hop1.items():
        all_impacts[var] = all_impacts.get(var, 0.0) + d
    for var, d in hop2.items():
        all_impacts[var] = all_impacts.get(var, 0.0) + d

    # Penalize negative impacts on non-target variables
    for var, d in all_impacts.items():
        if var in target_vars:
            continue  # we don't penalize target variable impacts
        tr = target_ranges.get(var, 1.0)
        nd = _normalize_delta(d, tr)
        if nd < 0:
            damage += abs(nd)

    return _clamp(damage, 0.0, 1.0)


def compute_uncertainty(action: dict, edges: List[dict]) -> float:
    """Uncertainty = 1 − min(min_conf_effects, min_edge_conf_traversed)."""
    effect_confs = [
        e.get("confidence", 0.5) for e in action.get("expected_effects", [])
    ]
    if not effect_confs:
        return 1.0

    # Find edge confidences traversed by this action's effects
    affected_vars = {e["variable"] for e in action.get("expected_effects", [])}
    edge_confs = [e["confidence"] for e in edges if e["from_variable"] in affected_vars]

    min_eff = min(effect_confs)
    min_edge = min(edge_confs) if edge_confs else 1.0
    return 1.0 - min(min_eff, min_edge)


def score_action(
    action: dict,
    active_objectives: List[dict],
    lambdas: Dict[str, float],
    target_ranges: Dict[str, float],
    edges: List[dict],
    state_values: Dict[str, Any],
) -> Optional[Tuple[float, dict]]:
    """Score a single action. Returns (score, breakdown) or None if ineligible."""
    # Check hard constraints
    if not check_constraints(action, state_values):
        return None

    # Check guardrails of all active objectives
    for obj in active_objectives:
        if not check_guardrails(obj.get("guardrails", []), state_values):
            return None

    # Target variables = union of all effect variables
    target_vars = {e["variable"] for e in action.get("expected_effects", [])}

    benefit = compute_benefit(action, active_objectives, target_ranges)
    risk = compute_risk(action)
    coupling = compute_coupling_damage(action, edges, target_ranges, target_vars)
    uncertainty = compute_uncertainty(action, edges)
    irreversibility = action.get("irreversibility_cost", 0.0)

    lr = lambdas.get("risk", 0.25)
    lc = lambdas.get("coupling_damage", 0.20)
    li = lambdas.get("irreversibility", 0.15)
    lu = lambdas.get("uncertainty", 0.15)

    penalty = lr * risk + lc * coupling + li * irreversibility + lu * uncertainty
    score = benefit - penalty

    breakdown = {
        "benefit": round(benefit, 6),
        "risk": round(risk, 6),
        "coupling_damage": round(coupling, 6),
        "irreversibility": round(irreversibility, 6),
        "uncertainty": round(uncertainty, 6),
        "penalty": round(penalty, 6),
        "score": round(score, 6),
    }

    return (score, breakdown)


def select_best_action(
    actions: List[dict],
    active_objectives: List[dict],
    lambdas: Dict[str, float],
    target_ranges: Dict[str, float],
    edges: List[dict],
    state_values: Dict[str, Any],
) -> Tuple[Optional[dict], Optional[dict]]:
    """Score all actions and return the best one.

    Returns (best_action, breakdown) or (None, None) if all suppressed.
    """
    candidates: List[Tuple[float, dict, dict]] = []

    for action in actions:
        result = score_action(
            action, active_objectives, lambdas, target_ranges, edges, state_values
        )
        if result is not None:
            score, breakdown = result
            candidates.append((score, action, breakdown))

    if not candidates:
        return None, None

    # Sort: highest score first, then tie-breakers
    def sort_key(item):
        score, action, _bd = item
        min_conf = min(
            (e.get("confidence", 0.5) for e in action.get("expected_effects", [])),
            default=0,
        )
        return (
            -score,
            -min_conf,
            action.get("irreversibility_cost", 0.0),
            _magnitude_value(action),
            action.get("id", ""),
        )

    candidates.sort(key=sort_key)
    best_score, best_action, best_bd = candidates[0]

    if best_score <= 0:
        return None, None

    return best_action, best_bd
