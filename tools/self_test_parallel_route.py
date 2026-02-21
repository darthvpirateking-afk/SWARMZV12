# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import os
import subprocess
import json


def generate_synthetic_events():
    events = [
        {"event_type": "process_start", "timestamp": "2026-02-17T10:00:00Z"},
        {
            "event_type": "file_write",
            "timestamp": "2026-02-17T10:01:00Z",
            "file": "test.txt",
        },
        {"event_type": "process_end", "timestamp": "2026-02-17T10:02:00Z"},
        {"event_type": "error", "timestamp": "2026-02-17T10:03:00Z"},
    ]
    with open("data/activity/events.jsonl", "w") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")


def run_tool(tool_path):
    try:
        subprocess.run(["python", tool_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {tool_path}: {e}")


def verify_sequences():
    with open("data/activity/sequences.json") as f:
        sequences = json.load(f)
        assert len(sequences) > 0, "No sequences found"


def verify_anomalies():
    with open("data/activity/anomalies.jsonl") as f:
        anomalies = f.readlines()
        assert len(anomalies) > 0, "No anomalies found"


def verify_bypass_map():
    with open("docs/BYPASS_MAP.md") as f:
        content = f.read()
        assert "# BYPASS MAP" in content, "Bypass map not generated"


def main():
    generate_synthetic_events()
    run_tool("tools/mine_sequences.py")
    verify_sequences()
    run_tool("tools/scan_anomalies.py")
    verify_anomalies()
    run_tool("tools/build_bypass_map.py")
    verify_bypass_map()
    print("All tests passed!")


if __name__ == "__main__":
    main()
