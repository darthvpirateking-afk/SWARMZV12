# tests/unit/test_ingestor.py
import time
import queue
from nexusmon.hologram.hologram_ingestor import HologramIngestor


class DummyFeed:
    def __init__(self):
        self.subs = []

    def subscribe(self, cb):
        self.subs.append(cb)

    def emit(self, ev):
        for cb in self.subs:
            cb(ev)


def test_normalize_agent_heartbeat():
    feed = DummyFeed()
    q = queue.Queue()
    ing = HologramIngestor(feed_stream=feed, update_queue=q)
    ev = {
        "type": "agent_heartbeat",
        "agent": "A1",
        "timestamp": time.time(),
        "data": {"health": 0.9, "metrics": {"cpu": 0.1}},
    }
    feed.emit(ev)
    upd = q.get(timeout=1)
    assert upd["op"] == "node_upsert"
    assert upd["node"]["id"] == "A1"
    assert "health" in upd["node"]
