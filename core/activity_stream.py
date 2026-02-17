# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import json
import os
import time
import uuid
from pathlib import Path

# Directory and file path for event storage
EVENTS_FILE = Path("data/activity/events.jsonl")
SESSION_FILE = "data/activity/session.json"

# Generate a unique session ID for this runtime session
SESSION_ID = str(uuid.uuid4())

# Ensure the directory exists
os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)

# Write session metadata
with open(SESSION_FILE, "w") as session_file:
    json.dump({
        "session_id": SESSION_ID,
        "start_time": time.time(),
        "pid": os.getpid()
    }, session_file)

def record_event(source, event_type, details):
    """
    Record an event to the activity stream.

    :param source: The source of the event (e.g., "ui", "cli", "runtime", "worker", "system").
    :param event_type: The type of event (e.g., "command", "file_write", "file_read", etc.).
    :param details: A dictionary containing additional details about the event.
    """
    try:
        event = {
            "timestamp": time.time(),
            "session_id": SESSION_ID,
            "source": source,
            "event_type": event_type,
            "details": details
        }
        with open(EVENTS_FILE, "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        # Fail-open: Silently skip if the file is unavailable
        pass

def record_event(event):
    """Append an event to the activity stream."""
    with EVENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
