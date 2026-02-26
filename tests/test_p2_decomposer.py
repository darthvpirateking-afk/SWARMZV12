import json
import os
from pathlib import Path
from swarm_runner import _worker_nexusmon_mission

def test_nexusmon_bio_decomposition():
    """Test that a bio intent is correctly decomposed into a DAG and executed."""
    mission = {
        "mission_id": "bio_test_001",
        "intent": "Verify CRISPR sequence for project SOVEREIGN",
        "spec": {"sequence_id": "SEQ-99"}
    }
    
    result = _worker_nexusmon_mission(mission)
    
    assert result["ok"] is True
    # Verify the results has multiple steps from the bio domain
    results = result["results"]
    
    # We expect: sequence_load -> crispr_verify -> fold_simulation
    task_ids = list(results.keys())
    assert "sequence_load" in task_ids
    assert "crispr_verify" in task_ids
    assert "fold_simulation" in task_ids
    
    # Verify the metadata in the results contains the sequence_id
    assert results["sequence_load"].metadata["sequence_id"] == "SEQ-99"

def test_nexusmon_space_decomposition():
    """Test that a space intent is correctly decomposed and executed."""
    # Enable capability for the test
    from core.capability_flags import registry, CapabilityStatus
    registry.set_status("space_mission_control", CapabilityStatus.AVAILABLE)

    mission = {
        "mission_id": "space_test_001",
        "intent": "Nexusmon space orbital sync",
        "spec": {"target": "NEXUS-7"}
    }
    
    result = _worker_nexusmon_mission(mission)
    
    assert result["ok"] is True
    task_ids = list(result["results"].keys())
    assert "orbital_sync" in task_ids
    assert "trajectory_verify" in task_ids
