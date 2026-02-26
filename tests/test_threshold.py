# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
tests/test_threshold.py — Threshold Layer Tests

Validates activation gates and threshold checks (QUARANTINE, rank, budget, rate).
"""

from core.threshold import (
    ThresholdLayer,
    check_threshold,
    check_quarantine,
    check_rank_progression,
    evaluate,
)


def test_check_threshold_crossed():
    """Threshold crossed should return crossed=True."""
    layer = ThresholdLayer()
    
    result = layer.check_threshold(15, "rank_d_to_c")  # >= 10 missions
    
    assert result.crossed
    assert result.current == 15
    assert result.limit == 10.0
    assert result.rule_name == "rank_d_to_c"


def test_check_threshold_not_crossed():
    """Below threshold should return crossed=False."""
    layer = ThresholdLayer()
    
    result = layer.check_threshold(5, "rank_d_to_c")  # < 10 missions
    
    assert not result.crossed
    assert result.current == 5


def test_check_threshold_min_samples():
    """Threshold with min_samples should require sufficient data."""
    layer = ThresholdLayer()
    
    # Insufficient samples
    result1 = layer.check_threshold(
        0.2,  # Below 0.30
        "quarantine",
        context={"sample_count": 5},  # < 10 min_samples
    )
    
    assert not result1.crossed
    assert "insufficient" in result1.reason.lower()
    
    # Sufficient samples
    result2 = layer.check_threshold(
        0.2,
        "quarantine",
        context={"sample_count": 15},  # >= 10 min_samples
    )
    
    assert result2.crossed  # success_rate < 0.30


def test_check_threshold_operators():
    """Should support gt, gte, lt, lte, eq, neq operators."""
    layer = ThresholdLayer()
    
    # Manually add test rules
    layer.thresholds["test_gt"] = {"operator": "gt", "value": 10.0}
    layer.thresholds["test_lte"] = {"operator": "lte", "value": 100.0}
    
    assert layer.check_threshold(15, "test_gt").crossed  # 15 > 10
    assert not layer.check_threshold(10, "test_gt").crossed  # 10 !> 10
    assert layer.check_threshold(100, "test_lte").crossed  # 100 <= 100
    assert not layer.check_threshold(101, "test_lte").crossed  # 101 !<= 100


def test_check_quarantine():
    """QUARANTINE check with min_samples guard."""
    # Below threshold, insufficient samples
    result1 = check_quarantine(success_rate=0.25, mission_count=5)
    assert not result1.crossed
    
    # Below threshold, sufficient samples
    result2 = check_quarantine(success_rate=0.25, mission_count=15)
    assert result2.crossed
    
    # Above threshold
    result3 = check_quarantine(success_rate=0.80, mission_count=20)
    assert not result3.crossed


def test_check_rank_progression():
    """Should return next rank when threshold crossed."""
    # E → D after 1 mission
    assert check_rank_progression(1, "E") == "D"
    assert check_rank_progression(0, "E") is None
    
    # D → C after 10 missions
    assert check_rank_progression(10, "D") == "C"
    assert check_rank_progression(9, "D") is None
    
    # B → A after 100 missions
    assert check_rank_progression(100, "B") == "A"
    assert check_rank_progression(99, "B") is None
    
    # S has no next rank
    assert check_rank_progression(1000, "S") is None


def test_evaluate_budget_fail():
    """Budget check should fail when budget <= 0."""
    action = {}
    context = {"budget_remaining": -10.0}
    
    result = evaluate(action, context)
    
    assert not result.passed
    assert result.layer == "threshold"
    assert "budget" in result.reason.lower()


def test_evaluate_rate_limit_fail():
    """Rate limit check should fail when exceeded."""
    action = {}
    context = {"requests_per_minute": 150}  # > 120 limit
    
    result = evaluate(action, context)
    
    assert not result.passed
    assert "rate limit" in result.reason.lower()


def test_evaluate_all_pass():
    """All threshold checks passing should return pass."""
    action = {}
    context = {
        "budget_remaining": 100.0,
        "requests_per_minute": 50,
    }
    
    result = evaluate(action, context)
    
    assert result.passed
    assert result.layer == "threshold"
    assert result.metadata["checks_performed"] == 2


def test_evaluate_no_checks():
    """No threshold checks should return pass."""
    action = {}
    context = {}
    
    result = evaluate(action, context)
    
    assert result.passed
    assert result.metadata["checks_performed"] == 0


def test_threshold_config_persistence():
    """Threshold layer should persist config on first load."""
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "thresholds.json"
        layer = ThresholdLayer(thresholds_path=config_path)
        
        assert config_path.exists()
        assert "quarantine" in layer.thresholds
        assert layer.thresholds["quarantine"]["value"] == 0.30


def test_unknown_threshold_rule():
    """Unknown rule should return not crossed."""
    layer = ThresholdLayer()
    
    result = layer.check_threshold(100, "nonexistent_rule")
    
    assert not result.crossed
    assert "unknown" in result.reason.lower()
