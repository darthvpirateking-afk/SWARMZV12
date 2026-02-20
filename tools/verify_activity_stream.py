# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import os
import time
import json
from pathlib import Path

EVENTS_FILE = Path("data/activity/events.jsonl")

def verify_activity_stream():
    """Verify that events are being appended to the activity stream."""
    if not EVENTS_FILE.exists():
        print("Activity stream file does not exist.")
        return False

    with EVENTS_FILE.open("r", encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            print("No events recorded.")
            return False

        print(f"{len(lines)} events recorded.")
        return True

if __name__ == "__main__":
    verify_activity_stream()
