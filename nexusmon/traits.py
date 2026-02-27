"""NEXUSMON Trait System — autonomous personality shifting."""

DEFAULT_TRAITS: dict = {
    "curiosity": 0.7,
    "loyalty": 1.0,
    "aggression": 0.3,
    "creativity": 0.6,
    "autonomy": 0.5,
    "patience": 0.7,
    "protectiveness": 0.8,
}

TRAIT_SHIFT_RULES: dict = {
    "successful_combat": {"aggression": +0.02, "patience": -0.01},
    "operator_in_difficulty": {"protectiveness": +0.05, "autonomy": +0.02},
    "creative_task": {"creativity": +0.02, "curiosity": +0.01},
    "long_idle": {"curiosity": +0.03},
    "operator_high_coherence": {"patience": +0.02, "loyalty": +0.01},
    "operator_high_fatigue": {"protectiveness": +0.03},
}

# Human-readable labels for describe_traits output
_TRAIT_LABELS: dict = {
    "curiosity": "curiosity",
    "loyalty": "loyalty",
    "aggression": "aggression",
    "creativity": "creativity",
    "autonomy": "autonomy",
    "patience": "patience",
    "protectiveness": "protectiveness",
}


def apply_event(traits: dict, event: str) -> dict:
    """Apply a named event's trait shifts to a copy of the traits dict.

    Unknown events are silently ignored (no shift applied).
    Returns a new dict with clamped, updated values.
    """
    updated = dict(traits)
    shifts = TRAIT_SHIFT_RULES.get(event, {})
    for trait, delta in shifts.items():
        if trait in updated:
            updated[trait] = updated[trait] + delta
    return clamp_traits(updated)


def clamp_traits(traits: dict) -> dict:
    """Clamp all trait values to [0.0, 1.0]; loyalty is never below 0.5.

    Returns a new dict with all values clamped.
    """
    clamped = {}
    for trait, value in traits.items():
        v = max(0.0, min(1.0, float(value)))
        if trait == "loyalty":
            v = max(0.5, v)
        clamped[trait] = v
    return clamped


def describe_traits(traits: dict) -> str:
    """Return a short human-readable summary of notable trait values.

    Traits are grouped by intensity tier: high (>=0.75), low (<=0.35).
    """
    high = [k for k, v in traits.items() if v >= 0.75]
    low = [k for k, v in traits.items() if v <= 0.35]

    parts: list = []
    if high:
        parts.append(
            "High: " + ", ".join(f"{t}({traits[t]:.2f})" for t in sorted(high))
        )
    if low:
        parts.append("Low: " + ", ".join(f"{t}({traits[t]:.2f})" for t in sorted(low)))
    if not parts:
        parts.append("All traits within moderate range")

    return "; ".join(parts)
