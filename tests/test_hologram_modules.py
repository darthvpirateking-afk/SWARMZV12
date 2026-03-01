"""tests/test_hologram_modules.py — Unit tests for the NEXUSMON hologram state engine.

Covers:
  - core.event_bus  — EventBus re-export
  - core.feed_stream — FeedStream subscribe/publish
  - HologramIngestor — event normalization
  - HologramReconciler — batch apply, tick increment, EWMA health
  - HologramPublisher — subscriber fan-out
  - bootstrap_hologram — no-app wiring (standalone mode)
"""

import queue
import time

# ── dependency layer ──────────────────────────────────────────────────────────

class TestEventBusReexport:
    def test_import_event_bus(self):
        from core.event_bus import EventBus
        assert EventBus is not None

    def test_event_bus_is_simple_event_bus(self):
        from core.event_bus import EventBus
        from core.agent_runtime import SimpleEventBus
        assert EventBus is SimpleEventBus

    def test_nexusmon_event_bus_reexport(self):
        from nexusmon.event_bus import EventBus
        from core.agent_runtime import SimpleEventBus
        assert EventBus is SimpleEventBus


class TestFeedStream:
    def setup_method(self):
        from core.event_bus import EventBus
        from core.feed_stream import FeedStream
        self.eb = EventBus()
        self.fs = FeedStream(event_bus=self.eb)

    def test_import_feed_stream(self):
        from core.feed_stream import FeedStream
        assert FeedStream is not None

    def test_nexusmon_feed_stream_reexport(self):
        from nexusmon.feed_stream import FeedStream
        from core.feed_stream import FeedStream as CoreFeedStream
        assert FeedStream is CoreFeedStream

    def test_subscribe_receives_events(self):
        received = []
        self.fs.subscribe(received.append)
        self.eb.publish({"type": "test", "v": 1})
        assert len(received) == 1
        assert received[0]["v"] == 1

    def test_publish_via_feed_stream(self):
        received = []
        self.fs.subscribe(received.append)
        self.fs.publish({"type": "ping"})
        assert len(received) == 1

    def test_recent_delegates_to_bus(self):
        self.eb.publish({"type": "x"})
        result = self.fs.recent(10)
        assert isinstance(result, list)
        assert len(result) >= 1


# ── HologramIngestor ──────────────────────────────────────────────────────────

class TestHologramIngestor:
    def setup_method(self):
        from core.event_bus import EventBus
        from core.feed_stream import FeedStream
        from nexusmon.hologram.hologram_ingestor import HologramIngestor
        self.eb = EventBus()
        self.fs = FeedStream(event_bus=self.eb)
        self.q = queue.Queue()
        self.ingestor = HologramIngestor(feed_stream=self.fs, update_queue=self.q, batch_ms=50)

    def _publish_and_drain(self, event):
        self.eb.publish(event)
        return self.q.get(timeout=1.0)

    def test_agent_heartbeat_becomes_node_upsert(self):
        ev = {"type": "agent_heartbeat", "agent": "AGEN1", "data": {"health": 0.9, "metrics": {}}}
        upd = self._publish_and_drain(ev)
        assert upd["op"] == "node_upsert"
        assert upd["node"]["id"] == "AGEN1"
        assert upd["node"]["type"] == "agent"

    def test_cognition_becomes_node_upsert(self):
        ev = {"type": "cognition", "agent": "AGEN2", "data": {"health": 0.5}}
        upd = self._publish_and_drain(ev)
        assert upd["op"] == "node_upsert"

    def test_mission_started_becomes_mission_update(self):
        ev = {"type": "mission_started", "agent": "AGEN3", "data": {"mission": {"id": "m1"}}}
        upd = self._publish_and_drain(ev)
        assert upd["op"] == "mission_update"
        assert upd["mission"]["id"] == "m1"

    def test_link_add_becomes_link_upsert(self):
        ev = {"type": "link_add", "agent": "AGEN4", "data": {"from": "A", "to": "B"}}
        upd = self._publish_and_drain(ev)
        assert upd["op"] == "link_upsert"

    def test_error_event_becomes_event_log(self):
        ev = {"type": "error", "agent": "AGEN5", "data": {}}
        upd = self._publish_and_drain(ev)
        assert upd["op"] == "event_log"

    def test_unknown_event_becomes_event_log(self):
        ev = {"type": "something_random", "agent": "X", "data": {}}
        upd = self._publish_and_drain(ev)
        assert upd["op"] == "event_log"

    def test_meta_contains_source_and_ts(self):
        ev = {"type": "agent_heartbeat", "agent": "AGEN6", "data": {"health": 1.0}}
        upd = self._publish_and_drain(ev)
        assert upd["meta"]["source"] == "AGEN6"
        assert "ts" in upd["meta"]

    def test_node_health_passthrough(self):
        ev = {"type": "agent_heartbeat", "agent": "H1", "data": {"health": 0.75}}
        upd = self._publish_and_drain(ev)
        assert upd["node"]["health"] == 0.75


