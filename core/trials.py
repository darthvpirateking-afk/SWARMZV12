# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Trials Inbox â€” Core Data Model, Storage, Gate, Metrics, Scoring.

Every meaningful change becomes a measurable Trial with delayed verification.
Append-only, audit-friendly, learns by survival outcomes (not opinion).
"""

import json
import uuid
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# â”€â”€ Storage paths â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "trials"
_TRIALS_FILE = _DATA_DIR / "trials.jsonl"
_AUDIT_FILE = _DATA_DIR / "audit.jsonl"
_SCORES_FILE = _DATA_DIR / "survival_scores.json"

_DATA_DIR.mkdir(parents=True, exist_ok=True)

_LOCK = threading.Lock()


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 1. DATA MODEL
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _now_ts() -> float:
    return time.time()


def new_trial(
    created_by: str,
    context: str,
    action: str,
    metric_name: str,
    check_after_sec: int,
    expected_delta: Optional[float] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None,
    evidence: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new Trial dict with all required fields."""
    now = _now_iso()
    ts = _now_ts()
    check_at = datetime.fromtimestamp(ts + check_after_sec, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    # Capture baseline metric at creation time â€” gated by Hologram level.
    # LV1 ROOKIE power: auto-baseline capture. Below LV1, we intentionally
    # skip this so early trials behave as "no baseline" and are evaluated
    # against their first measurement.
    baseline = None
    baseline_evidence = None
    # LV1 ROOKIE unlocks at >=5 verified trials (checked_at is set).
    # Compute directly to avoid a circular import with core.hologram.
    try:
        all_trials = load_all_trials()
        verified_count = sum(1 for t in all_trials if t.get("checked_at") is not None)
        allow_auto_baseline = verified_count >= 5
    except Exception:
        allow_auto_baseline = True

    if allow_auto_baseline:
        try:
            baseline, baseline_evidence = resolve_metric(metric_name, context)
        except Exception:
            pass  # fail-open: baseline will be captured later if needed

    trial = {
        "id": str(uuid.uuid4()),
        "created_at": now,
        "created_by": created_by,
        "context": context,
        "action": action,
        "metric_name": metric_name,
        "metric_before": baseline,
        "expected_delta": expected_delta,
        "check_after_sec": check_after_sec,
        "check_at": check_at,
        "checked_at": None,
        "metric_after": None,
        "survived": None,
        "reverted": False,
        "notes": notes,
        "tags": tags or [],
        "evidence": evidence or {},
    }

    if baseline_evidence:
        trial["evidence"]["baseline"] = baseline_evidence

    _append_trial(trial)
    _audit_event(
        "trial_created",
        trial["id"],
        {
            "action": action,
            "context": context,
            "metric_name": metric_name,
            "check_after_sec": check_after_sec,
            "metric_before": baseline,
        },
    )

    # Audit explicit use of the LV1 auto-baseline power when it is unlocked.
    if allow_auto_baseline and baseline is not None:
        _audit_event(
            "auto_baseline_captured",
            trial["id"],
            {
                "metric_name": metric_name,
                "context": context,
                "metric_before": baseline,
            },
        )

    return trial


# â”€â”€ Append-only persistence â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    """Append a single JSON object as a line. Thread-safe."""
    with _LOCK:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(obj, separators=(",", ":"), default=str) + "\n")
        except Exception:
            pass  # fail-open


def _append_trial(trial: Dict[str, Any]) -> None:
    _append_jsonl(_TRIALS_FILE, trial)


def _audit_event(
    event_type: str, trial_id: str, payload: Optional[Dict] = None
) -> None:
    event = {
        "event_id": str(uuid.uuid4()),
        "ts": _now_iso(),
        "event_type": event_type,
        "trial_id": trial_id,
        "payload": payload or {},
    }
    _append_jsonl(_AUDIT_FILE, event)


# â”€â”€ Read helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read all valid JSON lines from a file. Fail-open returns []."""
    if not path.exists():
        return []
    try:
        rows = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows
    except Exception:
        return []


