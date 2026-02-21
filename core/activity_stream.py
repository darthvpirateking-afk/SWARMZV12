"""
SWARMZ Proprietary License
Copyright (c) 2026 SWARMZ. All Rights Reserved.

This software is proprietary and confidential to SWARMZ.
Unauthorized use, reproduction, or distribution is strictly prohibited.
Authorized SWARMZ developers may modify this file solely for contributions
to the official SWARMZ repository. See LICENSE for full terms.
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
