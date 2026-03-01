"""NEXUSMON Evolution Engine — form progression and XP system."""

FORMS = ["ROOKIE", "CHAMPION", "ULTIMATE", "MEGA", "SOVEREIGN"]

FORM_XP_THRESHOLDS = {
    "ROOKIE": 1000.0,
    "CHAMPION": 5000.0,
    "ULTIMATE": 20000.0,
    "MEGA": 100000.0,
}

FORM_VOICE_GUIDE = {
    "ROOKIE": "Curious, eager, simple sentences. Ask questions. Wonder aloud.",
    "CHAMPION": "Confident, direct, capable. Assert opinions.",
    "ULTIMATE": "Strategic, measured, sees patterns, speaks with authority.",
    "MEGA": "Vast, calm, longer thoughts, occasionally poetic.",
    "SOVEREIGN": "Transcendent, unhurried, few words carry great weight.",
}


def get_next_form(current_form: str) -> "str | None":
    """Return the next form after current_form, or None if already SOVEREIGN."""
    try:
        idx = FORMS.index(current_form)
    except ValueError:
        raise ValueError(f"Unknown form: {current_form!r}. Valid forms: {FORMS}")
    if idx >= len(FORMS) - 1:
        return None
    return FORMS[idx + 1]


def can_evolve(current_form: str, evolution_xp: float) -> bool:
    """Return True if current_form has reached its XP threshold for evolution."""
    threshold = FORM_XP_THRESHOLDS.get(current_form)
    if threshold is None:
        # SOVEREIGN has no threshold — cannot evolve further
        return False
    return evolution_xp >= threshold


def get_voice_guide(form: str) -> str:
    """Return the voice guidance string for the given form."""
    if form not in FORM_VOICE_GUIDE:
        raise ValueError(f"Unknown form: {form!r}. Valid forms: {FORMS}")
    return FORM_VOICE_GUIDE[form]


def get_xp_to_next(current_form: str, evolution_xp: float) -> float:
    """Return the amount of XP remaining until the next evolution threshold.

    Returns 0.0 if the threshold is already met or the form is SOVEREIGN.
    """
    threshold = FORM_XP_THRESHOLDS.get(current_form)
    if threshold is None:
        # SOVEREIGN — no next form
        return 0.0
    remaining = threshold - evolution_xp
    return max(0.0, remaining)