# ── HologramPublisher ─────────────────────────────────────────────────────────

class TestHologramPublisher:
    def setup_method(self):
        from nexusmon.hologram.hologram_reconciler import HologramPublisher
        self.pub = HologramPublisher()

    def test_subscribe_and_receive_diff(self):
        received = []
        self.pub.subscribe(received.append)
        self.pub.publish_diff({"tick": 1, "nodes": []})
        assert len(received) == 1
        assert received[0]["type"] == "hologram.diff"

    def test_subscribe_and_receive_snapshot(self):
        received = []
        self.pub.subscribe(received.append)
        self.pub.publish_snapshot({"nodes": [], "meta": {}})
        assert len(received) == 1
        assert received[0]["type"] == "hologram.snapshot"

    def test_multiple_subscribers(self):
        a, b = [], []
        self.pub.subscribe(a.append)
        self.pub.subscribe(b.append)
        self.pub.publish_diff({"tick": 2})
        assert len(a) == 1
        assert len(b) == 1

    def test_faulty_subscriber_does_not_break_others(self):
        def bad(ev):
            raise RuntimeError("boom")
        good = []
        self.pub.subscribe(bad)
        self.pub.subscribe(good.append)
        self.pub.publish_diff({"tick": 3})
        assert len(good) == 1


# ── HologramReconciler ────────────────────────────────────────────────────────

class TestHologramReconciler:
    def setup_method(self):
        from nexusmon.hologram.hologram_reconciler import HologramReconciler, HologramPublisher
        self.q = queue.Queue()
        self.pub = HologramPublisher()
        self.rec = HologramReconciler(update_queue=self.q, publisher=self.pub, batch_ms=100, snapshot_interval=999)

    def _node_upsert(self, agent_id, health=1.0):
        return {"op": "node_upsert", "node": {"id": agent_id, "type": "agent", "health": health, "last_seen": time.time()}, "meta": {"ts": time.time()}}

    def test_apply_batch_increments_tick(self):
        batch = [self._node_upsert("A1")]
        diff = self.rec._apply_batch(batch)
        assert diff["tick"] == 1
        assert self.rec.state["meta"]["tick"] == 1

    def test_node_upsert_stores_node(self):
        batch = [self._node_upsert("A2", health=0.8)]
        self.rec._apply_batch(batch)
        assert "A2" in self.rec.state["nodes"]

    def test_ewma_health_applied_on_second_update(self):
        batch1 = [self._node_upsert("A3", health=1.0)]
        self.rec._apply_batch(batch1)
        batch2 = [self._node_upsert("A3", health=0.0)]
        self.rec._apply_batch(batch2)
        h = self.rec.state["nodes"]["A3"]["health"]
        # EWMA: 1.0 * 0.7 + 0.0 * 0.3 = 0.7
        assert abs(h - 0.7) < 1e-9

    def test_mission_update_stored(self):
        upd = {"op": "mission_update", "mission": {"id": "m1", "status": "running"}, "meta": {"ts": time.time()}}
        self.rec._apply_batch([upd])
        assert "m1" in self.rec.state["missions"]

    def test_link_upsert_stored(self):
        upd = {"op": "link_upsert", "link": {"id": "lnk1", "from": "A", "to": "B"}, "meta": {"ts": time.time()}}
        self.rec._apply_batch([upd])
        assert "lnk1" in self.rec.state["links"]

    def test_event_log_stored_in_deque(self):
        upd = {"op": "event_log", "event": {"type": "error", "id": "e1"}}
        self.rec._apply_batch([upd])
        assert len(self.rec.state["events"]) == 1

    def test_diff_nodes_list_populated(self):
        batch = [self._node_upsert("A4")]
        diff = self.rec._apply_batch(batch)
        assert len(diff["nodes"]) >= 1

    def test_diff_meta_present(self):
        batch = [self._node_upsert("A5")]
        diff = self.rec._apply_batch(batch)
        assert "meta" in diff

    def test_snapshot_contains_required_keys(self):
        batch = [self._node_upsert("A6")]
        self.rec._apply_batch(batch)
        snap = self.rec._snapshot()
        for key in ("nodes", "links", "missions", "events", "meta"):
            assert key in snap

    def test_get_latest_snapshot_fallback_to_live(self):
        snap = self.rec.get_latest_snapshot()
        assert "nodes" in snap

    def test_reconciler_loop_publishes_diffs(self):
        diffs = []
        self.pub.subscribe(diffs.append)
        self.rec.start()
        self.q.put(self._node_upsert("L1"))
        time.sleep(0.6)
        self.rec.stop()
        assert any(d.get("type") == "hologram.diff" for d in diffs)


