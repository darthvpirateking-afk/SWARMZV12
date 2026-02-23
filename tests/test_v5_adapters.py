from __future__ import annotations

from backend.automation.rules_engine import trigger_rule
from backend.intel.firecrawl_pipeline import run_firecrawl_pipeline
from backend.missions.phase_pipeline import run_phase_pipeline
from backend.runner.environment_provisioner import provision_environment


def test_rules_engine_secret_event_maps_to_alert() -> None:
    result = trigger_rule("secret.found", {"count": 1})
    assert result["action"] == "operator_alert"
    assert result["severity"] == "high"


def test_firecrawl_pipeline_runs_secret_scan_and_archive() -> None:
    result = run_firecrawl_pipeline(
        mission_id="m-adapter-1",
        url="https://example.local",
        content="token = ghp_abcdefghijklmnopqrstuvwxyz1234567890",
        js_detected=True,
        curiosity=80,
        creativity=80,
        patience=80,
        aggression=40,
    )
    assert "secret_findings" in result
    assert "archive" in result


def test_phase_pipeline_guarantees_cleanup_on_failure() -> None:
    result = run_phase_pipeline(
        mission_id="m-adapter-2",
        autonomy=80,
        protectiveness=80,
        patience=80,
        fail=True,
    )
    assert result["status"] == "FAILED"
    assert result["vpn_destroyed"] is True


def test_environment_provisioner_vm_and_container_paths() -> None:
    vm_env = provision_environment(
        backend="vm",
        mission_type="exploit",
        profile_name="windows_server_2019",
        creativity=80,
        autonomy=80,
        patience=80,
        protectiveness=80,
    )
    container_env = provision_environment(
        backend="docker",
        mission_type="web",
        profile_name="",
        creativity=40,
        autonomy=40,
        patience=40,
        protectiveness=70,
        mood="protective",
    )
    assert vm_env["backend"] == "vm"
    assert container_env["backend"] == "docker"