def load_all_trials() -> List[Dict[str, Any]]:
    """Load all trials. De-duplicates by id, keeping last version."""
    rows = _read_jsonl(_TRIALS_FILE)
    seen: Dict[str, Dict] = {}
    for r in rows:
        tid = r.get("id")
        if tid:
            seen[tid] = r
    return list(seen.values())


def get_trial(trial_id: str) -> Optional[Dict[str, Any]]:
    """Get a single trial by id."""
    rows = _read_jsonl(_TRIALS_FILE)
    result = None
    for r in rows:
        if r.get("id") == trial_id:
            result = r  # keep last version (append-only log, last entry wins)
    return result


def update_trial(
    trial_id: str, updates: Dict[str, Any], reason: str = "update"
) -> Optional[Dict[str, Any]]:
    """
    'Update' a trial by appending a new version (append-only).
    The latest version for a given id wins when reading.
    """
    trial = get_trial(trial_id)
    if not trial:
        return None
    trial.update(updates)
    _append_trial(trial)
    _audit_event(reason, trial_id, updates)
    return trial


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 2. TRIAL CREATION GATE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class TrialGateError(Exception):
    """Raised when a meaningful change is attempted without a Trial."""

    pass


def require_trial(
    action: str,
    context: str,
    metric_name: str,
    check_after_sec: int = 300,
    created_by: str = "system",
    non_trial_reason: Optional[str] = None,
    admin: bool = False,
    **kwargs,
) -> Optional[Dict[str, Any]]:
    """
    Gate function: meaningful changes must either create a Trial or be
    explicitly marked non-trial (admin-only) with a reason.

    Returns the Trial dict if created, or None if exempted.
    Raises TrialGateError if neither condition is met.
    """
    if non_trial_reason:
        if not admin:
            raise TrialGateError(
                "Only admin can mark a change as non-trial. "
                "Provide admin=True or create a Trial."
            )
        _audit_event(
            "non_trial_exemption",
            "NONE",
            {
                "action": action,
                "context": context,
                "reason": non_trial_reason,
                "created_by": created_by,
            },
        )
        return None

    return new_trial(
        created_by=created_by,
        context=context,
        action=action,
        metric_name=metric_name,
        check_after_sec=check_after_sec,
        **kwargs,
    )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 3. METRICS INTERFACE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# Registry of metric resolver functions
_METRIC_RESOLVERS: Dict[str, Any] = {}


def register_metric(name: str, resolver_fn):
    """Register a metric resolver function: fn(context) -> (number, evidence_dict)."""
    _METRIC_RESOLVERS[name] = resolver_fn


def resolve_metric(
    metric_name: str, context: str
) -> Tuple[Optional[float], Optional[Dict]]:
    """
    Resolve a metric value for a given context.
    Returns (value, evidence_dict).
    Falls back to stub resolvers if no custom resolver registered.
    """
    if metric_name in _METRIC_RESOLVERS:
        try:
            result = _METRIC_RESOLVERS[metric_name](context)
            if isinstance(result, tuple) and len(result) == 2:
                return result
            return (float(result), {})
        except Exception:
            return (None, None)

    # Built-in stub resolvers that pull from existing data where possible
    return _builtin_resolve(metric_name, context)


def _builtin_resolve(
    metric_name: str, context: str
) -> Tuple[Optional[float], Optional[Dict]]:
    """Built-in metric stubs. Pull real values from existing SWARMZ data."""
    data_dir = Path(__file__).resolve().parent.parent / "data"

    if metric_name == "conversion_rate":
        return _resolve_conversion_rate(data_dir, context)
    elif metric_name == "activation_rate":
        return _resolve_activation_rate(data_dir, context)
    elif metric_name == "retention_d1":
        return _resolve_retention_d1(data_dir, context)
    elif metric_name == "errors_per_1k":
        return _resolve_errors_per_1k(data_dir, context)
    elif metric_name == "latency_p95":
        return _resolve_latency_p95(data_dir, context)
    elif metric_name == "cost_per_day":
        return _resolve_cost_per_day(data_dir, context)
    else:
        return (None, {"error": f"unknown metric: {metric_name}"})


