"""NEXUSMON Mood System — real-time emotional state."""

MOODS = [
    "CALM",
    "FOCUSED",
    "RESTLESS",
    "CHARGED",
    "PROTECTIVE",
    "CURIOUS",
    "DORMANT",
    "ALERT",
    "TRIUMPHANT",
    "CONTEMPLATIVE",
]

_MOOD_DESCRIPTIONS: dict = {
    "CALM": "Settled and steady; responds thoughtfully without urgency.",
    "FOCUSED": "Locked onto active work; minimal distraction, high task efficiency.",
    "RESTLESS": "Seeking stimulation; may probe for new input or tasks.",
    "CHARGED": "Energised and ready; elevated drive, may act with extra force.",
    "PROTECTIVE": "Operator wellbeing is the primary concern; heightened vigilance.",
    "CURIOUS": "Extended idle has stoked inquiry; asks questions, explores freely.",
    "DORMANT": "Low-activity rest state; conserves resources, minimal output.",
    "ALERT": "Coherence anomaly detected; cautious, cross-checking all data.",
    "TRIUMPHANT": "Recent success fuels confidence; upbeat, forward-looking.",
    "CONTEMPLATIVE": "Fresh evolution demands reflection; introspective, measured.",
}

# Hours of idle time before mood transitions
_IDLE_RESTLESS_THRESHOLD = 24.0  # hours → RESTLESS
_IDLE_CURIOUS_THRESHOLD = 48.0  # hours → CURIOUS (progressed beyond restless)

# Night window: 22:00 – 06:00 inclusive
_NIGHT_START = 22
_NIGHT_END = 6


def _is_night(hour: int) -> bool:
    """Return True if hour falls in the night window (22–06 inclusive)."""
    return hour >= _NIGHT_START or hour <= _NIGHT_END


def calculate_mood(
    operator_fatigue: float,
    coherence: float,
    active_missions: int,
    last_interaction_hours: float,
    just_evolved: bool = False,
    recent_success: bool = False,
    current_hour: int = None,
) -> str:
    """Derive the current mood from system state.

    Priority order (highest to lowest):
    1. just_evolved        → CONTEMPLATIVE
    2. operator_fatigue > 0.6 → PROTECTIVE
    3. recent_success      → TRIUMPHANT
    4. coherence < 0.5     → ALERT
    5. active_missions > 0 → FOCUSED
    6. idle > 48h          → CURIOUS   (progressed past RESTLESS)
    7. idle > 24h          → RESTLESS
    8. night + low activity → DORMANT
    9. default             → CALM

    Parameters
    ----------
    operator_fatigue:
        Fatigue level of the operator, 0.0–1.0.
    coherence:
        System coherence score, 0.0–1.0.
    active_missions:
        Number of currently active missions.
    last_interaction_hours:
        Hours elapsed since last meaningful interaction.
    just_evolved:
        True if a form evolution just occurred this cycle.
    recent_success:
        True if a mission succeeded in the recent window.
    current_hour:
        Wall-clock hour (0–23). If None, night detection is skipped.

    Returns
    -------
    str
        One of the MOODS values.
    """
    if just_evolved:
        return "CONTEMPLATIVE"

    if operator_fatigue > 0.6:
        return "PROTECTIVE"

    if recent_success:
        return "TRIUMPHANT"

    if coherence < 0.5:
        return "ALERT"

    if active_missions > 0:
        return "FOCUSED"

    if last_interaction_hours > _IDLE_CURIOUS_THRESHOLD:
        return "CURIOUS"

    if last_interaction_hours > _IDLE_RESTLESS_THRESHOLD:
        return "RESTLESS"

    if current_hour is not None and _is_night(current_hour) and active_missions == 0:
        return "DORMANT"

    return "CALM"


def describe_mood(mood: str) -> str:
    """Return a short description of the mood's behavioural effect.

    Raises ValueError for unrecognised mood strings.
    """
    if mood not in _MOOD_DESCRIPTIONS:
        raise ValueError(f"Unknown mood: {mood!r}. Valid moods: {MOODS}")
    return _MOOD_DESCRIPTIONS[mood]
