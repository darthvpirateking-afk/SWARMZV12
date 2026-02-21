"""
MIT License
Copyright (c) 2026 SWARMZ

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
import os
import time
import uuid
from pathlib import Path

from swarmz_runtime.core import telemetry

# Directory and file path for event storage
EVENTS_FILE = Path("data/activity/events.jsonl")
SESSION_FILE = "data/activity/session.json"

# Generate a unique session ID for this runtime session
SESSION_ID = None


def record_event(*args, **kwargs):
    """Bridge to telemetry.record_event with lenient signature.

    Accepts either (name, payload), (namespace, name, payload), or a single
    payload dict. Extra kwargs are ignored except for 'payload'.
    """
    try:
        if len(args) == 1 and isinstance(args[0], dict):
            telemetry.record_event("event", args[0])
            return
        if len(args) == 2:
            name, payload = args
            telemetry.record_event(
                str(name),
                payload if isinstance(payload, dict) else {"payload": payload},
            )
            return
        if len(args) >= 3:
            namespace, name, payload = args[0], args[1], args[2]
            telemetry.record_event(
                f"{namespace}:{name}",
                payload if isinstance(payload, dict) else {"payload": payload},
            )
            return
        payload = kwargs.get("payload", {})
        telemetry.record_event(
            "event", payload if isinstance(payload, dict) else {"payload": payload}
        )
    except Exception:
        # Fail silent to avoid crashing callers that treat telemetry as best-effort
        pass


def initialize_activity_stream():
    """Initialize the activity stream by setting up directories and session metadata."""
    global SESSION_ID
    SESSION_ID = str(uuid.uuid4())
    os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
    with open(SESSION_FILE, "w") as session_file:
        json.dump(
            {"session_id": SESSION_ID, "start_time": time.time(), "pid": os.getpid()},
            session_file,
        )


# No import-time side effects. Call initialize_activity_stream() explicitly when needed.
