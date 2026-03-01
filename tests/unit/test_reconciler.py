# tests/unit/test_reconciler.py
import queue
import time
from nexusmon.hologram.hologram_reconciler import HologramReconciler, HologramPublisher


def test_apply_batch_node_upsert():
    q = queue.Queue()
    pub = HologramPublisher()
    rec = HologramReconciler(
        update_queue=q, publisher=pub, batch_ms=10, snapshot_interval=60
    )
    update = {
        "op": "node_upsert",
        "node": {"id": "A1", "health": 0.8, "last_seen": time.time()},
    }
    diff = rec._apply_batch([update])
    assert diff["nodes"]
    assert diff["nodes"][0]["health"] == 0.8
    assert rec.state["nodes"]["A1"]["health"] == 0.8
