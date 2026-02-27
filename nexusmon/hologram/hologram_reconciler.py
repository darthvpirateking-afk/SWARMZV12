import json
import os
import time
import threading
from collections import deque
from pathlib import Path

# Resolve snapshot directory from env var so Docker / k8s volume mounts work.
# Falls back to a local directory when running outside containers.
SNAPSHOT_DIR = Path(os.environ.get("HLOG_SNAPSHOT_DIR", "hologram_snapshots"))
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


class HologramPublisher:
    def __init__(self):
        self.subscribers = []

    def publish_diff(self, diff):
        for cb in list(self.subscribers):
            try:
                cb({"type": "hologram.diff", "tick": diff.get("tick"), "diff": diff})
            except Exception:
                pass

    def publish_snapshot(self, snapshot):
        for cb in list(self.subscribers):
            try:
                cb({"type": "hologram.snapshot", "snapshot": snapshot})
            except Exception:
                pass

    def subscribe(self, cb):
        self.subscribers.append(cb)


class HologramReconciler:
    def __init__(self, update_queue, publisher, batch_ms=200, snapshot_interval=5):
        self.update_queue = update_queue
        self.publisher = publisher
        self.batch_ms = batch_ms / 1000.0
        self.snapshot_interval = snapshot_interval
        self.state = {
            "nodes": {},
            "links": {},
            "missions": {},
            "events": deque(maxlen=1000),
            "meta": {"version": "1.0.0", "tick": 0, "generated_at": time.time(), "health": "green"}
        }
        self.lock = threading.Lock()
        self.running = False
        self._last_snapshot = time.time()

    def start(self):
        self.running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            batch = []
            start = time.time()
            while time.time() - start < self.batch_ms:
                try:
                    item = self.update_queue.get(timeout=self.batch_ms)
                    batch.append(item)
                except Exception:
                    break
            if batch:
                diff = self._apply_batch(batch)
                if diff:
                    self.publisher.publish_diff(diff)
            if time.time() - self._last_snapshot >= self.snapshot_interval:
                snap = self._snapshot()
                self.publisher.publish_snapshot(snap)
                self._last_snapshot = time.time()

    def _apply_batch(self, batch):
        diff = {"tick": self.state["meta"]["tick"] + 1, "nodes": [], "links": [], "missions": [], "events": []}
        with self.lock:
            for upd in batch:
                op = upd.get("op")
                if op == "node_upsert":
                    node = upd["node"]
                    nid = node["id"]
                    existing = self.state["nodes"].get(nid, {})
                    if "health" in node and existing:
                        prev = existing.get("health", node["health"])
                        existing["health"] = (prev * 0.7) + (node["health"] * 0.3) if node["health"] is not None else prev
                    else:
                        existing.update(node)
                    existing["last_seen"] = node.get("last_seen", time.time())
                    self.state["nodes"][nid] = existing
                    diff["nodes"].append(existing)

                elif op == "link_upsert":
                    link = upd["link"]
                    lid = link.get("id") or f"{link.get('from')}-{link.get('to')}"
                    link["last_seen"] = upd["meta"]["ts"]
                    self.state["links"][lid] = link
                    diff["links"].append(link)

                elif op == "mission_update":
                    mission = upd["mission"]
                    mid = mission.get("id")
                    mission["timestamps"] = mission.get("timestamps", {})
                    self.state["missions"][mid] = mission
                    diff["missions"].append(mission)

                elif op == "event_log":
                    ev = upd["event"]
                    self.state["events"].append(ev)
                    diff["events"].append(ev)

            self.state["meta"]["tick"] += 1
            self.state["meta"]["generated_at"] = time.time()
            diff["meta"] = dict(self.state["meta"])

        return diff

    def _snapshot(self):
        with self.lock:
            snap = {
                "nodes": list(self.state["nodes"].values()),
                "links": list(self.state["links"].values()),
                "missions": list(self.state["missions"].values()),
                "events": list(self.state["events"]),
                "meta": dict(self.state["meta"])
            }
        ts = int(time.time())
        path = SNAPSHOT_DIR / f"snapshot_{ts}.json"
        path.write_text(json.dumps(snap))
        snaps = sorted(SNAPSHOT_DIR.glob("snapshot_*.json"), key=lambda p: p.stat().st_mtime)
        while len(snaps) > 10:
            snaps.pop(0).unlink()
        return snap

    def get_latest_snapshot(self):
        snaps = sorted(SNAPSHOT_DIR.glob("snapshot_*.json"), key=lambda p: p.stat().st_mtime)
        if not snaps:
            return self._snapshot()
        return json.loads(snaps[-1].read_text())
