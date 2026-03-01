from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class HealthStatus:
    coherence: float
    freeze_autonomy: bool
    alert: str


def update_status(coherence: float, low_since_iso: str | None) -> HealthStatus:
    """Flag coherence dip and freeze autonomy when coherence < 0.7 for >60s."""
    now = datetime.now(timezone.utc)

    if coherence >= 0.7:
        return HealthStatus(coherence=coherence, freeze_autonomy=False, alert="ok")

    if low_since_iso:
        try:
            low_since = datetime.fromisoformat(low_since_iso)
        except Exception:
            low_since = now
    else:
        low_since = now

    freeze = (now - low_since) > timedelta(seconds=60)
    alert = "coherence_dip_freeze" if freeze else "coherence_dip_watch"
    return HealthStatus(coherence=coherence, freeze_autonomy=freeze, alert=alert)
