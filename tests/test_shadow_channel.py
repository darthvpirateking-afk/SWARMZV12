"""
Tests for Shadow Channel (P1.2)

Validates opaque decision tracking and user-facing message sanitization.
"""

import pytest
from core.shadow_channel import ShadowChannel, OpacityLevel, ShadowDecision
from core.reversible import LayerResult


def test_record_shadow_decision():
    """Shadow decisions should be recorded with full details."""
    shadow = ShadowChannel()
    shadow.clear_shadow_log()
    
    decision = shadow.record_shadow_decision(
        layer="threshold",
        passed=False,
        internal_reason="Budget exhausted: -50.0 remaining (technical details)",
        user_facing_message="Budget limit reached",
        opacity_level=OpacityLevel.PARTIAL,
        metadata={"budget": -50.0},
    )
    
    assert decision.layer == "threshold"
    assert decision.passed is False
    assert "technical details" in decision.internal_reason
    assert decision.user_facing_message == "Budget limit reached"
    assert decision.opacity_level == OpacityLevel.PARTIAL


def test_wrap_transparent_result():
    """TRANSPARENT opacity should preserve full details."""
    shadow = ShadowChannel()
    shadow.clear_shadow_log()
    
    original = LayerResult(
        layer="integrity",
        passed=True,
        reason="All structural constraints satisfied",
        metadata={"checks": 5},
        timestamp=123.0,
    )
    
    wrapped = shadow.wrap_layer_result(original, OpacityLevel.TRANSPARENT)
    
    # Should be unchanged
    assert wrapped.reason == original.reason
    assert wrapped.metadata != {"checks": 5}  # Shadow ID added
    assert "shadow_id" in wrapped.metadata


def test_wrap_partial_result():
    """PARTIAL opacity should simplify reasoning."""
    shadow = ShadowChannel()
    shadow.clear_shadow_log()
    
    original = LayerResult(
        layer="scoring",
        passed=False,
        reason="Risk score 85/100: high mission rank + budget impact + 3 recent failures",
        metadata={},
        timestamp=123.0,
    )
    
    wrapped = shadow.wrap_layer_result(original, OpacityLevel.PARTIAL)
    
    # Simplified message
    assert wrapped.reason == "Scoring constraints not met"
    assert "shadow_id" in wrapped.metadata
    
    # Original details in shadow log
    log = shadow.query_shadow_log(layer="scoring")
    assert len(log) == 1
    assert "Risk score 85/100" in log[0].internal_reason


def test_wrap_opaque_result():
    """OPAQUE opacity should hide all reasoning."""
    shadow = ShadowChannel()
    shadow.clear_shadow_log()
    
    original = LayerResult(
        layer="sovereign",
        passed=False,
        reason="Security policy blocks unsafe operations (CVE-2024-1234 detected)",
        metadata={},
        timestamp=123.0,
    )
    
    wrapped = shadow.wrap_layer_result(original, OpacityLevel.OPAQUE)
    
    # Generic message only
    assert wrapped.reason == "Action not permitted"
    assert "CVE" not in wrapped.reason
    
    # Full details in shadow log
    log = shadow.query_shadow_log(layer="sovereign")
    assert "CVE-2024-1234" in log[0].internal_reason


def test_wrap_silent_result():
    """SILENT opacity should provide no user-facing indication."""
    shadow = ShadowChannel()
    shadow.clear_shadow_log()
    
    original = LayerResult(
        layer="threshold",
        passed=True,
        reason="Rate limit passed (50/120 requests)",
        metadata={},
        timestamp=123.0,
    )
    
    wrapped = shadow.wrap_layer_result(original, OpacityLevel.SILENT)
    
    # No reason shown
    assert wrapped.reason == ""
    assert wrapped.metadata["silent"] is True
    
    # Logged internally
    log = shadow.query_shadow_log(opacity_level=OpacityLevel.SILENT)
    assert len(log) == 1
    assert "Rate limit passed" in log[0].internal_reason


def test_query_shadow_log_filters():
    """Shadow log queries should support filtering."""
    shadow = ShadowChannel()
    shadow.clear_shadow_log()
    
    # Record multiple decisions
    shadow.record_shadow_decision("layer1", True, "reason1", "msg1", OpacityLevel.TRANSPARENT)
    shadow.record_shadow_decision("layer2", False, "reason2", "msg2", OpacityLevel.OPAQUE)
    shadow.record_shadow_decision("layer1", False, "reason3", "msg3", OpacityLevel.PARTIAL)
    
    # Filter by layer
    layer1_results = shadow.query_shadow_log(layer="layer1")
    assert len(layer1_results) == 2
    
    # Filter by passed
    denied = shadow.query_shadow_log(passed=False)
    assert len(denied) == 2
    
    # Filter by opacity
    opaque = shadow.query_shadow_log(opacity_level=OpacityLevel.OPAQUE)
    assert len(opaque) == 1
    assert opaque[0].layer == "layer2"


def test_get_decision_by_id():
    """Should retrieve specific decision by ID."""
    shadow = ShadowChannel()
    shadow.clear_shadow_log()
    
    decision = shadow.record_shadow_decision(
        "test_layer", True, "internal", "external", OpacityLevel.PARTIAL
    )
    
    retrieved = shadow.get_decision_by_id(decision.decision_id)
    assert retrieved is not None
    assert retrieved.decision_id == decision.decision_id
    assert retrieved.internal_reason == "internal"


def test_get_decision_by_id_not_found():
    """Should return None for unknown ID."""
    shadow = ShadowChannel()
    shadow.clear_shadow_log()
    
    retrieved = shadow.get_decision_by_id("nonexistent_id")
    assert retrieved is None


def test_custom_user_message():
    """Should allow custom user-facing messages."""
    shadow = ShadowChannel()
    shadow.clear_shadow_log()
    
    original = LayerResult(
        layer="integrity",
        passed=False,
        reason="Cyclic dependency detected: A -> B -> C -> A",
        metadata={},
        timestamp=123.0,
    )
    
    wrapped = shadow.wrap_layer_result(
        original,
        OpacityLevel.PARTIAL,
        user_facing_message="Configuration error detected"
    )
    
    assert wrapped.reason == "Configuration error detected"
    
    # Original preserved in shadow
    log = shadow.query_shadow_log(layer="integrity")
    assert "Cyclic dependency" in log[0].internal_reason


def test_evaluate_passthrough():
    """Shadow channel evaluate should pass through."""
    shadow = ShadowChannel()
    
    result = shadow.evaluate({}, {})
    
    assert result.passed is True
    assert result.layer == "shadow"


def test_shadow_log_ordering():
    """Shadow log should maintain chronological order."""
    shadow = ShadowChannel()
    shadow.clear_shadow_log()
    
    for i in range(5):
        shadow.record_shadow_decision(
            f"layer{i}", True, f"reason{i}", f"msg{i}", OpacityLevel.TRANSPARENT
        )
    
    log = shadow.query_shadow_log(limit=5)
    
    # Should be in order recorded
    for i in range(5):
        assert log[i].internal_reason == f"reason{i}"
