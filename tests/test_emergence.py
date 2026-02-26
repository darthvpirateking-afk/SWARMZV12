"""
Tests for Emergence Layer (P2.1)

Validates pattern detection and emergent behavior tracking.
"""

from core.emergence import EmergenceLayer, Pattern


def test_record_action():
    """Should record actions to history."""
    emergence = EmergenceLayer(history_size=10)
    
    emergence.record_action({"action_type": "test"}, {"field": 123})
    
    assert len(emergence.action_history) == 1
    assert emergence.action_history[0]["action"]["action_type"] == "test"


def test_history_size_limit():
    """History should be bounded by max size."""
    emergence = EmergenceLayer(history_size=5)
    
    for i in range(10):
        emergence.record_action({"action_type": f"action_{i}"}, {})
    
    assert len(emergence.action_history) == 5
    # Should have most recent 5
    assert emergence.action_history[-1]["action"]["action_type"] == "action_9"


def test_detect_sequence_pattern():
    """Should detect repeated action sequences."""
    emergence = EmergenceLayer()
    
    # Create A -> B -> C pattern twice
    for _ in range(2):
        emergence.record_action({"action_type": "A"}, {})
        emergence.record_action({"action_type": "B"}, {})
        emergence.record_action({"action_type": "C"}, {})
    
    patterns = emergence.detect_sequence_pattern(sequence_length=3, min_occurrences=2)
    
    assert len(patterns) >= 1
    found = False
    for p in patterns:
        if p.metadata.get("sequence") == ("A", "B", "C"):
            found = True
            assert p.frequency >= 2
            assert p.pattern_type == "sequence"
    
    assert found, "Should find A->B->C sequence"


def test_detect_correlation_positive():
    """Should detect positive correlation between fields."""
    emergence = EmergenceLayer()
    
    # Create positive correlation: a increases, b increases
    for i in range(20):
        emergence.record_action(
            {"action_type": "test"},
            {"field_a": i, "field_b": i * 2}
        )
    
    pattern = emergence.detect_correlation("field_a", "field_b", threshold=0.7)
    
    assert pattern is not None
    assert pattern.pattern_type == "correlation"
    assert pattern.metadata["direction"] == "positive"
    assert pattern.confidence > 0.9  # Should be strong correlation


def test_detect_correlation_negative():
    """Should detect negative correlation between fields."""
    emergence = EmergenceLayer()
    
    # Create negative correlation: a increases, b decreases
    for i in range(20):
        emergence.record_action(
            {"action_type": "test"},
            {"field_a": i, "field_b": 100 - i}
        )
    
    pattern = emergence.detect_correlation("field_a", "field_b", threshold=0.7)
    
    assert pattern is not None
    assert pattern.metadata["direction"] == "negative"
    assert pattern.confidence > 0.9


def test_detect_correlation_insufficient_data():
    """Should not detect correlation with insufficient data."""
    emergence = EmergenceLayer()
    
    # Only 2 data points
    emergence.record_action({"action_type": "test"}, {"field_a": 1, "field_b": 2})
    emergence.record_action({"action_type": "test"}, {"field_a": 3, "field_b": 4})
    
    pattern = emergence.detect_correlation("field_a", "field_b")
    
    assert pattern is None


def test_detect_anomaly():
    """Should detect outliers in data."""
    emergence = EmergenceLayer()
    
    # Normal values around 50, plus one outlier
    for i in range(20):
        emergence.record_action(
            {"action_type": "test"},
            {"value": 50 + (i % 10)}  # 50-59 range
        )
    
    # Add outlier
    emergence.record_action({"action_type": "test"}, {"value": 500})
    
    anomalies = emergence.detect_anomaly("value", std_threshold=2.0)
    
    assert len(anomalies) >= 1
    # Last index should be anomaly with high z-score
    indices = [idx for idx, z in anomalies]
    assert len(emergence.action_history) - 1 in indices


def test_detect_cyclic_behavior():
    """Should detect repeating state cycles."""
    emergence = EmergenceLayer()
    
    # Create A -> B -> A -> B cycle (enough for detection)
    for _ in range(10):
        emergence.record_action({"action_type": "A"}, {"state": "init"})
        emergence.record_action({"action_type": "B"}, {"state": "process"})
    
    pattern = emergence.detect_cyclic_behavior(window_size=5)
    
    assert pattern is not None
    assert pattern.pattern_type == "cycle"
    assert pattern.metadata["period"] == 2


def test_analyze_emergence_with_patterns():
    """Analyze should detect and report strong patterns."""
    emergence = EmergenceLayer()
    
    # Create strong sequence pattern
    for _ in range(5):
        emergence.record_action({"action_type": "X"}, {})
        emergence.record_action({"action_type": "Y"}, {})
        emergence.record_action({"action_type": "Z"}, {})
    
    result = emergence.analyze_emergence()
    
    assert result.passed is True
    assert result.metadata["patterns_detected"] >= 1


def test_evaluate_records_and_analyzes():
    """Evaluate should record action and periodically analyze."""
    emergence = EmergenceLayer()
    
    # Record 10 actions to trigger analysis
    for i in range(10):
        result = emergence.evaluate(
            {"action_type": f"action_{i}"},
            {"value": i}
        )
    
    # Should have recorded all actions
    assert len(emergence.action_history) == 10
    
    # 10th action should trigger analysis
    assert result.layer == "emergence"


def test_get_patterns_filter_by_type():
    """Should filter patterns by type."""
    emergence = EmergenceLayer()
    
    # Create sequence pattern
    for _ in range(3):
        emergence.record_action({"action_type": "A"}, {})
        emergence.record_action({"action_type": "B"}, {})
    
    emergence.detect_sequence_pattern(sequence_length=2, min_occurrences=2)
    
    seq_patterns = emergence.get_patterns(pattern_type="sequence")
    
    assert all(p.pattern_type == "sequence" for p in seq_patterns)


def test_get_patterns_filter_by_confidence():
    """Should filter patterns by minimum confidence."""
    emergence = EmergenceLayer()
    
    # Create high-confidence correlation
    for i in range(20):
        emergence.record_action(
            {"action_type": "test"},
            {"a": i, "b": i}
        )
    
    emergence.detect_correlation("a", "b")
    
    high_conf = emergence.get_patterns(min_confidence=0.9)
    
    assert all(p.confidence >= 0.9 for p in high_conf)