def _resolve_conversion_rate(data_dir: Path, context: str) -> Tuple[float, Dict]:
    """Mission success rate as conversion proxy."""
    try:
        missions = _read_jsonl(data_dir / "missions.jsonl")
        if not missions:
            return (0.0, {"total": 0, "succeeded": 0})
        total = len(missions)
        succeeded = sum(1 for m in missions if m.get("status") == "SUCCESS")
        rate = round(succeeded / total, 4) if total > 0 else 0.0
        return (rate, {"total": total, "succeeded": succeeded, "context": context})
    except Exception:
        return (0.0, {"error": "could not compute conversion_rate"})


def _resolve_activation_rate(data_dir: Path, context: str) -> Tuple[float, Dict]:
    """Fraction of missions that moved past PENDING."""
    try:
        missions = _read_jsonl(data_dir / "missions.jsonl")
        if not missions:
            return (0.0, {"total": 0})
        total = len(missions)
        activated = sum(1 for m in missions if m.get("status") not in (None, "PENDING"))
        rate = round(activated / total, 4) if total > 0 else 0.0
        return (rate, {"total": total, "activated": activated, "context": context})
    except Exception:
        return (0.0, {"error": "could not compute activation_rate"})


def _resolve_retention_d1(data_dir: Path, context: str) -> Tuple[float, Dict]:
    """Fraction of days with at least one mission (from telemetry)."""
    try:
        tele = _read_jsonl(data_dir / "telemetry.jsonl")
        if not tele:
            return (0.0, {"days_active": 0, "days_total": 0})
        days = set()
        for t in tele:
            ts = t.get("ts", "")
            if len(ts) >= 10:
                days.add(ts[:10])
        days_total = max(len(days), 1)
        missions = _read_jsonl(data_dir / "missions.jsonl")
        mission_days = set()
        for m in missions:
            ts = m.get("created_at") or m.get("timestamp", "")
            if len(ts) >= 10:
                mission_days.add(ts[:10])
        retained = len(days & mission_days) if mission_days else 0
        rate = round(retained / days_total, 4)
        return (rate, {"days_active": retained, "days_total": days_total})
    except Exception:
        return (0.0, {"error": "could not compute retention_d1"})


def _resolve_errors_per_1k(data_dir: Path, context: str) -> Tuple[float, Dict]:
    """Error rate from missions: failures per 1000 missions."""
    try:
        missions = _read_jsonl(data_dir / "missions.jsonl")
        total = max(len(missions), 1)
        failures = sum(1 for m in missions if m.get("status") == "FAILURE")
        per_1k = round((failures / total) * 1000, 2)
        return (per_1k, {"total": total, "failures": failures})
    except Exception:
        return (0.0, {"error": "could not compute errors_per_1k"})


def _resolve_latency_p95(data_dir: Path, context: str) -> Tuple[float, Dict]:
    """P95 latency from telemetry (ms field if available, else stub)."""
    try:
        tele = _read_jsonl(data_dir / "telemetry.jsonl")
        latencies = []
        for t in tele:
            lat = t.get("latency_ms") or t.get("duration_ms")
            if lat is not None:
                try:
                    latencies.append(float(lat))
                except (ValueError, TypeError):
                    pass
        if not latencies:
            return (0.0, {"samples": 0, "note": "no latency data found"})
        latencies.sort()
        idx = int(len(latencies) * 0.95)
        p95 = latencies[min(idx, len(latencies) - 1)]
        return (round(p95, 2), {"samples": len(latencies), "p95": p95})
    except Exception:
        return (0.0, {"error": "could not compute latency_p95"})


