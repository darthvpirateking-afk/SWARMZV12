# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Hologram Evolution Ladder â€” Core Engine.

XP = count(verified trials). Evolutions unlock at XP thresholds +
minimum survival-data quality. Unlocks are deterministic (no vibes).

Levels:
  LV0 EGG        0â€“4 verified trials
  LV1 ROOKIE     â‰¥5 verified trials
  LV2 CHAMPION   â‰¥20 verified trials, â‰¥5 per metric
  LV3 ULTIMATE   â‰¥60 verified trials, â‰¥20 in same context_tag
  LV4 MEGA       â‰¥150 verified trials, â‰¥10 drift events
  LV5 BURST      manual toggle; requires rollback available

Power Currencies (all computed, never manual):
  STABILITY     % survived in last 30 days
  NOVELTY       % novel action_templates in last 30 days
  REVERSIBILITY % trials with valid rollback path

Add-only module.  No existing files modified.
"""

import json
import math
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.trials import (
    load_all_trials,
    compute_survival_scores,
    get_audit_trail,
    new_trial,
    _audit_event,
    _now_iso,
)

# â”€â”€ Storage â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_HOLO_DIR = Path(__file__).resolve().parent.parent / "data" / "hologram"
_HOLO_DIR.mkdir(parents=True, exist_ok=True)
_STATE_FILE = _HOLO_DIR / "holo_state.json"
_BURST_FILE = _HOLO_DIR / "burst_sessions.jsonl"
_DRIFT_EVENTS_FILE = _HOLO_DIR / "drift_events.jsonl"

_LOCK = threading.Lock()


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 1. XP + LEVEL COMPUTATION
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

LEVELS = [
    {"level": 0, "name": "EGG", "xp_min": 0, "label": "LV0 Â· EGG"},
    {"level": 1, "name": "ROOKIE", "xp_min": 5, "label": "LV1 Â· ROOKIE"},
    {"level": 2, "name": "CHAMPION", "xp_min": 20, "label": "LV2 Â· CHAMPION"},
    {"level": 3, "name": "ULTIMATE", "xp_min": 60, "label": "LV3 Â· ULTIMATE"},
    {"level": 4, "name": "MEGA", "xp_min": 150, "label": "LV4 Â· MEGA"},
    {"level": 5, "name": "BURST", "xp_min": 150, "label": "LV5 Â· BURST MODE"},
]


def _verified_trials(trials: List[Dict]) -> List[Dict]:
    """Filter to trials that have been checked (checked_at is set)."""
    return [t for t in trials if t.get("checked_at") is not None]


def compute_xp(trials: Optional[List[Dict]] = None) -> int:
    """XP = number of verified trials."""
    if trials is None:
        trials = load_all_trials()
    return len(_verified_trials(trials))


def _metrics_per_metric_count(verified: List[Dict]) -> Dict[str, int]:
    """Count verified trials per metric_name."""
    counts: Dict[str, int] = {}
    for t in verified:
        m = t.get("metric_name", "")
        counts[m] = counts.get(m, 0) + 1
    return counts


def _max_same_context_tag(verified: List[Dict]) -> int:
    """Max count of verified trials sharing the same first tag."""
    tag_counts: Dict[str, int] = {}
    for t in verified:
        tags = t.get("tags", [])
        tag = tags[0] if tags else "untagged"
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return max(tag_counts.values()) if tag_counts else 0


def _drift_event_count() -> int:
    """Count total drift events recorded."""
    events = _read_drift_events()
    return len(events)


def _read_drift_events() -> List[Dict]:
    """Read drift events from hologram data."""
    if not _DRIFT_EVENTS_FILE.exists():
        return []
    try:
        rows = []
        with _DRIFT_EVENTS_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return rows
    except Exception:
        return []


def _burst_enabled() -> bool:
    """Check if burst mode is manually toggled on."""
    state = _load_state()
    return state.get("burst_enabled", False)


def compute_level(trials: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Compute current evolution level + unlock progress.
    Returns full state: level, name, xp, next unlock, currencies, etc.
    """
    if trials is None:
        trials = load_all_trials()

    verified = _verified_trials(trials)
    xp = len(verified)
    metrics_counts = _metrics_per_metric_count(verified)
    min_per_metric = min(metrics_counts.values()) if metrics_counts else 0
    max_context_tag = _max_same_context_tag(verified)
    drift_count = _drift_event_count()

    # Determine level
    level = 0
    unlock_reason = "Need â‰¥5 verified trials"

    if xp >= 5:
        level = 1
        unlock_reason = "Need â‰¥20 verified trials AND â‰¥5 per metric"

    if xp >= 20 and min_per_metric >= 5:
        level = 2
        unlock_reason = "Need â‰¥60 verified trials AND â‰¥20 in same context_tag"

    if xp >= 60 and max_context_tag >= 20:
        level = 3
        unlock_reason = "Need â‰¥150 verified trials AND â‰¥10 drift events"

    if xp >= 150 and drift_count >= 10:
        level = 4
        unlock_reason = "Burst Mode available (manual toggle, rollback required)"

    # LV5 is special: manual toggle
    if level >= 4 and _burst_enabled():
        level = 5
        unlock_reason = "BURST MODE active"

    level_info = LEVELS[level]

    # Next level info
    next_level = None
    if level < 4:
        nl = LEVELS[level + 1]
        next_level = {
            "level": nl["level"],
            "name": nl["name"],
            "xp_needed": nl["xp_min"],
            "hint": unlock_reason,
        }
    elif level == 4:
        next_level = {
            "level": 5,
            "name": "BURST",
            "xp_needed": 150,
            "hint": "Toggle Burst Mode (rollback required)",
        }

    # Power currencies
    currencies = compute_power_currencies(verified)

    # Unlocked powers
    powers = _powers_for_level(level)

    return {
        "level": level,
        "name": level_info["name"],
        "label": level_info["label"],
        "xp": xp,
        "xp_total": len(trials),
        "next_level": next_level,
        "currencies": currencies,
        "powers": powers,
        "metrics_counts": metrics_counts,
        "max_context_tag": max_context_tag,
        "drift_events": drift_count,
        "burst_enabled": _burst_enabled(),
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 2. POWER CURRENCIES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def compute_power_currencies(verified: Optional[List[Dict]] = None) -> Dict[str, float]:
    """
    STABILITY     % survived in last 30 days
    NOVELTY       % novel action_templates in last 30 days
    REVERSIBILITY % trials with rollback path (reverted=True or has revert tag)
    """
    if verified is None:
        verified = _verified_trials(load_all_trials())

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)

    # Single pass: collect recent IDs, recent/old templates, stability, reversibility
    recent_ids: set[str] = set()
    recent_templates: set[str] = set()
    old_templates: set[str] = set()
    survived_count = 0
    with_rollback = 0

    for t in verified:
        tid = t.get("id") or ""
        tmpl = (t.get("action", "").split(":")[0].strip() or "unknown").lower()
        is_recent = False
        try:
            ca = t.get("checked_at", "")
            if ca:
                ca_dt = datetime.fromisoformat(ca.replace("Z", "+00:00"))
                if ca_dt >= cutoff:
                    is_recent = True
        except Exception:
            pass

        if is_recent:
            if tid:
                recent_ids.add(tid)
            recent_templates.add(tmpl)
            if t.get("survived") is True:
                survived_count += 1
        else:
            old_templates.add(tmpl)

        if (
            t.get("reverted")
            or "revert" in t.get("tags", [])
            or "followup" in t.get("tags", [])
        ):
            with_rollback += 1

    # STABILITY: % survived in last 30 days
    recent_count = len(recent_ids)
    stability = round(survived_count / recent_count, 4) if recent_count else 0.0

    # NOVELTY: % of recent templates not seen in older trials
    novel_templates = recent_templates - old_templates
    novelty = (
        round(len(novel_templates) / len(recent_templates), 4)
        if recent_templates
        else 0.0
    )

    # REVERSIBILITY: % of verified trials with rollback path
    reversibility = (
        round(with_rollback / len(verified), 4) if verified else 0.0
    )

    return {
        "stability": stability,
        "novelty": novelty,
        "reversibility": reversibility,
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 3. POWERS PER LEVEL
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def _powers_for_level(level: int) -> List[Dict[str, Any]]:
    """Return list of unlocked powers at given level (cumulative)."""
    all_powers = [
        {
            "level": 1,
            "id": "auto_baseline",
            "name": "Auto-baseline capture",
            "description": "Baseline metric is captured at trial creation time. Enforced.",
        },
        {
            "level": 2,
            "id": "auto_check_scheduler",
            "name": "Auto-check scheduler + Inbox triage",
            "description": "Due trials auto-check. Failed trials go to Needs Review.",
        },
        {
            "level": 3,
            "id": "survival_ranking",
            "name": "Survival score ranking",
            "description": "Suggestions sorted by survival_rate (Laplace smoothed). Low-confidence flagged.",
        },
        {
            "level": 4,
            "id": "drift_alarms",
            "name": "Drift alarms",
            "description": "Detect metric drift bands. Proposes follow-up trials (never auto-exec).",
        },
        {
            "level": 5,
            "id": "parallel_batch",
            "name": "Parallel batch trials",
            "description": "Run 3-10 small trials concurrently with budget + kill-switch + rollback.",
        },
    ]
    return [p for p in all_powers if p["level"] <= level]


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 4. VISUAL EFFECTS DATA (cosmetic but honest)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def compute_effects(trial: Optional[Dict] = None, level: int = 0) -> Dict[str, Any]:
    """
    Compute cosmetic effect params driven by real numbers.
    Returns CSS-ready values for the frontend.
    """
    effects = {
        "glow_intensity": 0.0,
        "flicker_rate": 0.0,
        "scanlines": level >= 2,
        "field_shimmer": False,
        "overclock": level >= 5,
        "evolution_anim": False,
        "level_name": LEVELS[min(level, 5)]["name"],
    }

    if trial and trial.get("survived") is not None:
        # Glow = |delta| / max_expected, clamped 0..1
        metric_before = trial.get("metric_before") or 0
        metric_after = trial.get("metric_after") or 0
        expected_delta = trial.get("expected_delta")
        delta = abs(metric_after - metric_before)
        max_delta = abs(expected_delta) if expected_delta else max(delta, 0.01)
        effects["glow_intensity"] = round(min(delta / max_delta, 1.0), 4)

        # Flicker = failure rate in context tag
        if trial.get("survived") is False:
            effects["flicker_rate"] = 0.6
        else:
            effects["flicker_rate"] = 0.0

    # Field shimmer at LV4 when stability > 0.7
    if level >= 4:
        currencies = compute_power_currencies()
        if currencies["stability"] > 0.7:
            effects["field_shimmer"] = True

    return effects


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 5. TRIAL DETAIL FOR HOLOGRAM (level-gated content)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def hologram_trial_detail(trial_id: str) -> Dict[str, Any]:
    """
    Return trial detail with level-gated content.
    Higher levels unlock richer content.
    """
    from core.trials import get_trial

    trial = get_trial(trial_id)
    if not trial:
        return {"ok": False, "error": "trial not found"}

    state = compute_level()
    level = state["level"]

    detail: Dict[str, Any] = {
        "ok": True,
        "level": level,
        "level_name": state["name"],
        "trial": trial,
        "effects": compute_effects(trial, level),
        "powers": state["powers"],
    }

    # LV1+: basic detail card
    if level >= 1:
        detail["verdict"] = _verdict_badge(trial)

    # LV2+: delta graph data + audit spine + why-failed hint
    if level >= 2:
        detail["delta_graph"] = _build_delta_graph(trial)
        detail["audit_spine"] = get_audit_trail(trial_id=trial_id, tail=30)
        if trial.get("survived") is False:
            detail["why_failed_hint"] = _why_failed_hint(trial)

    # LV3+: trajectory (state graph) + survival score on edges
    if level >= 3:
        detail["trajectory"] = _build_trajectory(trial.get("context", ""))
        detail["survival_scores"] = compute_survival_scores()

    # LV4+: stability field + drift indicators
    if level >= 4:
        detail["stability_field"] = _build_stability_field(trial)
        detail["drift_indicators"] = _get_drift_indicators(trial.get("context", ""))

    return detail


def _verdict_badge(trial: Dict) -> Dict[str, Any]:
    """Build verdict badge data."""
    if trial.get("reverted"):
        return {"status": "reverted", "label": "REVERTED", "color": "amber"}
    if trial.get("survived") is True:
        return {"status": "survived", "label": "SURVIVED", "color": "mint"}
    if trial.get("survived") is False:
        return {"status": "failed", "label": "FAILED", "color": "red"}
    return {"status": "pending", "label": "PENDING", "color": "cyan"}


def _build_delta_graph(trial: Dict) -> Dict[str, Any]:
    """
    Build a small time plot of metric around baseline.
    Even 3 points is fine: before, expected, after.
    """
    before = trial.get("metric_before")
    after = trial.get("metric_after")
    expected_delta = trial.get("expected_delta")
    expected = None
    if before is not None and expected_delta is not None:
        expected = before + expected_delta

    points = []
    if before is not None:
        points.append(
            {"label": "Baseline", "value": before, "ts": trial.get("created_at")}
        )
    if expected is not None:
        points.append(
            {"label": "Expected", "value": expected, "ts": trial.get("check_at")}
        )
    if after is not None:
        points.append({"label": "After", "value": after, "ts": trial.get("checked_at")})

    return {
        "metric_name": trial.get("metric_name", ""),
        "points": points,
        "baseline": before,
        "target": expected,
        "actual": after,
    }


def _why_failed_hint(trial: Dict) -> str:
    """
    Rule-based hint for why a trial failed. No LLM needed.
    Uses evidence fields.
    """
    before = trial.get("metric_before") or 0
    after = trial.get("metric_after") or 0
    expected_delta = trial.get("expected_delta")
    evidence = trial.get("evidence", {})

    hints = []

    delta = after - before
    if expected_delta is not None:
        shortfall = (before + expected_delta) - after
        if shortfall > 0:
            hints.append(
                f"Metric fell short by {round(shortfall, 4)} (needed +{expected_delta}, got {round(delta, 4)})"
            )
    else:
        if after < before:
            hints.append(
                f"Metric worsened: {before} â†’ {after} (Î”={round(delta, 4)})"
            )

    # Check if baseline was captured late
    eval_ev = evidence.get("evaluation", {})
    if eval_ev.get("metric_before") is None and trial.get("metric_before") is None:
        hints.append("No baseline was captured â€” comparison unreliable")

    if not hints:
        hints.append("Trial did not meet survival threshold")

    return " | ".join(hints)


def _build_trajectory(context: str) -> Dict[str, Any]:
    """
    Build a state graph for a context:
    - nodes = unique state snapshots (trials at points in time)
    - edges = trial actions with survival badge
    """
    trials = load_all_trials()
    ctx_trials = [t for t in trials if t.get("context", "") == context]
    ctx_trials.sort(key=lambda t: t.get("created_at", ""))

    nodes = []
    edges = []

    for i, t in enumerate(ctx_trials):
        node_id = f"n{i}"
        nodes.append(
            {
                "id": node_id,
                "label": t.get("action", "?")[:30],
                "trial_id": t.get("id"),
                "metric_before": t.get("metric_before"),
                "metric_after": t.get("metric_after"),
                "survived": t.get("survived"),
            }
        )
        if i > 0:
            prev_id = f"n{i-1}"
            survived = t.get("survived")
            # Compute edge survival score
            tmpl = (t.get("action", "").split(":")[0].strip() or "unknown").lower()
            tags = t.get("tags", [])
            tag = tags[0] if tags else "untagged"
            scores = compute_survival_scores()
            key = f"{tmpl}|{tag}"
            score_data = scores.get(key, {})
            edge_score = score_data.get("survival_rate", 0.5)

            edges.append(
                {
                    "from": prev_id,
                    "to": node_id,
                    "action": t.get("action", ""),
                    "survived": survived,
                    "survival_score": edge_score,
                    "style": "steady" if survived else "flicker",
                }
            )

    return {"nodes": nodes, "edges": edges, "context": context}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 6. DRIFT DETECTION (for LV4 MEGA)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def detect_drift(
    metric_name: str, context: str, window_days: int = 7
) -> Dict[str, Any]:
    """
    Detect metric drift by comparing recent vs older trial outcomes.
    Returns drift event if band exceeded.
    """
    trials = load_all_trials()
    verified = _verified_trials(trials)
    relevant = [
        t
        for t in verified
        if t.get("metric_name") == metric_name
        and t.get("context", "") == context
        and t.get("metric_after") is not None
    ]

    if len(relevant) < 4:
        return {"drift": False, "reason": "insufficient data", "n": len(relevant)}

    relevant.sort(key=lambda t: t.get("checked_at", ""))

    # Split into older half and recent window
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window_days)
    recent_vals = []
    older_vals = []
    for t in relevant:
        try:
            ca = datetime.fromisoformat(t["checked_at"].replace("Z", "+00:00"))
            val = float(t["metric_after"])
            if ca >= cutoff:
                recent_vals.append(val)
            else:
                older_vals.append(val)
        except Exception:
            continue

    if not older_vals or not recent_vals:
        return {"drift": False, "reason": "not enough split data"}

    older_mean = sum(older_vals) / len(older_vals)
    recent_mean = sum(recent_vals) / len(recent_vals)

    # Std dev of older
    if len(older_vals) >= 2:
        variance = sum((v - older_mean) ** 2 for v in older_vals) / (
            len(older_vals) - 1
        )
        older_std = math.sqrt(variance) if variance > 0 else 0.001
    else:
        older_std = 0.001

    drift_magnitude = abs(recent_mean - older_mean) / older_std
    is_drift = drift_magnitude > 1.5  # ~1.5 sigma threshold

    result = {
        "drift": is_drift,
        "drift_magnitude": round(drift_magnitude, 4),
        "older_mean": round(older_mean, 4),
        "recent_mean": round(recent_mean, 4),
        "older_std": round(older_std, 4),
        "metric_name": metric_name,
        "context": context,
        "older_n": len(older_vals),
        "recent_n": len(recent_vals),
    }

    if is_drift:
        # Record drift event
        _append_drift_event(result)

        # Also emit an audit event so drift alarms are visible in the
        # main trials audit trail (LV4 MEGA power usage).
        try:
            _audit_event(
                "drift_detected",
                "NONE",
                {
                    "metric_name": metric_name,
                    "context": context,
                    "drift_magnitude": result["drift_magnitude"],
                    "older_mean": result["older_mean"],
                    "recent_mean": result["recent_mean"],
                    "older_std": result["older_std"],
                },
            )
        except Exception:
            # Never let audit failures break detection.
            pass

    return result


