# tests/integration/test_hologram_pipeline.py
import time
from nexusmon.event_bus import EventBus
from nexusmon.feed_stream import FeedStream
from nexusmon.hologram.hologram_bootstrap import bootstrap_hologram


def test_end_to_end_smoke():
    eb = EventBus()
    fs = FeedStream(event_bus=eb)
    reconciler, publisher, ingestor, holo_app = bootstrap_hologram(
        feed_stream=fs, event_bus=eb
    )
    diffs = []
    publisher.subscribe(lambda d: diffs.append(d))
    try:
        eb.publish({
            "type": "agent_heartbeat",
            "agent": "ATENGIC",
            "data": {"health": 0.95, "metrics": {"cpu": 0.1}},
        })
        eb.publish({
            "type": "mission_created",
            "agent": "ATENGIC",
            "data": {"mission": {"id": "m1", "type": "research", "status": "pending"}},
        })
        time.sleep(1.0)
        assert any(d.get("type") == "hologram.diff" for d in diffs), \
            "no hologram diffs published"
        snap = reconciler.get_latest_snapshot()
        assert isinstance(snap, dict)
    finally:
        reconciler.stop()
