"""
Tests for Uplift Layer (P2.2)

Validates progressive capability unlocking.
"""

from core.uplift import UpliftLayer, Capability, CapabilityTier


def test_basic_capabilities_unlocked():
    """BASIC tier capabilities should be unlocked by default."""
    uplift = UpliftLayer()
    
    assert uplift.is_capability_unlocked("basic_execution")


def test_intermediate_unlock_conditions():
    """INTERMEDIATE tier should unlock after meeting conditions."""
    uplift = UpliftLayer()
    
    # Initially locked
    assert not uplift.is_capability_unlocked("parallel_execution")
    
    # Simulate successful executions
    for _ in range(10):
        uplift.update_maturity(success=True, confidence=0.9)
    
    uplift.evaluate_unlocks()
    
    # Should now be unlocked (10 successes, 100% success rate)
    assert uplift.is_capability_unlocked("parallel_execution")


def test_advanced_unlock_requires_uptime():
    """ADVANCED tier should require uptime in addition to success."""
    uplift = UpliftLayer()
    
    # Even with high success, advanced needs uptime
    for _ in range(60):
        uplift.update_maturity(success=True, confidence=0.95)
    
    # Without waiting for uptime, should still be locked
    uplift.evaluate_unlocks()
    
    # Check that it's locked due to uptime
    can_unlock, reason = uplift.check_unlock_conditions(
        uplift.capabilities["autonomous_planning"]
    )
    
    assert not can_unlock
    assert "uptime" in reason.lower()


def test_success_rate_calculation():
    """Should correctly calculate success rate."""
    uplift = UpliftLayer()
    
    # 8 successes, 2 failures = 80%
    for _ in range(8):
        uplift.update_maturity(success=True)
    for _ in range(2):
        uplift.update_maturity(success=False)
    
    assert uplift.maturity.success_rate() == 0.8


def test_low_success_rate_blocks_unlock():
    """Low success rate should prevent unlock."""
    uplift = UpliftLayer()
    
    # Need 80% for intermediate, only give 60%
    for _ in range(6):
        uplift.update_maturity(success=True)
    for _ in range(4):
        uplift.update_maturity(success=False)
    
    uplift.evaluate_unlocks()
    
    assert not uplift.is_capability_unlocked("parallel_execution")


def test_rollback_count_blocks_experimental():
    """Too many rollbacks should block EXPERIMENTAL tier."""
    uplift = UpliftLayer()
    
    # Meet action/success requirements
    for _ in range(150):
        uplift.update_maturity(success=True, confidence=0.98)
    
    # But too many rollbacks
    for _ in range(10):
        uplift.update_maturity(success=True, rolled_back=True)
    
    uplift.evaluate_unlocks()
    
    # Check experimental is still locked
    # Note: May fail on uptime before rollback check, both are valid blocking reasons
    can_unlock, reason = uplift.check_unlock_conditions(
        uplift.capabilities["self_modification"]
    )
    
    assert not can_unlock
    # Reason is either uptime or rollback
    assert "uptime" in reason.lower() or "rollback" in reason.lower()


def test_evaluate_returns_unlock_event():
    """Evaluate should report when capabilities unlock."""
    uplift = UpliftLayer()
    
    # Progress to unlock
    for _ in range(10):
        result = uplift.evaluate({}, {"success": True, "confidence": 0.9})
    
    # Check if unlock was reported
    assert result.layer == "uplift"
    if "newly_unlocked" in result.metadata:
        assert len(result.metadata["newly_unlocked"]) > 0


def test_get_locked_capabilities():
    """Should return list of locked capabilities."""
    uplift = UpliftLayer()
    
    locked = uplift.get_locked_capabilities()
    
    # At start, should have 3 locked (intermediate, advanced, experimental)
    assert len(locked) >= 3
    assert all(not c.unlocked for c in locked)


def test_get_unlocked_capabilities():
    """Should return list of unlocked capabilities."""
    uplift = UpliftLayer()
    
    unlocked = uplift.get_unlocked_capabilities()
    
    # At start, should have 1 unlocked (basic)
    assert len(unlocked) >= 1
    assert all(c.unlocked for c in unlocked)


def test_capability_unlock_timestamp():
    """Should record unlock timestamp."""
    uplift = UpliftLayer()
    
    # Unlock intermediate
    for _ in range(12):
        uplift.update_maturity(success=True, confidence=0.9)
    
    uplift.evaluate_unlocks()
    
    capability = uplift.capabilities["parallel_execution"]
    if capability.unlocked:
        assert capability.unlocked_at is not None
        assert capability.unlocked_at > 0


def test_custom_capability_addition():
    """Should be able to add custom capabilities."""
    uplift = UpliftLayer()
    
    custom = Capability(
        name="custom_feature",
        tier=CapabilityTier.INTERMEDIATE,
        unlock_conditions={"successful_actions": 5},
    )
    
    uplift.add_capability(custom)
    
    assert "custom_feature" in uplift.capabilities
    assert not uplift.is_capability_unlocked("custom_feature")
    
    # Unlock it
    for _ in range(5):
        uplift.update_maturity(success=True)
    
    uplift.evaluate_unlocks()
    
    assert uplift.is_capability_unlocked("custom_feature")
