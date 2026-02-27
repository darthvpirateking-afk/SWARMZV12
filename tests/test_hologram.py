# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Tests for the Hologram Evolution Ladder system.

Tests cover: XP computation, level detection, power currencies,
powers per level, effects, burst mode, drift detection, suggestions.
"""

import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

# Ensure project root on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _make_trial(
    trial_id="t1",
    checked=True,
    survived=True,
    metric_before=0.5,
    metric_after=0.6,
    expected_delta=0.1,
    metric_name="conversion_rate",
    action="deploy feature X",
    context="onboarding",
    tags=None,
    reverted=False,
    created_days_ago=0,
):
    """Create a minimal trial dict for testing."""
    now = datetime.now(timezone.utc)
    created = now - timedelta(days=created_days_ago)
    return {
        "id": trial_id,
        "created_at": created.isoformat(),
        "created_by": "test",
        "context": context,
        "action": action,
        "metric_name": metric_name,
        "metric_before": metric_before,
        "expected_delta": expected_delta,
        "check_after_sec": 300,
        "check_at": (created + timedelta(seconds=300)).isoformat(),
        "checked_at": (
            (created + timedelta(seconds=350)).isoformat() if checked else None
        ),
        "metric_after": metric_after if checked else None,
        "survived": survived if checked else None,
        "reverted": reverted,
        "notes": "",
        "tags": tags or ["growth"],
        "evidence": {},
    }


def _make_trials(
    n, metric_names=None, tags=None, survived_ratio=1.0, context="onboarding"
):
    """Generate n trials."""
    metric_names = metric_names or ["conversion_rate"]
    tags = tags or ["growth"]
    trials = []
    for i in range(n):
        metric = metric_names[i % len(metric_names)]
        tag = tags[i % len(tags)]
        survived = (i / n) < survived_ratio
        trials.append(
            _make_trial(
                trial_id=f"t{i}",
                checked=True,
                survived=survived,
                metric_name=metric,
                action=f"action_{i}: deploy step {i}",
                context=context,
                tags=[tag],
                created_days_ago=max(0, 10 - i),
            )
        )
    return trials


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 1. XP + LEVEL TESTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class TestXP:
    def test_xp_zero_no_trials(self):
        from core.hologram import compute_xp

        assert compute_xp([]) == 0

    def test_xp_counts_verified_only(self):
        from core.hologram import compute_xp

        trials = [
            _make_trial("t1", checked=True),
            _make_trial("t2", checked=False),
            _make_trial("t3", checked=True),
        ]
        assert compute_xp(trials) == 2

    def test_xp_all_verified(self):
        from core.hologram import compute_xp

        trials = _make_trials(10)
        assert compute_xp(trials) == 10


class TestLevel:
    def test_level_0_egg(self):
        from core.hologram import compute_level

        trials = _make_trials(3)
        state = compute_level(trials)
        assert state["level"] == 0
        assert state["name"] == "EGG"

    def test_level_1_rookie(self):
        from core.hologram import compute_level

        trials = _make_trials(5)
        state = compute_level(trials)
        assert state["level"] == 1
        assert state["name"] == "ROOKIE"

    def test_level_2_champion(self):
        from core.hologram import compute_level

        # Need â‰¥20 verified + â‰¥5 per metric
        # With 2 metrics, 25 trials = 12-13 each â‰¥ 5
        trials = _make_trials(25, metric_names=["conversion_rate", "activation_rate"])
        state = compute_level(trials)
        assert state["level"] == 2
        assert state["name"] == "CHAMPION"

    def test_level_2_blocked_insufficient_per_metric(self):
        from core.hologram import compute_level

        # 20 trials but 19 in one metric, 1 in another â†’ min_per_metric = 1 < 5
        trials = _make_trials(20, metric_names=["a"])
        trials.append(_make_trial("t_extra", metric_name="b"))
        state = compute_level(trials)
        # min per metric = 1 (for "b"), so not champion
        assert state["level"] == 1  # Rookie

    def test_level_3_ultimate(self):
        from core.hologram import compute_level

        # Need â‰¥60 verified + â‰¥20 in same context_tag
        # 70 trials, all same tag â†’ max_same_context_tag = 70 â‰¥ 20
        trials = _make_trials(70, metric_names=["a", "b"], tags=["growth"])
        state = compute_level(trials)
        assert state["level"] == 3
        assert state["name"] == "ULTIMATE"

    def test_level_3_blocked_insufficient_context_tag(self):
        from core.hologram import compute_level

        # 60 trials but spread across 5 tags = 12 each < 20
        trials = _make_trials(
            60, metric_names=["a", "b"], tags=["t1", "t2", "t3", "t4", "t5"]
        )
        state = compute_level(trials)
        assert state["level"] == 2  # Champion (60 trials, 30 each metric â‰¥ 5)

    def test_level_returns_powers(self):
        from core.hologram import compute_level

        trials = _make_trials(25, metric_names=["a", "b"])
        state = compute_level(trials)
        assert "powers" in state
        assert len(state["powers"]) == 2  # LV2 gets auto_baseline + auto_check
        assert state["powers"][0]["id"] == "auto_baseline"
        assert state["powers"][1]["id"] == "auto_check_scheduler"

    def test_level_returns_currencies(self):
        from core.hologram import compute_level

        trials = _make_trials(10)
        state = compute_level(trials)
        assert "currencies" in state
        assert "stability" in state["currencies"]
        assert "novelty" in state["currencies"]
        assert "reversibility" in state["currencies"]

    def test_level_returns_next_level(self):
        from core.hologram import compute_level

        trials = _make_trials(3)
        state = compute_level(trials)
        assert state["next_level"] is not None
        assert state["next_level"]["name"] == "ROOKIE"
        assert state["next_level"]["xp_needed"] == 5


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 2. POWER CURRENCIES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class TestCurrencies:
    def test_stability_all_survived(self):
        from core.hologram import compute_power_currencies, _verified_trials

        trials = _make_trials(10, survived_ratio=1.0)
        verified = _verified_trials(trials)
        cur = compute_power_currencies(verified)
        assert cur["stability"] == 1.0

    def test_stability_half_survived(self):
        from core.hologram import compute_power_currencies, _verified_trials

        trials = _make_trials(10, survived_ratio=0.5)
        verified = _verified_trials(trials)
        cur = compute_power_currencies(verified)
        assert 0.4 <= cur["stability"] <= 0.6

    def test_stability_empty(self):
        from core.hologram import compute_power_currencies

        cur = compute_power_currencies([])
        assert cur["stability"] == 0.0

    def test_reversibility_with_reverts(self):
        from core.hologram import compute_power_currencies

        trials = _make_trials(10)
        # Mark 3 as reverted
        for i in range(3):
            trials[i]["reverted"] = True
        cur = compute_power_currencies(trials)
        assert cur["reversibility"] == 0.3

    def test_novelty_zero_no_recent(self):
        from core.hologram import compute_power_currencies

        # All trials created 60 days ago (outside 30d window)
        trials = []
        for i in range(5):
            trials.append(_make_trial(f"t{i}", checked=True, created_days_ago=60))
        cur = compute_power_currencies(trials)
        # No recent trials â†’ novelty = 0
        assert cur["novelty"] == 0.0


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 3. POWERS PER LEVEL
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class TestPowers:
    def test_no_powers_lv0(self):
        from core.hologram import _powers_for_level

        powers = _powers_for_level(0)
        assert len(powers) == 0

    def test_one_power_lv1(self):
        from core.hologram import _powers_for_level

        powers = _powers_for_level(1)
        assert len(powers) == 1
        assert powers[0]["id"] == "auto_baseline"

    def test_cumulative_powers_lv3(self):
        from core.hologram import _powers_for_level

        powers = _powers_for_level(3)
        assert len(powers) == 3
        ids = [p["id"] for p in powers]
        assert "auto_baseline" in ids
        assert "auto_check_scheduler" in ids
        assert "survival_ranking" in ids

    def test_all_powers_lv5(self):
        from core.hologram import _powers_for_level

        powers = _powers_for_level(5)
        assert len(powers) == 5


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 4. VISUAL EFFECTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class TestEffects:
    def test_effects_default(self):
        from core.hologram import compute_effects

        effects = compute_effects(None, 0)
        assert effects["glow_intensity"] == 0.0
        assert effects["scanlines"] is False
        assert effects["level_name"] == "EGG"

    def test_effects_survived_trial(self):
        from core.hologram import compute_effects

        trial = _make_trial(
            "t1", survived=True, metric_before=0.5, metric_after=0.6, expected_delta=0.1
        )
        effects = compute_effects(trial, 1)
        assert effects["glow_intensity"] == 1.0  # |0.1| / |0.1| = 1.0
        assert effects["flicker_rate"] == 0.0

    def test_effects_failed_trial_flicker(self):
        from core.hologram import compute_effects

        trial = _make_trial(
            "t1",
            survived=False,
            metric_before=0.5,
            metric_after=0.4,
            expected_delta=0.1,
        )
        effects = compute_effects(trial, 1)
        assert effects["flicker_rate"] == 0.6

    def test_effects_scanlines_lv2(self):
        from core.hologram import compute_effects

        effects = compute_effects(None, 2)
        assert effects["scanlines"] is True

    def test_effects_overclock_lv5(self):
        from core.hologram import compute_effects

        effects = compute_effects(None, 5)
        assert effects["overclock"] is True


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 5. VERDICT BADGE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class TestVerdict:
    def test_survived_badge(self):
        from core.hologram import _verdict_badge

        trial = _make_trial(survived=True)
        badge = _verdict_badge(trial)
        assert badge["status"] == "survived"
        assert badge["color"] == "mint"

    def test_failed_badge(self):
        from core.hologram import _verdict_badge

        trial = _make_trial(survived=False)
        badge = _verdict_badge(trial)
        assert badge["status"] == "failed"
        assert badge["color"] == "red"

    def test_reverted_badge(self):
        from core.hologram import _verdict_badge

        trial = _make_trial(reverted=True)
        badge = _verdict_badge(trial)
        assert badge["status"] == "reverted"
        assert badge["color"] == "amber"

    def test_pending_badge(self):
        from core.hologram import _verdict_badge

        trial = _make_trial(checked=False)
        badge = _verdict_badge(trial)
        assert badge["status"] == "pending"
        assert badge["color"] == "cyan"


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 6. DELTA GRAPH
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class TestDeltaGraph:
    def test_delta_graph_has_points(self):
        from core.hologram import _build_delta_graph

        trial = _make_trial(metric_before=0.5, metric_after=0.6, expected_delta=0.1)
        graph = _build_delta_graph(trial)
        assert graph["metric_name"] == "conversion_rate"
        assert len(graph["points"]) == 3  # baseline, expected, after
        assert graph["baseline"] == 0.5
        assert graph["actual"] == 0.6

    def test_delta_graph_no_expected(self):
        from core.hologram import _build_delta_graph

        trial = _make_trial(expected_delta=None)
        graph = _build_delta_graph(trial)
        assert len(graph["points"]) == 2  # baseline and after only
        assert graph["target"] is None


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 7. WHY FAILED HINT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class TestWhyFailed:
    def test_shortfall_hint(self):
        from core.hologram import _why_failed_hint

        trial = _make_trial(
            survived=False, metric_before=0.5, metric_after=0.52, expected_delta=0.1
        )
        hint = _why_failed_hint(trial)
        assert "short" in hint.lower() or "shortfall" in hint.lower()

    def test_worsened_hint(self):
        from core.hologram import _why_failed_hint

        trial = _make_trial(
            survived=False, metric_before=0.5, metric_after=0.4, expected_delta=None
        )
        hint = _why_failed_hint(trial)
        assert "worsened" in hint.lower()


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 8. DRIFT DETECTION
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class TestDrift:
    def test_drift_insufficient_data(self):
        from core.hologram import detect_drift

        with patch("core.hologram.load_all_trials", return_value=[]):
            result = detect_drift("conversion_rate", "ctx")
            assert result["drift"] is False
            assert "insufficient" in result["reason"]

    def test_drift_detection_with_data(self):
        from core.hologram import detect_drift

        # Build trials with clear drift: older ~0.5, recent ~0.9
        now = datetime.now(timezone.utc)
        older_trials = []
        for i in range(10):
            t = _make_trial(
                f"old_{i}",
                metric_name="conv",
                metric_after=0.5 + (i * 0.001),
                context="ctx",
                created_days_ago=20,
            )
            t["checked_at"] = (now - timedelta(days=20)).isoformat()
            older_trials.append(t)
        recent_trials = []
        for i in range(5):
            t = _make_trial(
                f"new_{i}",
                metric_name="conv",
                metric_after=0.9 + (i * 0.001),
                context="ctx",
                created_days_ago=2,
            )
            t["checked_at"] = (now - timedelta(days=2)).isoformat()
            recent_trials.append(t)

        all_trials = older_trials + recent_trials

        with (
            patch("core.hologram.load_all_trials", return_value=all_trials),
            patch("core.hologram._append_drift_event"),
        ):
            result = detect_drift("conv", "ctx", window_days=7)
            assert result["drift"] is True
            assert result["drift_magnitude"] > 1.5


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 9. BURST MODE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class TestBurstMode:
    def setup_method(self):
        """Use temp dir for hologram data."""
        self._tmpdir = tempfile.mkdtemp()
        self._orig_holo_dir = None

    def teardown_method(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_burst_toggle_requires_lv4(self):
        from core.hologram import toggle_burst_mode

        # Mock compute_level to return LV1
        with patch(
            "core.hologram.compute_level",
            return_value={"level": 1, "currencies": {"reversibility": 0.5}},
        ):
            result = toggle_burst_mode(True)
            assert result["ok"] is False
            assert "LV4" in result["error"]

    def test_burst_toggle_requires_reversibility(self):
        from core.hologram import toggle_burst_mode

        with (
            patch(
                "core.hologram.compute_level",
                return_value={"level": 4, "currencies": {"reversibility": 0.0}},
            ),
            patch("core.hologram._load_state", return_value={}),
        ):
            result = toggle_burst_mode(True)
            assert result["ok"] is False
            assert "reversibility" in result["error"].lower()

    def test_burst_batch_requires_enabled(self):
        from core.hologram import create_burst_batch

        with patch("core.hologram._burst_enabled", return_value=False):
            result = create_burst_batch([{"action": "test"}] * 5)
            assert result["ok"] is False
            assert "not enabled" in result["error"].lower()

    def test_burst_batch_min_trials(self):
        from core.hologram import create_burst_batch

        with patch("core.hologram._burst_enabled", return_value=True):
            result = create_burst_batch([{"action": "test"}] * 2)
            assert result["ok"] is False
            assert "3" in result["error"]

    def test_burst_batch_min_budget(self):
        from core.hologram import create_burst_batch

        with patch("core.hologram._burst_enabled", return_value=True):
            result = create_burst_batch([{"action": "test"}] * 5, budget_sec=30)
            assert result["ok"] is False
            assert "60" in result["error"]


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 10. SUGGEST FOLLOWUPS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class TestSuggestions:
    def test_suggest_empty_scores(self):
        from core.hologram import suggest_best_followups

        with patch("core.hologram.compute_survival_scores", return_value={}):
            results = suggest_best_followups("ctx")
            assert len(results) == 0

    def test_suggest_returns_sorted(self):
        from core.hologram import suggest_best_followups

        scores = {
            "high|g": {
                "action_template": "high",
                "tag": "g",
                "survival_rate": 0.9,
                "survived_count": 9,
                "failed_count": 1,
            },
            "low|g": {
                "action_template": "low",
                "tag": "g",
                "survival_rate": 0.3,
                "survived_count": 3,
                "failed_count": 7,
            },
        }
        with patch("core.hologram.compute_survival_scores", return_value=scores):
            results = suggest_best_followups("", limit=5)
            assert len(results) == 2
            assert results[0]["survival_rate"] == 0.9
            assert results[1]["survival_rate"] == 0.3
            assert results[1]["low_confidence"] is True


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# 11. LEVELS INFO
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class TestLevelsInfo:
    def test_six_levels_defined(self):
        from core.hologram import LEVELS

        assert len(LEVELS) == 6

    def test_levels_ordered(self):
        from core.hologram import LEVELS

        for i, lv in enumerate(LEVELS):
            assert lv["level"] == i
