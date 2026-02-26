import json
import time
from datetime import datetime, timezone
from pathlib import Path
from swarm_runner import _process_one
from core.telemetry import telemetry
from core.capability_flags import registry, CapabilityStatus

DATA_DIR = Path("data")
MISSIONS_FILE = DATA_DIR / "missions.jsonl"

def test_legacy_to_nexusmon_routing():
    """Verify that a legacy mission with 'sovereign' in intent is routed to Nexusmon Engine."""
    # Ensure missions file exists and is EMPTY for clean test
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(MISSIONS_FILE, "w", encoding="utf-8") as f:
        f.write("")
    
    # Create a fresh PENDING mission
    mission_id = f"LEGACY-{int(time.time())}"
    mission = {
        "mission_id": mission_id,
        "intent": "E2E sovereign dispatch", # This should trigger Nexusmon routing
        "status": "PENDING",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
    }
    
    # Write to missions.jsonl
    with open(MISSIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(mission) + "\n")
    
    # Ensure kernel is up
    registry.set_status("kernel_base", CapabilityStatus.AVAILABLE)
    
    # Run one tick of the runner
    telemetry.clear()
    _process_one()
    
    # Check if the runner processed it via NexusmonEngine
    logs = telemetry.get_recent_logs()
    # "Initiating mission" is a log from core/mission_engine.py
    assert any("Initiating mission" in log['message'] for log in logs)
    assert any(mission_id in log['message'] for log in logs)
    
    # Verify mission status in file
    with open(MISSIONS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        last_mission = json.loads(lines[-1].strip())
        assert last_mission["mission_id"] == mission_id
        assert last_mission["status"] in ["SUCCESS", "FAILURE", "RUNNING"]
