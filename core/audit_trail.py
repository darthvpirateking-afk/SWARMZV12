import json
import time
import os
from pathlib import Path

AUDIT_FILE = Path("data/persistent_audit.jsonl")


def initialize_audit_trail():
    os.makedirs(AUDIT_FILE.parent, exist_ok=True)
    if not AUDIT_FILE.exists():
        AUDIT_FILE.touch()


def log_audit_event(event_type: str, details: dict, actor: str = "system"):
    """Granular, timestamped logging of decision pathways and memory edits."""
    event = {
        "timestamp": time.time(),
        "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event_type": event_type,
        "actor": actor,
        "details": details,
    }
    try:
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        print(f"Failed to write audit log: {e}")


initialize_audit_trail()
