"""
Tests for Exploration Layer (P2.4)

Validates safe exploration and boundary enforcement.
"""

from core.exploration import ExplorationLayer, ExplorationMode, ExplorationBound


def test_default_bounds_configured():
    """Should have default safety bounds."""
    exploration = ExplorationLayer(seed=42)

    assert "risk_score" in exploration.bounds
    assert "complexity" in exploration.bounds


def test_is_safe_to_explore_within_bounds():
    """Should be safe when within bounds."""
    exploration = ExplorationLayer(seed=42)

    is_safe, reason = exploration.is_safe_to_explore(
        {
            "risk_score": 50.0,
            "complexity": 3.0,
        }
    )

    assert is_safe
    assert reason is None


def test_is_safe_to_explore_outside_bounds():
    """Should be unsafe when outside bounds."""
    exploration = ExplorationLayer(seed=42)

    is_safe, reason = exploration.is_safe_to_explore(
        {
            "risk_score": 90.0,  # Above safe max (70)
            "complexity": 3.0,
        }
    )

    assert not is_safe
    assert "risk_score" in reason


def test_should_explore_exploit_mode():
    """EXPLOIT mode should never explore."""
    exploration = ExplorationLayer(seed=42)
    exploration.set_mode(ExplorationMode.EXPLOIT)

    # Try many times
    for _ in range(20):
        assert not exploration.should_explore()


def test_should_explore_explore_mode():
    """EXPLORE mode should always explore."""
    exploration = ExplorationLayer(seed=42)
    exploration.set_mode(ExplorationMode.EXPLORE)

    # Try many times
    for _ in range(20):
        assert exploration.should_explore()


def test_should_explore_balanced_mode():
    """BALANCED mode should sometimes explore based on rate."""
    exploration = ExplorationLayer(seed=42)
    exploration.set_mode(ExplorationMode.BALANCED)
    exploration.set_exploration_rate(0.5)  # 50% rate

    # Sample many times
    explorations = sum(1 for _ in range(100) if exploration.should_explore())

    # Should be roughly 50% (allow some variance)
    assert 35 <= explorations <= 65


def test_clamp_to_bounds():
    """Should clamp parameters to safety bounds."""
    exploration = ExplorationLayer(seed=42)

    clamped = exploration.clamp_to_bounds(
        {
            "risk_score": 90.0,  # Above max (70)
            "complexity": 0.5,  # Below min (1.0)
            "other_param": 123,  # No bound, unchanged
        }
    )

    assert clamped["risk_score"] == 70.0
    assert clamped["complexity"] == 1.0
    assert clamped["other_param"] == 123


def test_record_exploration():
    """Should record exploration attempts."""
    exploration = ExplorationLayer(seed=42)

    exploration.record_exploration("strategy_a", success=True, reward=0.8)

    assert len(exploration.exploration_history) == 1
    assert exploration.exploration_history[0].strategy == "strategy_a"
    assert exploration.exploration_history[0].success is True


def test_record_exploration_adds_to_known_good():
    """Successful high-reward explorations should become known-good."""
    exploration = ExplorationLayer(seed=42)

    exploration.record_exploration("strategy_x", success=True, reward=0.9)

    assert "strategy_x" in exploration.known_good_strategies


def test_get_exploration_stats():
    """Should calculate exploration statistics."""
    exploration = ExplorationLayer(seed=42)

    # Record some results
    exploration.record_exploration("s1", success=True, reward=0.8)
    exploration.record_exploration("s2", success=True, reward=0.9)
    exploration.record_exploration("s3", success=False, reward=0.2)
    exploration.record_exploration("s4", success=True, reward=0.7, reverted=True)

    stats = exploration.get_exploration_stats()

    assert stats["total_explorations"] == 4
    assert stats["success_rate"] == 0.75  # 3/4
    assert stats["reversion_rate"] == 0.25  # 1/4
    assert stats["average_reward"] == (0.8 + 0.9 + 0.2 + 0.7) / 4


def test_evaluate_blocks_unsafe_exploration():
    """Evaluate should block exploration when unsafe."""
    exploration = ExplorationLayer(seed=42)

    result = exploration.evaluate(
        {"action_type": "test"}, {"risk_score": 90.0}  # Above safe max
    )

    assert result.passed is False
    assert "unsafe" in result.reason.lower()


def test_evaluate_allows_safe_exploration():
    """Evaluate should allow exploration when safe."""
    exploration = ExplorationLayer(seed=42)

    result = exploration.evaluate(
        {"action_type": "test"}, {"risk_score": 30.0, "complexity": 2.0}
    )

    assert result.passed is True


def test_evaluate_includes_stats():
    """Evaluate should include exploration stats in metadata."""
    exploration = ExplorationLayer(seed=42)

    result = exploration.evaluate({}, {})

    assert "stats" in result.metadata
    assert "total_explorations" in result.metadata["stats"]


def test_add_custom_bound():
    """Should be able to add custom safety bounds."""
    exploration = ExplorationLayer(seed=42)

    custom = ExplorationBound(
        parameter="custom_metric",
        safe_min=0.0,
        safe_max=100.0,
        fallback_value=50.0,
    )

    exploration.add_bound(custom)

    assert "custom_metric" in exploration.bounds

    # Test bound enforcement
    is_safe, reason = exploration.is_safe_to_explore({"custom_metric": 150.0})
    assert not is_safe


def test_set_exploration_rate():
    """Should be able to set exploration rate."""
    exploration = ExplorationLayer(seed=42)

    exploration.set_exploration_rate(0.3)

    assert exploration.exploration_rate == 0.3


def test_set_exploration_rate_clamped():
    """Exploration rate should be clamped to 0-1."""
    exploration = ExplorationLayer(seed=42)

    exploration.set_exploration_rate(1.5)
    assert exploration.exploration_rate == 1.0

    exploration.set_exploration_rate(-0.5)
    assert exploration.exploration_rate == 0.0


def test_deterministic_rng():
    """With same seed, exploration should be deterministic."""
    exp = ExplorationLayer(seed=123)
    exp.set_mode(ExplorationMode.BALANCED)

    # Record first sequence
    results1 = [exp.should_explore() for _ in range(20)]

    # Reset with same seed
    exp2 = ExplorationLayer(seed=123)
    exp2.set_mode(ExplorationMode.BALANCED)
    results2 = [exp2.should_explore() for _ in range(20)]

    # Should be identical
    assert results1 == results2
