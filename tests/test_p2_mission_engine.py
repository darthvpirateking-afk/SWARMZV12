import time
from core.mission_engine import MissionEngine
from core.capability_flags import registry, CapabilityStatus, Capability
from core.sovereign import PolicyRule, SovereignOutcome, add_rule
from core.reversible import LayerResult
from core.telemetry import telemetry


def test_mission_engine_full_dag_execution():
    """Verify that a multi-step DAG with Bio Lab and Space tasks executes correctly."""
    engine = MissionEngine()

    # Ensure capabilities are set for this test
    registry.set_status("bio_lab_api", CapabilityStatus.AVAILABLE)
    # space_mission_control is DISABLED by default. Let's enable it for the success test.
    registry.set_status("space_mission_control", CapabilityStatus.AVAILABLE)

    mission_data = {
        "mission_id": "TEST-DAG-001",
        "tasks": [
            {
                "id": "step1",
                "dependencies": [],
                "capability_id": "kernel_base",
                "params": {"action": "init"},
            },
            {
                "id": "step2",
                "dependencies": ["step1"],
                "capability_id": "bio_lab_api",
                "params": {"action": "scan_sample", "sample_id": "BIO-99"},
            },
            {
                "id": "step3",
                "dependencies": ["step2"],
                "capability_id": "space_mission_control",
                "params": {"target": "orbital_insertion"},
            },
        ],
    }

    result = engine.execute(mission_data)

    assert result["ok"] is True
    assert "step1" in result["results"]
    assert "step2" in result["results"]
    assert "step3" in result["results"]
    assert result["results"]["step2"].layer == "bio_lab_api"


def test_mission_engine_capability_block():
    """Verify that a DISABLED capability blocks the mission."""
    engine = MissionEngine()

    # Disable space_mission_control
    registry.set_status("space_mission_control", CapabilityStatus.DISABLED)

    mission_data = {
        "mission_id": "TEST-BLOCK-001",
        "tasks": [
            {
                "id": "step1",
                "dependencies": [],
                "capability_id": "space_mission_control",
                "params": {"target": "launch"},
            }
        ],
    }

    result = engine.execute(mission_data)

    assert result["ok"] is False
    assert "Capability 'space_mission_control' is disabled" in result["error"]


def test_mission_engine_sovereign_deny():
    """Verify that a Sovereign DENY triggers rollback and mission failure."""
    engine = MissionEngine()
    telemetry.clear()

    # Add a sovereign rule that denies a specific mission action
    add_rule(
        PolicyRule(
            name="deny_unsafe_bio",
            priority=200,
            condition="action == 'unsafe_bio_action'",
            outcome=SovereignOutcome.DENY,
            severity="S2",
            reason="Blocked for safety in tests",
        )
    )

    registry.set_status("bio_lab_api", CapabilityStatus.AVAILABLE)

    mission_data = {
        "mission_id": "TEST-DENY-001",
        "tasks": [
            {
                "id": "bad_step",
                "dependencies": [],
                "capability_id": "bio_lab_api",
                "params": {"action": "unsafe_bio_action"},
            }
        ],
    }

    result = engine.execute(mission_data)

    assert result["ok"] is False
    assert "Sovereign DENY" in result["error"]

    # Verify rollback was called (audit logs or telemetry)
    logs = telemetry.get_recent_logs()
    assert any("MISSION TERMINATED: Sovereign DENY" in log["message"] for log in logs)


def test_mission_engine_rollback_on_worker_failure():
    """Verify that if a worker fails, the mission fails and rolls back."""
    engine = MissionEngine()

    # Mock a failing internal worker by using an unknown capability with a failing stub
    # Wait, the internal worker currently always returns passed=True.
    # Let's add a test-only worker that fails.

    def failing_worker(params):
        return LayerResult(
            layer="fail_layer",
            passed=False,
            reason="Simulated failure",
            metadata={},
            timestamp=time.time(),
        )

    engine._workers["fail_cap"] = failing_worker
    registry.register(
        Capability(
            id="fail_cap",
            name="Failure Cap",
            status=CapabilityStatus.AVAILABLE,
            version_required="1.0.0",
        )
    )

    mission_data = {
        "mission_id": "TEST-FAIL-001",
        "tasks": [
            {
                "id": "fail_step",
                "dependencies": [],
                "capability_id": "fail_cap",
                "params": {},
            }
        ],
    }

    result = engine.execute(mission_data)

    assert result["ok"] is False
    assert "Sovereign DENY" in result["error"]
    assert "Simulated failure" in result["error"]
