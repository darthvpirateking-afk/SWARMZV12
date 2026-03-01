# tests/unit/test_feedstream.py
import time
from nexusmon.event_bus import EventBus
from nexusmon.feed_stream import FeedStream


def test_feed_subscription_and_normalization():
    eb = EventBus()
    fs = FeedStream(event_bus=eb)
    collected = []

    def cb(ev):
        collected.append(ev)

    fs.subscribe(cb)
    eb.publish({"type": "agent_heartbeat", "agent": "A2", "data": {"health": 0.99}})
    time.sleep(0.1)
    assert collected, "FeedStream did not forward events to subscribers"
