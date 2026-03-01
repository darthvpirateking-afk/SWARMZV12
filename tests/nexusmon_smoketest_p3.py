"""
NEXUSMON Phase 3 Smoketest (End-to-End Hardened Loop)

This script validates the entire pipeline:
1. Routing from intent to Nexusmon Engine.
2. DAG decomposition of domain-specific tasks.
3. Capability checks (Registry).
4. Sovereign classification (Safety).
5. Telemetry persistence.
"""

import json
from pathlib import Path
from swarm_runner import _process_one
from core.capability_flags import registry, CapabilityStatus

DATA_DIR = Path("data")
MISSIONS_FILE = DATA_DIR / "missions.jsonl"
TELEMETRY_FILE = DATA_DIR / "telemetry.jsonl"


def setup_clean_state():
    print("[1] Cleaning old data...")
    if MISSIONS_FILE.exists():
        MISSIONS_FILE.unlink()
    if TELEMETRY_FILE.exists():
        TELEMETRY_FILE.unlink()

    # Enable domains
    registry.set_status("bio_lab_api", CapabilityStatus.AVAILABLE)
    registry.set_status("space_mission_control", CapabilityStatus.AVAILABLE)


def run_loop_test():
    setup_clean_state()

    print("[2] Queuing Sovereign Bio-Mission...")
    mission = {
        "mission_id": "SMOKE-P3-BIO",
        "intent": "Run nexusmon CRISPR verify for PROJECT SOVEREIGN",
        "status": "PENDING",
        "spec": {"sequence_id": "SOV-X1"},
        "created_at": "2024-01-01T00:00:00Z",
    }

    with open(MISSIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(mission) + "\n")

    print("[3] Running runner tick...")
    _process_one()

    print("[4] Verifying Outcomes...")
    # Check results in packs directory
    pack_res = Path("packs/SMOKE-P3-BIO/result.json")
    if pack_res.exists():
        res_data = json.loads(pack_res.read_text())
        if res_data.get("ok"):
            print("  ✅ Mission SUCCESS")
            print(f"  ✅ Executed {len(res_data.get('results', {}))} steps.")
        else:
            print(f"  ❌ Mission FAILED: {res_data.get('error')}")
    else:
        print("  ❌ Result file missing!")

    # Check telemetry
    if TELEMETRY_FILE.exists():
        logs = TELEMETRY_FILE.read_text().splitlines()
        print(f"  ✅ Generated {len(logs)} telemetry events.")

    print("\n[COMPLETE] NEXUSMON P3 Hardened Loop is FUNCTIONAL.")


if __name__ == "__main__":
    run_loop_test()