# ── bootstrap_hologram (standalone) ──────────────────────────────────────────

class TestBootstrapHologram:
    def setup_method(self):
        from core.event_bus import EventBus
        from core.feed_stream import FeedStream
        from nexusmon.hologram.hologram_bootstrap import bootstrap_hologram
        self.eb = EventBus()
        self.fs = FeedStream(event_bus=self.eb)
        self.bootstrap_hologram = bootstrap_hologram

    def test_bootstrap_returns_four_tuple_without_app(self):
        result = self.bootstrap_hologram(feed_stream=self.fs, event_bus=self.eb)
        assert len(result) == 4

    def test_bootstrap_components_not_none(self):
        reconciler, publisher, ingestor, holo_app = self.bootstrap_hologram(feed_stream=self.fs, event_bus=self.eb)
        assert reconciler is not None
        assert publisher is not None
        assert ingestor is not None
        assert holo_app is not None

    def test_bootstrap_reconciler_is_running(self):
        reconciler, publisher, ingestor, holo_app = self.bootstrap_hologram(feed_stream=self.fs, event_bus=self.eb)
        assert reconciler.running is True
        reconciler.stop()

    def test_bootstrap_ingestor_receives_events(self):
        reconciler, publisher, ingestor, holo_app = self.bootstrap_hologram(feed_stream=self.fs, event_bus=self.eb)
        received = []
        publisher.subscribe(received.append)
        self.eb.publish({"type": "agent_heartbeat", "agent": "BT1", "data": {"health": 1.0}})
        time.sleep(0.5)
        reconciler.stop()
        assert any(r.get("type") == "hologram.diff" for r in received)

    def test_bootstrap_with_app_returns_three_tuple(self):
        # Use a real FastAPI app to test the mount path
        from fastapi import FastAPI
        dummy_app = FastAPI()
        result = self.bootstrap_hologram(feed_stream=self.fs, event_bus=self.eb, main_fastapi_app=dummy_app)
        assert len(result) == 3
        reconciler, publisher, ingestor = result
        reconciler.stop()

    def test_get_latest_snapshot_after_events(self):
        reconciler, publisher, ingestor, holo_app = self.bootstrap_hologram(feed_stream=self.fs, event_bus=self.eb)
        self.eb.publish({"type": "agent_heartbeat", "agent": "SNAP1", "data": {"health": 0.9}})
        time.sleep(0.5)
        snap = reconciler.get_latest_snapshot()
        reconciler.stop()
        assert "nodes" in snap
        assert "meta" in snap
