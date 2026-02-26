import time
from core.sovereign import classify, SovereignOutcome
from core.capability_flags import registry, CapabilityStatus
from core.telemetry import telemetry
from core.reversible import LayerResult
from kernel_runtime.orchestrator import SwarmzOrchestrator

def test_critical_system_escalation():
    """Verify that a 'system_critical' action results in ESCALATE (not PASS)."""
    layer_result = LayerResult(
        layer="test_layer",
        passed=True,
        reason="Test action",
        metadata={},
        timestamp=time.time()
    )
    context = {"action_type": "system_critical"}
    
    decision = classify(layer_result, context)
    
    assert decision.outcome == SovereignOutcome.ESCALATE
    assert decision.severity == "S1"
    assert "human-in-the-loop" in decision.reason

def test_capability_disabled_blocking():
    """Verify that a mission targeting a DISABLED capability is blocked."""
    # Ensure space_mission_control is DISABLED (it is by default in registry)
    assert registry.check("space_mission_control") is False
    
    orchestrator = SwarmzOrchestrator()
    # Mocking start_func for _safe_activate
    def mock_start():
        return "STARTED"
    
    result = orchestrator._safe_activate("space_mission_control", mock_start)
    
    # It should return an object() or similar "stub" and not call mock_start
    assert result != "STARTED"
    
    # Check telemetry for warning
    logs = telemetry.get_recent_logs()
    assert any("space_mission_control' is DISABLED" in log['message'] for log in logs)

def test_telemetry_escalation_capture():
    """Verify telemetry captures full metadata for an escalation."""
    telemetry.clear()
    
    telemetry.log_escalation(
        component="test_component",
        rule_name="test_rule",
        reason="test_reason",
        action_id="ACT-123",
        risk_score=0.98
    )
    
    logs = telemetry.get_recent_logs()
    assert len(logs) == 1
    log = logs[0]
    assert log['level'] == "CRITICAL"
    assert log['metadata']['rule_name'] == "test_rule"
    assert log['metadata']['action_id'] == "ACT-123"
    assert log['metadata']['risk_score'] == 0.98

def test_orchestrator_activation_hardening():
    """Verify that orchestrator activation respects the kernel_base registry lock."""
    telemetry.clear()
    
    # Temporarily disable kernel_base (manually in dictionary since it has a lock in the class)
    # Actually, registry.set_status won't work due to lock.
    # In a real test we'd mock the registry or use a fresh one.
    
    # Let's test the lock first
    success = registry.set_status("kernel_base", CapabilityStatus.DISABLED)
    assert success is False
    assert registry.get_status("kernel_base") == CapabilityStatus.AVAILABLE
    
    orchestrator = SwarmzOrchestrator()
    orchestrator.activate()
    
    logs = telemetry.get_recent_logs()
    assert any("NEXUSMON Hardened Activation Sequence Initiated" in log['message'] for log in logs)
    assert any("Kernel activation sequence complete" in log['message'] for log in logs)
