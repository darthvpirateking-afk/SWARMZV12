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
SESSION_ID = None

def initialize_activity_stream():
    """Initialize the activity stream by setting up directories and session metadata."""
    global SESSION_ID
    SESSION_ID = str(uuid.uuid4())
    os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
    with open(SESSION_FILE, "w") as session_file:
        json.dump({
            "session_id": SESSION_ID,
            "start_time": time.time(),
            "pid": os.getpid()
        }, session_file)

# Ensure the initializer is explicitly called to set up the environment
# initialize_activity_stream()