def _append_drift_event(event: Dict) -> None:
    """Append a drift event to the drift events file."""
    with _LOCK:
        try:
            event["ts"] = _now_iso()
            event["event_id"] = str(__import__("uuid").uuid4())
            with _DRIFT_EVENTS_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, separators=(",", ":"), default=str) + "\n")
        except Exception:
            pass


def _get_drift_indicators(context: str) -> List[Dict]:
    """Get drift events for a context."""
    events = _read_drift_events()
    return [e for e in events if e.get("context") == context][-10:]


def _build_stability_field(trial: Dict) -> Dict[str, Any]:
    """
    Build stability field data: current metric band (min/target/max)
    and recent drift events.
    """
    metric_name = trial.get("metric_name", "")
    context = trial.get("context", "")

    trials = load_all_trials()
    verified = _verified_trials(trials)
    relevant = [
        t
        for t in verified
        if t.get("metric_name") == metric_name
        and t.get("context", "") == context
        and t.get("metric_after") is not None
    ]

    values = [
        float(t["metric_after"]) for t in relevant if t.get("metric_after") is not None
    ]

    if not values:
        return {"metric_name": metric_name, "context": context, "band": None}

    current = values[-1] if values else 0
    mean_val = sum(values) / len(values)
    min_val = min(values)
    max_val = max(values)

    # Standard deviation
    if len(values) >= 2:
        variance = sum((v - mean_val) ** 2 for v in values) / (len(values) - 1)
        std_val = math.sqrt(variance)
    else:
        std_val = 0

    # Band = mean Â± 1 std
    band_low = round(mean_val - std_val, 4)
    band_high = round(mean_val + std_val, 4)
    in_band = band_low <= current <= band_high

    return {
        "metric_name": metric_name,
        "context": context,
        "current": round(current, 4),
        "mean": round(mean_val, 4),
        "min": round(min_val, 4),
        "max": round(max_val, 4),
        "band_low": band_low,
        "band_high": band_high,
        "in_band": in_band,
        "std": round(std_val, 4),
        "n_samples": len(values),
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 7. MEGA POWER: DRIFT ALARM SUGGESTIONS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def suggest_drift_correction(metric_name: str, context: str) -> Optional[Dict]:
    """
    Propose a micro-correction as a follow-up trial.
    NEVER auto-executes; always creates a gated trial suggestion.
    Returns trial suggestion dict or None.
    """
    drift = detect_drift(metric_name, context)
    if not drift.get("drift"):
        return None

    # Build suggestion (not created yet â€” operator must confirm)
    direction = "increase" if drift["recent_mean"] < drift["older_mean"] else "decrease"
    delta = abs(drift["older_mean"] - drift["recent_mean"])

    suggestion = {
        "action": f"Drift correction: {direction} {metric_name}",
        "context": context,
        "metric_name": metric_name,
        "check_after_sec": 600,
        "expected_delta": round(delta * 0.5, 4),
        "tags": ["drift_correction", "auto_suggested"],
        "notes": f"Auto-suggested: drift {round(drift['drift_magnitude'], 2)}Ïƒ detected. Propose {direction} correction.",
        "drift_data": drift,
    }

    _audit_event(
        "drift_correction_suggested",
        "NONE",
        {
            "metric_name": metric_name,
            "context": context,
            "drift_magnitude": drift["drift_magnitude"],
            "suggestion": suggestion["action"],
        },
    )

    return suggestion


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 8. BURST MODE (LV5)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def _load_state() -> Dict[str, Any]:
    """Load hologram state from file."""
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_state(state: Dict[str, Any]) -> None:
    """Save hologram state to file."""
    with _LOCK:
        try:
            _STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except Exception:
            pass


def toggle_burst_mode(enabled: bool) -> Dict[str, Any]:
    """
    Toggle Burst Mode on/off.
    Requires: LV4+ and reversibility > 0 (rollback path exists).
    """
    state = _load_state()
    level_data = compute_level()

    if level_data["level"] < 4:
        return {"ok": False, "error": "Burst Mode requires LV4 (MEGA) or above"}

    currencies = level_data["currencies"]
    if enabled and currencies["reversibility"] <= 0:
        return {
            "ok": False,
            "error": "Burst Mode requires rollback capability (reversibility > 0)",
        }

    state["burst_enabled"] = enabled
    state["burst_toggled_at"] = _now_iso()
    _save_state(state)

    _audit_event(
        "burst_mode_toggled",
        "NONE",
        {
            "enabled": enabled,
            "level": level_data["level"],
            "reversibility": currencies["reversibility"],
        },
    )

    return {"ok": True, "burst_enabled": enabled}


def create_burst_batch(
    trials_specs: List[Dict[str, Any]],
    budget_sec: int = 3600,
    max_parallel: int = 10,
    created_by: str = "burst",
) -> Dict[str, Any]:
    """
    Create a batch of parallel trials with budget + kill-switch.
    Requires: Burst Mode enabled, 3â€“10 trials, budget set.

    Each spec: {action, context, metric_name, check_after_sec, expected_delta, tags}
    """
    if not _burst_enabled():
        return {"ok": False, "error": "Burst Mode not enabled"}

    if len(trials_specs) < 3 or len(trials_specs) > max_parallel:
        return {"ok": False, "error": f"Burst batch requires 3â€“{max_parallel} trials"}

    if budget_sec < 60:
        return {"ok": False, "error": "Budget must be at least 60 seconds"}

    batch_id = str(__import__("uuid").uuid4())
    created_trials = []

    for i, spec in enumerate(trials_specs[:max_parallel]):
        check_sec = min(spec.get("check_after_sec", 300), budget_sec)
        trial = new_trial(
            created_by=created_by,
            context=spec.get("context", "burst"),
            action=spec.get("action", f"Burst trial {i+1}"),
            metric_name=spec.get("metric_name", "conversion_rate"),
            check_after_sec=check_sec,
            expected_delta=spec.get("expected_delta"),
            tags=["burst", f"batch:{batch_id}"] + spec.get("tags", []),
            notes=f"Burst batch {batch_id}, trial {i+1}/{len(trials_specs)}",
        )
        created_trials.append(trial)

    # Record batch session
    batch_record = {
        "batch_id": batch_id,
        "created_at": _now_iso(),
        "created_by": created_by,
        "budget_sec": budget_sec,
        "trial_count": len(created_trials),
        "trial_ids": [t["id"] for t in created_trials],
        "kill_switch": True,
        "status": "active",
    }

    with _LOCK:
        try:
            with _BURST_FILE.open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps(batch_record, separators=(",", ":"), default=str) + "\n"
                )
        except Exception:
            pass

    _audit_event(
        "burst_batch_created",
        batch_id,
        {
            "trial_count": len(created_trials),
            "budget_sec": budget_sec,
            "trial_ids": [t["id"] for t in created_trials],
        },
    )

    return {
        "ok": True,
        "batch_id": batch_id,
        "trials": created_trials,
        "budget_sec": budget_sec,
        "kill_switch": True,
    }


