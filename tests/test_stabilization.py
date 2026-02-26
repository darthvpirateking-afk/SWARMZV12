"""
Tests for Stabilization Layer (P2.3)

Validates oscillation detection and stability enforcement.
"""

from core.stabilization import StabilizationLayer, OscillationDetector, CooldownTracker
import time


def test_oscillation_detector_stable():
    """Should not detect oscillation in stable values."""
    detector = OscillationDetector("test_metric", window_size=10, threshold_crossings=3)
    
    # Add truly stable values (same value)
    for i in range(10):
        detector.add_value(50.0)
    
    assert not detector.detect_oscillation()


def test_oscillation_detector_oscillating():
    """Should detect rapidly oscillating values."""
    detector = OscillationDetector("test_metric", window_size=10, threshold_crossings=3)
    
    # Add oscillating values
    for i in range(10):
        detector.add_value(100.0 if i % 2 == 0 else 0.0)
    
    assert detector.detect_oscillation()


def test_cooldown_tracker_ready_initially():
    """Cooldown should be ready initially."""
    tracker = CooldownTracker("test_action", cooldown_seconds=60.0)
    
    assert tracker.is_ready()
    assert tracker.remaining_cooldown() == 0.0


def test_cooldown_tracker_not_ready_after_execution():
    """Should not be ready immediately after execution."""
    tracker = CooldownTracker("test_action", cooldown_seconds=60.0)
    
    tracker.record_execution()
    
    assert not tracker.is_ready()
    assert tracker.remaining_cooldown() > 0.0


def test_cooldown_tracker_ready_after_elapsed():
    """Should be ready after cooldown elapses."""
    tracker = CooldownTracker("test_action", cooldown_seconds=0.1)  # 100ms
    
    tracker.record_execution()
    time.sleep(0.15)  # Wait for cooldown
    
    assert tracker.is_ready()


def test_track_metric():
    """Should track metrics for oscillation detection."""
    stabilization = StabilizationLayer()
    
    stabilization.track_metric("test_metric", 10.0)
    stabilization.track_metric("test_metric", 20.0)
    
    assert "test_metric" in stabilization.oscillation_detectors
    assert len(stabilization.oscillation_detectors["test_metric"].values) == 2


def test_is_oscillating():
    """Should detect oscillating metrics."""
    stabilization = StabilizationLayer()
    
    # Create oscillation
    for i in range(10):
        stabilization.track_metric("oscillating", 100.0 if i % 2 == 0 else 0.0)
    
    assert stabilization.is_oscillating("oscillating")


def test_set_and_check_cooldown():
    """Should set and check cooldown for actions."""
    stabilization = StabilizationLayer()
    
    stabilization.set_cooldown("test_action", 60.0)
    
    # Initially ready
    is_ready, remaining = stabilization.check_cooldown("test_action")
    assert is_ready
    
    # Record execution
    stabilization.record_action("test_action")
    
    # Now in cooldown
    is_ready, remaining = stabilization.check_cooldown("test_action")
    assert not is_ready
    assert remaining > 0.0


def test_apply_damping():
    """Should apply damping to smooth changes."""
    stabilization = StabilizationLayer()
    
    # Move from 0 to 100 with 50% damping
    damped = stabilization.apply_damping(0.0, 100.0, damping_factor=0.5)
    
    # Should be halfway (50% of change applied)
    assert damped == 50.0


def test_apply_damping_no_damping():
    """Zero damping should apply full change."""
    stabilization = StabilizationLayer()
    
    damped = stabilization.apply_damping(0.0, 100.0, damping_factor=0.0)
    
    assert damped == 100.0


def test_apply_hysteresis_prevents_flapping():
    """Hysteresis should prevent threshold flapping."""
    stabilization = StabilizationLayer()
    stabilization.stability_buffer = 0.1  # 10% buffer
    
    threshold = 50.0
    
    # Currently False, need to exceed threshold + buffer to flip
    assert not stabilization.apply_hysteresis(50.0, threshold, last_state=False)
    assert not stabilization.apply_hysteresis(54.0, threshold, last_state=False)
    assert stabilization.apply_hysteresis(56.0, threshold, last_state=False)
    
    # Currently True, need to drop below threshold - buffer to flip
    assert stabilization.apply_hysteresis(50.0, threshold, last_state=True)
    assert stabilization.apply_hysteresis(46.0, threshold, last_state=True)
    assert not stabilization.apply_hysteresis(44.0, threshold, last_state=True)


def test_evaluate_blocks_on_cooldown():
    """Evaluate should block actions in cooldown."""
    stabilization = StabilizationLayer()
    
    stabilization.set_cooldown("test_action", 60.0)
    stabilization.record_action("test_action")
    
    result = stabilization.evaluate(
        {"action_type": "test_action"},
        {}
    )
    
    assert result.passed is False
    assert "cooldown" in result.reason.lower()


def test_evaluate_blocks_on_oscillation():
    """Evaluate should block when system is oscillating."""
    stabilization = StabilizationLayer()
    
    # Create oscillating metric
    for i in range(10):
        stabilization.track_metric("test_metric", 100.0 if i % 2 == 0 else 0.0)
    
    result = stabilization.evaluate(
        {"action_type": "test"},
        {"test_metric": 100.0}
    )
    
    assert result.passed is False
    assert "oscillating" in result.reason.lower()


def test_evaluate_passes_when_stable():
    """Evaluate should pass when system is stable."""
    stabilization = StabilizationLayer()
    
    # Track stable metrics
    for i in range(10):
        stabilization.track_metric("stable_metric", 50.0)
    
    result = stabilization.evaluate(
        {"action_type": "test"},
        {"stable_metric": 50.0}
    )
    
    assert result.passed is True


def test_get_oscillating_metrics():
    """Should return list of oscillating metrics."""
    stabilization = StabilizationLayer()
    
    # Create one stable, one oscillating
    for i in range(10):
        stabilization.track_metric("stable", 50.0)
        stabilization.track_metric("oscillating", 100.0 if i % 2 == 0 else 0.0)
    
    oscillating = stabilization.get_oscillating_metrics()
    
    assert "oscillating" in oscillating
    assert "stable" not in oscillating
