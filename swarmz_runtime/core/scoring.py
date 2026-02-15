from typing import Dict, Any, List


def calculate_leverage_score(mission: Dict[str, Any]) -> float:
    category = mission.get("category", "forge")
    constraints = mission.get("constraints", {})
    
    base_scores = {
        "coin": 90,
        "forge": 70,
        "library": 60,
        "sanctuary": 50
    }
    
    base_score = base_scores.get(category, 50)
    
    unlock_multiplier = constraints.get("unlocks_future_tasks", 0) * 10
    
    complexity_penalty = len(constraints) * 2
    
    score = base_score + unlock_multiplier - complexity_penalty
    
    return max(0, min(100, score))


def rank_missions(missions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    scored = []
    for mission in missions:
        score = calculate_leverage_score(mission)
        mission["leverage_score"] = score
        scored.append(mission)
    
    return sorted(scored, key=lambda x: x["leverage_score"], reverse=True)


def calculate_expected_value(mission: Dict[str, Any]) -> float:
    category = mission.get("category", "forge")
    
    value_map = {
        "coin": 10.0,
        "forge": 5.0,
        "library": 2.0,
        "sanctuary": 1.0
    }
    
    return value_map.get(category, 0.0)


def should_execute(mission: Dict[str, Any]) -> bool:
    ev = calculate_expected_value(mission)
    is_research = mission.get("category") == "library"
    
    return ev > 0 or is_research
