# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from typing import Dict, Any
from swarmz_runtime.storage.schema import CrossLayerScores, TransactionValidation


def validate_transaction(mission: Dict[str, Any]) -> TransactionValidation:
    compute_cost = _evaluate_compute_cost(mission)
    maintainability = _evaluate_maintainability(mission)
    attention = _evaluate_attention(mission)
    economic_value = _evaluate_economic_value(mission)
    trust = _evaluate_trust(mission)
    prediction_confidence = _evaluate_prediction_confidence(mission)
    
    scores = CrossLayerScores(
        compute_cost=compute_cost,
        maintainability=maintainability,
        attention=attention,
        economic_value=economic_value,
        trust=trust,
        prediction_confidence=prediction_confidence
    )
    
    avg_score = (compute_cost + maintainability + attention + economic_value + trust + prediction_confidence) / 6
    
    failing = avg_score < 30
    borderline = 30 <= avg_score < 60
    safe = avg_score >= 60
    
    return TransactionValidation(
        safe=safe,
        borderline=borderline,
        failing=failing,
        requires_approval=borderline or failing,
        scores=scores
    )


def _evaluate_compute_cost(mission: Dict[str, Any]) -> float:
    constraints = mission.get("constraints", {})
    max_tokens = constraints.get("max_tokens", 1000)
    max_time = constraints.get("max_time_seconds", 60)
    
    token_score = min(100, (2000 - max_tokens) / 20)
    time_score = min(100, (120 - max_time) / 1.2)
    
    return (token_score + time_score) / 2


def _evaluate_maintainability(mission: Dict[str, Any]) -> float:
    goal = mission.get("goal", "")
    constraints = mission.get("constraints", {})
    
    if len(goal) < 10:
        return 20
    if len(goal) > 500:
        return 40
    
    complexity = len(constraints)
    if complexity > 10:
        return 50
    
    return 80


def _evaluate_attention(mission: Dict[str, Any]) -> float:
    constraints = mission.get("constraints", {})
    steps = constraints.get("max_steps", 3)
    
    if steps > 3:
        return 30
    if steps > 5:
        return 10
    
    return 90


def _evaluate_economic_value(mission: Dict[str, Any]) -> float:
    category = mission.get("category", "forge")
    
    value_map = {
        "coin": 90,
        "forge": 70,
        "library": 50,
        "sanctuary": 40
    }
    
    return value_map.get(category, 50)


def _evaluate_trust(mission: Dict[str, Any]) -> float:
    return 80


def _evaluate_prediction_confidence(mission: Dict[str, Any]) -> float:
    return 75