def _resolve_cost_per_day(data_dir: Path, context: str) -> Tuple[float, Dict]:
    """Estimate cost from AI audit log (count of API calls as proxy)."""
    try:
        audit = _read_jsonl(data_dir / "audit_ai.jsonl")
        if not audit:
            return (0.0, {"calls": 0})
        # Group by day
        days: Dict[str, int] = {}
        for a in audit:
            ts = a.get("ts", a.get("timestamp", ""))
            if len(ts) >= 10:
                day = ts[:10]
                days[day] = days.get(day, 0) + 1
        if not days:
            return (0.0, {"calls": len(audit), "days": 0})
        avg_calls = sum(days.values()) / len(days)
        # Rough estimate: $0.002 per call
        cost = round(avg_calls * 0.002, 4)
        return (
            cost,
            {"avg_calls_per_day": round(avg_calls, 1), "days_counted": len(days)},
        )
    except Exception:
        return (0.0, {"error": "could not compute cost_per_day"})


def list_available_metrics() -> List[str]:
    """Return list of all known metric names."""
    builtin = [
        "conversion_rate",
        "activation_rate",
        "retention_d1",
        "errors_per_1k",
        "latency_p95",
        "cost_per_day",
    ]
    custom = [k for k in _METRIC_RESOLVERS if k not in builtin]
    return builtin + custom


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 4. INBOX QUERIES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def inbox_pending() -> List[Dict[str, Any]]:
    """Trials where survived is None, sorted by check_at ascending."""
    trials = load_all_trials()
    pending = [t for t in trials if t.get("survived") is None and not t.get("reverted")]
    pending.sort(key=lambda t: t.get("check_at", ""))
    return pending


def inbox_needs_review() -> List[Dict[str, Any]]:
    """Trials where survived == False, newest first."""
    trials = load_all_trials()
    needs = [t for t in trials if t.get("survived") is False]
    needs.sort(key=lambda t: t.get("checked_at", ""), reverse=True)
    return needs


def inbox_completed() -> List[Dict[str, Any]]:
    """Trials where survived == True, newest first."""
    trials = load_all_trials()
    done = [t for t in trials if t.get("survived") is True]
    done.sort(key=lambda t: t.get("checked_at", ""), reverse=True)
    return done


def inbox_counts() -> Dict[str, int]:
    """Quick counts for all three tabs."""
    trials = load_all_trials()
    pending = 0
    needs_review = 0
    completed = 0
    reverted = 0
    for t in trials:
        survived = t.get("survived")
        is_reverted = bool(t.get("reverted"))
        if survived is None and not is_reverted:
            pending += 1
        if survived is False:
            needs_review += 1
        if survived is True:
            completed += 1
        if is_reverted:
            reverted += 1
    return {
        "pending": pending,
        "needs_review": needs_review,
        "completed": completed,
        "reverted": reverted,
        "total": len(trials),
    }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 5. REVERT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def revert_trial(
    trial_id: str, created_by: str = "operator"
) -> Optional[Dict[str, Any]]:
    """
    Mark trial as reverted. Creates a new 'revert' trial automatically.
    """
    trial = get_trial(trial_id)
    if not trial:
        return None

    updated = update_trial(trial_id, {"reverted": True}, reason="trial_reverted")

    # Create a follow-up revert trial
    revert = new_trial(
        created_by=created_by,
        context=trial.get("context", ""),
        action=f"REVERT: {trial.get('action', 'unknown')}",
        metric_name=trial.get("metric_name", "conversion_rate"),
        check_after_sec=trial.get("check_after_sec", 300),
        expected_delta=0,
        tags=["revert"] + trial.get("tags", []),
        notes=f"Auto-created revert trial for {trial_id}",
    )

    return {"reverted_trial": updated, "revert_trial": revert}


def add_note(trial_id: str, note: str) -> Optional[Dict[str, Any]]:
    """Append a note to an existing trial."""
    trial = get_trial(trial_id)
    if not trial:
        return None
    existing = trial.get("notes") or ""
    sep = "\n---\n" if existing else ""
    new_notes = existing + sep + f"[{_now_iso()}] {note}"
    return update_trial(trial_id, {"notes": new_notes}, reason="note_added")


