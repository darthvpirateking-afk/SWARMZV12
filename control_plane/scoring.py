# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
scoring.py â€“ Deterministic action scoring for the Layer-Weaver control plane.

Score = Benefit âˆ’ (Î»_risk * Risk + Î»_coupling * CouplingDamage
                   + Î»_irr * Irreversibility + Î»_uncertainty * Uncertainty)

All deltas are normalised before scoring.  Ties are broken deterministically by
action_id (lexicographic ascending).  If the best score is <= 0, NO_ACTION is
returned.
"""

from __future__ import annotations

import json
import os
from typing import Any

import jsonschema

_DIR = os.path.dirname(os.path.abspath(__file__))

# Load coupling graph and action definitions once
with open(os.path.join(_DIR, "data", "coupling.json")) as _f:
    _COUPLING: list[dict] = json.load(_f)

with open(os.path.join(_DIR, "schemas", "edge.schema.json")) as _f:
    _EDGE_SCHEMA = json.load(_f)

# Validate coupling on import
for edge in _COUPLING:
    jsonschema.validate(instance=edge, schema=_EDGE_SCHEMA)

# Default lambda weights
LAMBDAS: dict[str, float] = {
    "risk": 0.25,
    "coupling": 0.25,
    "irr": 0.25,
    "uncertainty": 0.25,
}


def _coupling_damage(action: dict) -> float:
    """Estimate coupling damage from an action's expected effects."""
    damage = 0.0
    affected_vars = {e["variable"] for e in action.get("expected_effects", [])}
    for edge in _COUPLING:
        if edge["from_variable"] in affected_vars and edge["sign"] == -1:
            damage += edge["strength"] * edge["confidence"]
    return min(damage, 1.0)


# Normalisation divisor: deltas are divided by this value and clamped to [0, 1].
_NORM_SCALE = 100.0


def _benefit(action: dict) -> float:
    """Sum of positive expected deltas (normalised 0-1, clamped)."""
    total = 0.0
    for eff in action.get("expected_effects", []):
        d = eff.get("delta", 0)
        if d > 0:
            total += min(d / _NORM_SCALE, 1.0)
    return min(total, 1.0)


def _risk(action: dict) -> float:
    """Risk is the fraction of expected deltas that are negative."""
    effects = action.get("expected_effects", [])
    if not effects:
        return 0.0
    neg = sum(1 for e in effects if e.get("delta", 0) < 0)
    return neg / len(effects)


def score_action(action: dict, state: dict[str, Any],
                 lambdas: dict[str, float] | None = None) -> float:
    """Return a deterministic score for *action* given current *state*."""
    lam = lambdas or LAMBDAS
    b = _benefit(action)
    r = _risk(action)
    cd = _coupling_damage(action)
    irr = action.get("irreversibility_cost", 0.0)
    # uncertainty = 1 âˆ’ average confidence across affected variables
    confs: list[float] = []
    for eff in action.get("expected_effects", []):
        sv = state.get(eff["variable"])
        if sv and isinstance(sv, dict):
            confs.append(sv.get("confidence", 0.5))
        else:
            confs.append(0.5)
    unc = 1.0 - (sum(confs) / len(confs)) if confs else 0.5

    return b - (lam["risk"] * r + lam["coupling"] * cd
                + lam["irr"] * irr + lam["uncertainty"] * unc)


def select_best(actions: list[dict], state: dict[str, Any],
                lambdas: dict[str, float] | None = None) -> dict | None:
    """Pick the best action. Returns ``None`` (NO_ACTION) when best score <= 0."""
    scored = []
    for a in actions:
        s = score_action(a, state, lambdas)
        scored.append((s, a["action_id"], a))

    # Deterministic tie-breaking: highest score first, then lexicographic action_id
    scored.sort(key=lambda t: (-t[0], t[1]))

    if not scored or scored[0][0] <= 0:
        return None
    return scored[0][2]

