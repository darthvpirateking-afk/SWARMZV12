from typing import Any, Dict, List


def schedule_next_mission(
    mission_queue: List[Dict[str, Any]],
    entropy: float,
    drift: float,
) -> Dict[str, Any]:
    """Select next mission only when stability thresholds are safe.

    Refuses scheduling when entropy > 0.4 or drift > 0.3.
    """
    if entropy > 0.4 or drift > 0.3:
        return {
            "scheduled": False,
            "reason": "throttled_by_stability_threshold",
            "entropy": entropy,
            "drift": drift,
        }

    if not mission_queue:
        return {"scheduled": False, "reason": "queue_empty"}

    next_mission = mission_queue[0]
    return {
        "scheduled": True,
        "mission": next_mission,
        "reason": "ok",
        "entropy": entropy,
        "drift": drift,
    }