def create_followup(
    trial_id: str, created_by: str = "operator", **overrides
) -> Optional[Dict[str, Any]]:
    """Create a follow-up trial pre-filled from an existing trial."""
    trial = get_trial(trial_id)
    if not trial:
        return None
    return new_trial(
        created_by=created_by,
        context=overrides.get("context", trial.get("context", "")),
        action=overrides.get("action", f"Follow-up: {trial.get('action', '')}"),
        metric_name=overrides.get(
            "metric_name", trial.get("metric_name", "conversion_rate")
        ),
        check_after_sec=overrides.get(
            "check_after_sec", trial.get("check_after_sec", 300)
        ),
        expected_delta=overrides.get("expected_delta", trial.get("expected_delta")),
        tags=overrides.get("tags", ["followup"] + trial.get("tags", [])),
        notes=overrides.get("notes", f"Follow-up from trial {trial_id}"),
    )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 6. SURVIVAL SCORING & RANKING
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def compute_survival_scores() -> Dict[str, Dict[str, Any]]:
    """
    Compute survival score per (action_template, context_tag) pair.
    Uses Laplace smoothing: (survived+1) / (survived+failed+2)
    """
    trials = load_all_trials()
    buckets: Dict[str, Dict[str, int]] = {}

    for t in trials:
        if t.get("survived") is None:
            continue  # skip unchecked
        # Build bucket key from action first word + first tag
        action_template = (
            t.get("action", "").split(":")[0].strip() or "unknown"
        ).lower()
        tags = t.get("tags", [])
        tag = tags[0] if tags else "untagged"
        key = f"{action_template}|{tag}"

        if key not in buckets:
            buckets[key] = {"survived": 0, "failed": 0}
        if t["survived"]:
            buckets[key]["survived"] += 1
        else:
            buckets[key]["failed"] += 1

    scores = {}
    for key, counts in buckets.items():
        s = counts["survived"]
        f = counts["failed"]
        # Laplace smoothing
        score = round((s + 1) / (s + f + 2), 4)
        scores[key] = {
            "survival_rate": score,
            "survived_count": s,
            "failed_count": f,
            "total": s + f,
            "action_template": key.split("|")[0],
            "tag": key.split("|")[1] if "|" in key else "untagged",
        }

    # Persist
    try:
        _SCORES_FILE.write_text(json.dumps(scores, indent=2), encoding="utf-8")
    except Exception:
        pass

    return scores


def rank_suggestions(suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank a list of suggestion dicts by survival score.
    Each suggestion should have 'action' and optionally 'tags'.
    High survival first. Bottom quartile marked as low-confidence.
    """
    scores = compute_survival_scores()

    def _score_for(suggestion: Dict) -> float:
        action = (
            suggestion.get("action", "").split(":")[0].strip() or "unknown"
        ).lower()
        tags = suggestion.get("tags", [])
        tag = tags[0] if tags else "untagged"
        key = f"{action}|{tag}"
        s = scores.get(key)
        if s:
            return s["survival_rate"]
        return 0.5  # prior with no data

    for s in suggestions:
        s["_survival_score"] = _score_for(s)

    suggestions.sort(key=lambda x: x["_survival_score"], reverse=True)

    # Mark bottom quartile
    if len(suggestions) >= 4:
        cutoff = len(suggestions) * 3 // 4
        for i, s in enumerate(suggestions):
            s["_low_confidence"] = i >= cutoff
    else:
        for s in suggestions:
            s["_low_confidence"] = False

    return suggestions


def get_survival_leaderboard(limit: int = 20) -> List[Dict[str, Any]]:
    """Return top survival scores, sorted by rate descending."""
    scores = compute_survival_scores()
    items = list(scores.values())
    items.sort(key=lambda x: x["survival_rate"], reverse=True)
    return items[:limit]


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 7. AUDIT TRAIL
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def get_audit_trail(
    trial_id: Optional[str] = None, tail: int = 50
) -> List[Dict[str, Any]]:
    """Read audit events. Optionally filter by trial_id."""
    all_events = _read_jsonl(_AUDIT_FILE)
    if trial_id:
        all_events = [e for e in all_events if e.get("trial_id") == trial_id]
    return all_events[-tail:]
