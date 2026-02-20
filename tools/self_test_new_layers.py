# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from core.activity_stream import record_event


def test_activity_stream():
    """Test the activity stream by recording a test event."""
    test_event = {"event": "test_event", "timestamp": "2026-02-17T00:00:00Z"}
    record_event(test_event)
    print("Test event recorded successfully.")


if __name__ == "__main__":
    test_activity_stream()
