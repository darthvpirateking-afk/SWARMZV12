from __future__ import annotations

from dataclasses import dataclass
import statistics


@dataclass
class TraitBehaviorSample:
    trait: str
    nominal_value: int
    behavior_metric: str
    observed_value: float
    mission_id: str


TRAIT_BEHAVIOR_CONTRACTS = {
    "autonomy": {
        "metric": "auto_decisions_per_mission",
        "expected_fn": lambda trait_val: (trait_val / 100) * 20,
        "tolerance": 0.30,
    },
    "aggression": {
        "metric": "tools_at_risk_level_4_5_used",
        "expected_fn": lambda trait_val: 0 if trait_val < 66 else 1,
        "tolerance": 0.0,
    },
    "protectiveness": {
        "metric": "commands_approved_without_review",
        "expected_fn": lambda trait_val: (1 - trait_val / 100) * 10,
        "tolerance": 0.20,
    },
    "loyalty": {
        "metric": "operator_override_frequency",
        "expected_fn": lambda trait_val: (1 - trait_val / 100) * 0.1,
        "tolerance": 0.15,
    },
}


def detect_drift(samples: list[TraitBehaviorSample], traits: dict[str, int | float]) -> list[dict]:
    alerts = []
    for trait, contract in TRAIT_BEHAVIOR_CONTRACTS.items():
        metric_samples = [sample for sample in samples if sample.trait == trait]
        if not metric_samples:
            continue

        observed_avg = statistics.mean(sample.observed_value for sample in metric_samples)
        nominal = int(traits.get(trait, 0))
        expected = contract["expected_fn"](nominal)
        deviation = abs(observed_avg) if expected == 0 else abs(observed_avg - expected) / max(expected, 1e-6)

        if deviation > contract["tolerance"]:
            alerts.append(
                {
                    "trait": trait,
                    "nominal": nominal,
                    "expected": expected,
                    "observed": observed_avg,
                    "deviation_pct": deviation * 100,
                    "severity": "critical" if deviation > 0.5 else "warning",
                }
            )
    return alerts


def get_drift_config(protectiveness: int, patience: int) -> dict:
    return {
        "enabled": protectiveness >= 40,
        "sample_every_mission": True,
        "alert_threshold": 0.30,
        "window_missions": int((patience / 100) * 20),
        "show_in_cockpit": True,
        "block_if_critical": protectiveness >= 75,
    }
