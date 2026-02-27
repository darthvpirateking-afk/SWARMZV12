"""hologram_test_harness.py — Standalone smoke test for the hologram state engine.

Run directly:
    python nexusmon/hologram/hologram_test_harness.py
"""
import time
from nexusmon.event_bus import EventBus
from nexusmon.feed_stream import FeedStream
from nexusmon.hologram.hologram_bootstrap import bootstrap_hologram


def run_smoke():
    eb = EventBus()
    fs = FeedStream(event_bus=eb)
    reconciler, publisher, ingestor, holo_app = bootstrap_hologram(feed_stream=fs, event_bus=eb)
    diffs = []

    def collector(ev):
        diffs.append(ev)

    publisher.subscribe(collector)

    eb.publish({"type": "agent_heartbeat", "agent": "ATENGIC", "data": {"health": 0.95, "metrics": {"cpu": 0.1}}})
    eb.publish({"type": "mission_created", "agent": "ATENGIC", "data": {"mission": {"id": "m1", "type": "research", "status": "pending"}}})
    time.sleep(1.0)

    assert any(d.get("type") == "hologram.diff" for d in diffs), "no diffs published"
    snap = reconciler.get_latest_snapshot()
    print("snapshot nodes:", len(snap["nodes"]))
    print("hologram smoke test OK")


if __name__ == "__main__":
    run_smoke()
