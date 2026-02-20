# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Trials Worker â€” Scheduler that evaluates trials on schedule.

Runs as a background thread. Checks every 30 seconds for trials
whose check_at has passed, resolves metrics, and evaluates survival.
All writes are append-only and audited.
"""

import time
import threading
from datetime import datetime, timezone
from typing import Optional

from core.trials import (
    load_all_trials,
    update_trial,
    resolve_metric,
    _audit_event,
    _now_iso,
    compute_survival_scores,
)


_WORKER_RUNNING = False
_WORKER_THREAD: Optional[threading.Thread] = None
_CHECK_INTERVAL_SEC = 30  # check every 30 seconds


def _parse_iso(ts: str) -> Optional[datetime]:
    """Parse ISO timestamp string to datetime. Fail-open returns None."""
    if not ts:
        return None
    try:
        # Handle both Z suffix and +00:00
        ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def evaluate_trial(trial: dict) -> Optional[dict]:
    """
    Evaluate a single trial:
    1. Resolve metric_after
    2. Compare with metric_before
    3. Determine survived
    4. Persist result

    Returns updated trial or None on failure.
    """
    trial_id = trial.get("id")
    if not trial_id:
        return None

    metric_name = trial.get("metric_name", "")
    context = trial.get("context", "")

    # Resolve current metric value
    try:
        metric_after, after_evidence = resolve_metric(metric_name, context)
    except Exception:
        metric_after = None
        after_evidence = {"error": "resolve_metric failed"}

    if metric_after is None:
        # Can't evaluate â€” skip this cycle, will retry next time
        _audit_event("evaluation_skipped", trial_id, {
            "reason": "metric_after is None",
            "metric_name": metric_name,
        })
        return None

    metric_before = trial.get("metric_before")
    expected_delta = trial.get("expected_delta")

    # If baseline was never captured, use current as baseline (no-op trial)
    if metric_before is None:
        metric_before = metric_after

    # Evaluate survival
    if expected_delta is not None:
        survived = metric_after >= (metric_before + expected_delta)
    else:
        # Default: must not worsen
        survived = metric_after >= metric_before

    now = _now_iso()
    updates = {
        "checked_at": now,
        "metric_after": metric_after,
        "metric_before": metric_before,  # persist if it was null before
        "survived": survived,
    }

    # Store evidence
    evidence = trial.get("evidence", {})
    evidence["evaluation"] = {
        "metric_after": metric_after,
        "after_evidence": after_evidence,
        "metric_before": metric_before,
        "expected_delta": expected_delta,
        "survived": survived,
        "evaluated_at": now,
    }
    updates["evidence"] = evidence

    result = update_trial(trial_id, updates, reason="trial_evaluated")

    _audit_event("trial_evaluated", trial_id, {
        "metric_before": metric_before,
        "metric_after": metric_after,
        "expected_delta": expected_delta,
        "survived": survived,
    })

    return result


def check_due_trials() -> int:
    """
    Find all trials where survived is None and check_at <= now.
    Evaluate each one. Returns count of trials evaluated.
    """
    # LV2 CHAMPION power: auto-check scheduler. Below LV2 we intentionally
    # skip automatic evaluation so trials must be checked manually.
    try:
        from core.hologram import compute_level  # type: ignore

        level_state = compute_level()
        if level_state.get("level", 0) < 2:
            _audit_event("auto_check_skipped_low_level", "SYSTEM", {
                "level": level_state.get("level", 0),
                "reason": "Auto-check scheduler unlocks at LV2 (CHAMPION)",
            })
            return 0
    except Exception:
        # If hologram is unavailable or misconfigured, fall back to
        # legacy behaviour and keep auto-check running.
        pass

    now = datetime.now(timezone.utc)
    trials = load_all_trials()
    evaluated = 0

    for trial in trials:
        # Skip already evaluated or reverted
        if trial.get("survived") is not None:
            continue
        if trial.get("reverted"):
            continue

        check_at = _parse_iso(trial.get("check_at", ""))
        if check_at is None:
            continue
        if check_at > now:
            continue  # not yet due

        result = evaluate_trial(trial)
        if result is not None:
            evaluated += 1

    # Recompute survival scores after evaluations
    if evaluated > 0:
        try:
            compute_survival_scores()
        except Exception:
            pass

    return evaluated


def _worker_loop():
    """Background loop that checks for due trials."""
    global _WORKER_RUNNING
    while _WORKER_RUNNING:
        try:
            count = check_due_trials()
            if count > 0:
                _audit_event("worker_cycle", "SYSTEM", {
                    "trials_evaluated": count,
                    "timestamp": _now_iso(),
                })
        except Exception:
            pass  # fail-open: never crash the worker
        time.sleep(_CHECK_INTERVAL_SEC)


def start_worker() -> bool:
    """Start the background trials worker. Returns True if started, False if already running."""
    global _WORKER_RUNNING, _WORKER_THREAD

    if _WORKER_RUNNING and _WORKER_THREAD and _WORKER_THREAD.is_alive():
        return False  # already running

    _WORKER_RUNNING = True
    _WORKER_THREAD = threading.Thread(target=_worker_loop, daemon=True, name="trials-worker")
    _WORKER_THREAD.start()
    return True


def stop_worker() -> None:
    """Stop the background worker."""
    global _WORKER_RUNNING
    _WORKER_RUNNING = False


def worker_status() -> dict:
    """Return worker status."""
    global _WORKER_RUNNING, _WORKER_THREAD
    return {
        "running": _WORKER_RUNNING and _WORKER_THREAD is not None and _WORKER_THREAD.is_alive(),
        "interval_sec": _CHECK_INTERVAL_SEC,
    }

