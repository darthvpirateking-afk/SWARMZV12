# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Defines the canonical event schema and versioning for SWARMZ.
"""

import hashlib
import json

EVENT_SCHEMA_VERSION = "1.0"

def compute_event_id(event):
    """Compute a unique event ID based on the canonical JSON representation."""
    event_copy = event.copy()
    event_copy.pop("event_id", None)
    canonical_json = json.dumps(event_copy, sort_keys=True)
    return hashlib.sha256(canonical_json.encode()).hexdigest()

def validate_event(event):
    """Validate an event against the canonical schema."""
    required_fields = ["schema_version", "event_id", "event_type", "timestamp"]
    for field in required_fields:
        if field not in event:
            return False, f"Missing required field: {field}"
    if event["schema_version"] != EVENT_SCHEMA_VERSION:
        return False, "Schema version mismatch"
    return True, "Valid event"
