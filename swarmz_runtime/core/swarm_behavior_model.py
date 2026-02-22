from .persona_layer import SwarmTier


class SwarmBehaviorModel:
    """
    SwarmBehaviorModel
    ------------------
    - Maps swarm tier to pacing + intensity.
    - Represents parallelism level, not emotion or autonomy.
    """

    _MODEL = {
        SwarmTier.T0: {
            "pacing": "slow",
            "intensity": "low",
        },
        SwarmTier.T1: {
            "pacing": "steady",
            "intensity": "low-medium",
        },
        SwarmTier.T2: {
            "pacing": "normal",
            "intensity": "medium",
        },
        SwarmTier.T3: {
            "pacing": "fast",
            "intensity": "medium-high",
        },
        SwarmTier.T4: {
            "pacing": "very-fast",
            "intensity": "high",
        },
        SwarmTier.T5: {
            "pacing": "burst",
            "intensity": "max",
        },
    }

    def get_style(self, tier: SwarmTier) -> dict:
        return self._MODEL[tier]
