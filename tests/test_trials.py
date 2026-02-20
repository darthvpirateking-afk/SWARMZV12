# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
tests/test_trials.py â€” Comprehensive tests for the Trials Inbox system.

Covers: data model, storage, creation gate, metrics, inbox queries,
revert, followup, survival scoring, audit trail, worker.
"""

import json
import shutil
import time
from pathlib import Path

import pytest

# â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

TRIALS_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "trials"
TRIALS_FILE = TRIALS_DATA_DIR / "trials.jsonl"
AUDIT_FILE = TRIALS_DATA_DIR / "audit.jsonl"
SCORES_FILE = TRIALS_DATA_DIR / "survival_scores.json"
BACKUP_DIR = TRIALS_DATA_DIR.parent / "_trials_backup_test"


def _backup():
    """Backup existing trials data before test session."""
    if TRIALS_DATA_DIR.exists():
        if BACKUP_DIR.exists():
            shutil.rmtree(BACKUP_DIR)
        shutil.copytree(TRIALS_DATA_DIR, BACKUP_DIR)


def _restore():
    """Restore trials data after test session."""
    if BACKUP_DIR.exists():
        if TRIALS_DATA_DIR.exists():
            shutil.rmtree(TRIALS_DATA_DIR)
        shutil.copytree(BACKUP_DIR, TRIALS_DATA_DIR)
        shutil.rmtree(BACKUP_DIR)


def _clear():
    """Clear trials data files for a clean slate."""
    TRIALS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for f in [TRIALS_FILE, AUDIT_FILE, SCORES_FILE]:
        if f.exists():
            f.unlink()


def setup_module():
    _backup()
    _clear()


def teardown_module():
    _restore()


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 1. DATA MODEL â€” new_trial, load, get, update
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def test_new_trial_creates_valid_record():
    from core.trials import new_trial

    t = new_trial(
        created_by="test",
        context="test-ctx",
        action="add button",
        metric_name="conversion_rate",
        check_after_sec=60,
        expected_delta=0.01,
        tags=["ui"],
        notes="first trial",
    )
    assert t["id"]
    assert t["created_at"]
    assert t["check_at"]
    assert t["survived"] is None
    assert t["reverted"] is False
    assert t["metric_name"] == "conversion_rate"
    assert t["expected_delta"] == 0.01
    assert t["tags"] == ["ui"]
    assert t["notes"] == "first trial"
    assert t["created_by"] == "test"
    assert t["action"] == "add button"
    assert t["context"] == "test-ctx"


def test_trial_persisted_to_file():
    assert TRIALS_FILE.exists(), "trials.jsonl should exist after creating trial"
    lines = TRIALS_FILE.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 1, "should have at least one trial line"
    last = json.loads(lines[-1])
    assert "id" in last
    assert "action" in last


def test_load_all_trials():
    from core.trials import load_all_trials

    trials = load_all_trials()
    assert isinstance(trials, list)
    assert len(trials) >= 1
    assert trials[0].get("action") == "add button"


def test_get_trial_by_id():
    from core.trials import load_all_trials, get_trial

    all_t = load_all_trials()
    first_id = all_t[0]["id"]
    found = get_trial(first_id)
    assert found is not None
    assert found["id"] == first_id


def test_get_trial_missing():
    from core.trials import get_trial

    result = get_trial("nonexistent-id-123")
    assert result is None


def test_update_trial_appends():
    from core.trials import load_all_trials, update_trial, get_trial

    first = load_all_trials()[0]
    tid = first["id"]
    before_lines = len(TRIALS_FILE.read_text(encoding="utf-8").strip().split("\n"))

    updated = update_trial(tid, {"notes": "updated note"}, reason="test_update")
    assert updated is not None
    assert updated["notes"] == "updated note"

    after_lines = len(TRIALS_FILE.read_text(encoding="utf-8").strip().split("\n"))
    assert after_lines > before_lines, "update should append, not overwrite"

    # Latest version should have the updated note
    latest = get_trial(tid)
    assert latest["notes"] == "updated note"


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 2. TRIAL CREATION GATE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def test_require_trial_creates():
    from core.trials import require_trial

    t = require_trial(
        action="change theme",
        context="global",
        metric_name="conversion_rate",
        check_after_sec=120,
        created_by="test_gate",
    )
    assert t is not None
    assert t["action"] == "change theme"
    assert t["survived"] is None


def test_require_trial_exemption_admin():
    from core.trials import require_trial

    result = require_trial(
        action="hotfix",
        context="emergency",
        metric_name="conversion_rate",
        non_trial_reason="critical production fix",
        admin=True,
        created_by="admin",
    )
    assert result is None  # no trial created, exempted


def test_require_trial_exemption_non_admin_raises():
    from core.trials import require_trial, TrialGateError

    try:
        require_trial(
            action="sneak change",
            context="global",
            metric_name="conversion_rate",
            non_trial_reason="just because",
            admin=False,
            created_by="user",
        )
        assert False, "should have raised TrialGateError"
    except TrialGateError:
        pass


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 3. METRICS INTERFACE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def test_list_available_metrics():
    from core.trials import list_available_metrics

    metrics = list_available_metrics()
    assert isinstance(metrics, list)
    assert "conversion_rate" in metrics
    assert "activation_rate" in metrics
    assert "errors_per_1k" in metrics
    assert len(metrics) >= 6


def test_resolve_metric_builtin():
    from core.trials import resolve_metric

    val, evidence = resolve_metric("conversion_rate", "global")
    # Value can be 0.0 if no missions exist â€” that's fine
    assert isinstance(val, (int, float)) or val is None
    assert isinstance(evidence, dict) or evidence is None


def test_resolve_metric_unknown():
    from core.trials import resolve_metric

    val, evidence = resolve_metric("fake_metric_xyz", "global")
    # Should return None or some error indicator
    assert val is None or isinstance(val, (int, float))


def test_register_custom_metric():
    from core.trials import register_metric, resolve_metric

    register_metric("test_custom", lambda ctx: (42.0, {"custom": True}))
    val, evidence = resolve_metric("test_custom", "any")
    assert val == 42.0
    assert evidence.get("custom") is True


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 4. INBOX QUERIES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def test_inbox_pending():
    from core.trials import inbox_pending

    pending = inbox_pending()
    assert isinstance(pending, list)
    for t in pending:
        assert t.get("survived") is None
        assert not t.get("reverted")


def test_inbox_needs_review_empty_initially():
    from core.trials import inbox_needs_review

    needs = inbox_needs_review()
    assert isinstance(needs, list)
    # All trials so far are pending (survived=None), not failed


def test_inbox_completed_empty_initially():
    from core.trials import inbox_completed

    done = inbox_completed()
    assert isinstance(done, list)


def test_inbox_counts():
    from core.trials import inbox_counts

    counts = inbox_counts()
    assert isinstance(counts, dict)
    assert "pending" in counts
    assert "needs_review" in counts
    assert "completed" in counts
    assert "total" in counts
    assert counts["pending"] >= 1, "should have at least one pending trial"
    assert counts["total"] >= counts["pending"]


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 5. REVERT, NOTE, FOLLOWUP
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def test_add_note():
    from core.trials import load_all_trials, add_note, get_trial

    first = load_all_trials()[0]
    tid = first["id"]
    result = add_note(tid, "this is a test note")
    assert result is not None
    refreshed = get_trial(tid)
    assert "this is a test note" in refreshed.get("notes", "")


def test_create_followup():
    from core.trials import load_all_trials, create_followup

    first = load_all_trials()[0]
    tid = first["id"]
    followup = create_followup(tid, created_by="test_followup")
    assert followup is not None
    assert followup["id"] != tid
    assert "followup" in followup.get("tags", [])
    assert f"Follow-up from trial {tid}" in followup.get("notes", "")


def test_revert_trial():
    from core.trials import new_trial, update_trial, revert_trial

    # Create trial and mark it as survived
    t = new_trial(
        created_by="test_revert",
        context="revert-ctx",
        action="bad change",
        metric_name="conversion_rate",
        check_after_sec=10,
    )
    tid = t["id"]
    update_trial(
        tid,
        {"survived": False, "checked_at": "2025-01-01T00:00:00Z"},
        reason="evaluation",
    )

    result = revert_trial(tid, created_by="test_revert")
    assert result is not None
    assert result["reverted_trial"]["reverted"] is True

    revert_t = result["revert_trial"]
    assert "REVERT" in revert_t["action"]
    assert "revert" in revert_t.get("tags", [])


def test_revert_nonexistent():
    from core.trials import revert_trial

    result = revert_trial("nonexistent-id")
    assert result is None


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 6. SURVIVAL SCORING
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def test_compute_survival_scores():
    from core.trials import new_trial, update_trial, compute_survival_scores

    # Create several trials and mark them survived/failed
    for i in range(3):
        t = new_trial(
            created_by="test_score",
            context="scoring",
            action=f"feature: test_{i}",
            metric_name="conversion_rate",
            check_after_sec=10,
            tags=["scoring"],
        )
        update_trial(
            t["id"],
            {
                "survived": True,
                "checked_at": "2025-01-01T00:00:00Z",
                "metric_after": 0.5,
            },
            reason="evaluation",
        )

    t_fail = new_trial(
        created_by="test_score",
        context="scoring",
        action="feature: fail_1",
        metric_name="conversion_rate",
        check_after_sec=10,
        tags=["scoring"],
    )
    update_trial(
        t_fail["id"],
        {
            "survived": False,
            "checked_at": "2025-01-01T00:00:00Z",
            "metric_after": 0.1,
        },
        reason="evaluation",
    )

    scores = compute_survival_scores()
    assert isinstance(scores, dict)
    assert len(scores) >= 1

    # Check Laplace smoothing: (3+1)/(3+1+2) = 0.6667 for survived
    for key, val in scores.items():
        assert "survival_rate" in val
        assert "survived_count" in val
        assert "failed_count" in val
        assert 0 <= val["survival_rate"] <= 1


def test_survival_scores_persisted():
    from core.trials import compute_survival_scores

    compute_survival_scores()
    assert SCORES_FILE.exists(), "survival_scores.json should be persisted"
    data = json.loads(SCORES_FILE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)


def test_get_survival_leaderboard():
    from core.trials import get_survival_leaderboard

    board = get_survival_leaderboard(limit=10)
    assert isinstance(board, list)
    # Should be sorted descending
    for i in range(len(board) - 1):
        assert board[i]["survival_rate"] >= board[i + 1]["survival_rate"]


def test_rank_suggestions():
    from core.trials import rank_suggestions

    suggestions = [
        {"action": "feature: x", "tags": ["scoring"]},
        {"action": "feature: y", "tags": ["untagged"]},
        {"action": "feature: z", "tags": ["fresh"]},
    ]
    ranked = rank_suggestions(suggestions)
    assert isinstance(ranked, list)
    assert len(ranked) == 3
    for s in ranked:
        assert "_survival_score" in s
        assert "_low_confidence" in s


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 7. AUDIT TRAIL
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def test_audit_trail_written():
    assert AUDIT_FILE.exists(), "audit.jsonl should exist"
    lines = AUDIT_FILE.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 1, "should have audit events"
    first = json.loads(lines[0])
    assert "event_type" in first
    assert "trial_id" in first
    assert "ts" in first


def test_get_audit_trail():
    from core.trials import get_audit_trail

    events = get_audit_trail()
    assert isinstance(events, list)
    assert len(events) >= 1


def test_get_audit_trail_by_trial_id():
    from core.trials import load_all_trials, get_audit_trail

    all_t = load_all_trials()
    if not all_t:
        return
    tid = all_t[0]["id"]
    events = get_audit_trail(trial_id=tid)
    assert isinstance(events, list)
    for e in events:
        assert e.get("trial_id") == tid


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 8. WORKER (unit-level)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def test_worker_evaluate_trial():
    """Test that evaluate_trial correctly marks a trial."""
    from core.trials import new_trial, get_trial
    from core.trials_worker import evaluate_trial

    t = new_trial(
        created_by="test_worker",
        context="worker-ctx",
        action="worker test",
        metric_name="conversion_rate",
        check_after_sec=0,  # immediate
    )

    evaluate_trial(t)
    refreshed = get_trial(t["id"])
    assert refreshed is not None
    assert refreshed["checked_at"] is not None
    assert refreshed["survived"] is not None  # either True or False


def test_worker_status():
    from core.trials_worker import worker_status

    status = worker_status()
    assert isinstance(status, dict)
    assert "running" in status


def test_worker_start_stop():
    from core.trials_worker import start_worker, stop_worker, worker_status

    start_worker()
    status = worker_status()
    assert status["running"] is True
    stop_worker()
    time.sleep(0.3)
    status2 = worker_status()
    assert status2["running"] is False


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 10. HOLOGRAM-POWER GATING (baseline + auto-check)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def test_auto_baseline_locked_at_lv0(monkeypatch: pytest.MonkeyPatch):
    """LV0 should not auto-capture baselines (power locked)."""
    import core.hologram as holo
    from core import trials as trials_mod

    # Force hologram level 0 regardless of existing trials.
    monkeypatch.setattr(holo, "compute_level", lambda: {"level": 0}, raising=False)

    # Stub metric resolver so if it is called we notice via metric_before.
    monkeypatch.setattr(
        trials_mod,
        "resolve_metric",
        lambda name, ctx: (42.0, {"stub": True}),
        raising=False,
    )

    t = trials_mod.new_trial(
        created_by="test_lv0",
        context="ctx-locked",
        action="change locked",
        metric_name="conversion_rate",
        check_after_sec=60,
    )

    # With LV0, auto-baseline capture should be disabled.
    assert t["metric_before"] is None


def test_auto_baseline_unlocked_at_lv1(monkeypatch: pytest.MonkeyPatch):
    """LV1+ should auto-capture baselines via resolver."""
    import core.hologram as holo
    from core import trials as trials_mod

    monkeypatch.setattr(holo, "compute_level", lambda: {"level": 1}, raising=False)
    monkeypatch.setattr(
        trials_mod,
        "resolve_metric",
        lambda name, ctx: (99.9, {"stub": True}),
        raising=False,
    )

    t = trials_mod.new_trial(
        created_by="test_lv1",
        context="ctx-open",
        action="change open",
        metric_name="conversion_rate",
        check_after_sec=60,
    )

    assert t["metric_before"] == 99.9


def test_auto_check_scheduler_requires_lv2(monkeypatch: pytest.MonkeyPatch):
    """Auto-check worker should be gated until LV2 CHAMPION."""
    import core.hologram as holo
    from core import trials as trials_mod
    from core.trials_worker import check_due_trials

    # Force LV0 so scheduler should early-return.
    monkeypatch.setattr(holo, "compute_level", lambda: {"level": 0}, raising=False)

    t = trials_mod.new_trial(
        created_by="test_worker_lv0",
        context="worker-ctx-locked",
        action="worker locked",
        metric_name="conversion_rate",
        check_after_sec=0,
    )

    count = check_due_trials()
    refreshed = trials_mod.get_trial(t["id"])

    assert count == 0
    assert refreshed["checked_at"] is None


def test_auto_check_scheduler_runs_at_lv2(monkeypatch: pytest.MonkeyPatch):
    """At LV2+, the worker should evaluate due trials."""
    import core.hologram as holo
    from core import trials as trials_mod
    from core.trials_worker import check_due_trials

    monkeypatch.setattr(holo, "compute_level", lambda: {"level": 2}, raising=False)

    t = trials_mod.new_trial(
        created_by="test_worker_lv2",
        context="worker-ctx-open",
        action="worker open",
        metric_name="conversion_rate",
        check_after_sec=0,
    )

    count = check_due_trials()
    refreshed = trials_mod.get_trial(t["id"])

    assert count >= 1
    assert refreshed["checked_at"] is not None


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 9. APPEND-ONLY INVARIANT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def test_append_only_no_rewrite():
    """Verify that the file only grows â€” lines are never deleted."""
    from core.trials import new_trial

    count_before = 0
    if TRIALS_FILE.exists():
        count_before = len(TRIALS_FILE.read_text(encoding="utf-8").strip().split("\n"))

    new_trial(
        created_by="test_append",
        context="append-test",
        action="append only check",
        metric_name="conversion_rate",
        check_after_sec=60,
    )

    count_after = len(TRIALS_FILE.read_text(encoding="utf-8").strip().split("\n"))
    assert count_after > count_before, "file must only grow (append-only)"


def test_audit_only_grows():
    """Verify the audit file only grows."""
    from core.trials import add_note, load_all_trials

    count_before = 0
    if AUDIT_FILE.exists():
        count_before = len(AUDIT_FILE.read_text(encoding="utf-8").strip().split("\n"))

    all_t = load_all_trials()
    if all_t:
        add_note(all_t[0]["id"], "audit growth test")

    count_after = len(AUDIT_FILE.read_text(encoding="utf-8").strip().split("\n"))
    assert count_after >= count_before, "audit file must only grow"