def kill_burst_batch(batch_id: str) -> Dict[str, Any]:
    """
    Kill switch: immediately mark all trials in a burst batch as reverted.
    """
    from core.trials import revert_trial

    # Find batch
    if not _BURST_FILE.exists():
        return {"ok": False, "error": "No burst sessions found"}

    batches = []
    try:
        with _BURST_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        batches.append(json.loads(line))
                    except Exception:
                        continue
    except Exception:
        return {"ok": False, "error": "Cannot read burst sessions"}

    target = None
    for b in batches:
        if b.get("batch_id") == batch_id:
            target = b
            break

    if not target:
        return {"ok": False, "error": f"Batch {batch_id} not found"}

    reverted_ids = []
    for tid in target.get("trial_ids", []):
        result = revert_trial(tid, created_by="burst_kill_switch")
        if result:
            reverted_ids.append(tid)

    _audit_event(
        "burst_batch_killed",
        batch_id,
        {
            "reverted_count": len(reverted_ids),
            "trial_ids": reverted_ids,
        },
    )

    return {
        "ok": True,
        "batch_id": batch_id,
        "reverted_count": len(reverted_ids),
    }


def list_burst_batches(limit: int = 20) -> List[Dict]:
    """List recent burst batch sessions."""
    if not _BURST_FILE.exists():
        return []
    try:
        rows = []
        with _BURST_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        continue
        return rows[-limit:]
    except Exception:
        return []


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 9. FOLLOW-UP SUGGESTION (for LV3 ULTIMATE)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def suggest_best_followups(context: str, limit: int = 5) -> List[Dict]:
    """
    Suggest best follow-up trial templates based on survival scores.
    Sorted by survival_rate descending (Laplace smoothed).
    """
    scores = compute_survival_scores()
    relevant = []
    for key, data in scores.items():
        tag = data.get("tag", "")
        if context and tag != context and data.get("action_template", "") != context:
            # include if context matches either tag or action_template
            continue
        relevant.append(data)

    if not relevant:
        # If no specific match, return all scores
        relevant = list(scores.values())

    relevant.sort(key=lambda x: x.get("survival_rate", 0), reverse=True)

    suggestions = []
    for s in relevant[:limit]:
        suggestions.append(
            {
                "action": f"{s['action_template']}: follow-up",
                "context": context,
                "metric_name": "conversion_rate",
                "check_after_sec": 300,
                "survival_rate": s["survival_rate"],
                "survived_count": s["survived_count"],
                "failed_count": s["failed_count"],
                "low_confidence": s["survival_rate"] < 0.4,
            }
        )

    # Audit LV3 ULTIMATE power usage: survival-ranking driven suggestions.
    try:
        _audit_event(
            "followup_suggestions_generated",
            "NONE",
            {
                "context": context,
                "limit": limit,
                "count": len(suggestions),
            },
        )
    except Exception:
        pass

    return suggestions
