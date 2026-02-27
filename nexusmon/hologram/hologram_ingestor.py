import time
import queue
import uuid


class HologramIngestor:
    def __init__(self, feed_stream, update_queue=None, batch_ms=100):
        self.feed_stream = feed_stream
        self.update_queue = update_queue or queue.Queue()
        self.batch_ms = batch_ms
        self.feed_stream.subscribe(self._on_event)

    def _on_event(self, event):
        update = self._normalize(event)
        self.update_queue.put(update)

    def _normalize(self, event):
        etype = event.get("type")
        base = {
            "id": str(uuid.uuid4()),
            "ts": event.get("timestamp", time.time()),
            "source": event.get("agent"),
            "type": etype,
            "raw": event.get("payload", event.get("data", {}))
        }

        if etype in ("cognition", "agent_heartbeat"):
            return {"op": "node_upsert", "node": {
                "id": base["source"],
                "type": "agent",
                "health": base["raw"].get("health"),
                "metrics": base["raw"].get("metrics", {}),
                "persona": base["raw"].get("persona"),
                "last_seen": base["ts"]
            }, "meta": base}

        if etype is not None and etype.startswith("mission_"):
            mission = base["raw"].get("mission") or base["raw"]
            return {"op": "mission_update", "mission": mission, "meta": base}

        if etype in ("link_add", "link_update"):
            link = base["raw"]
            return {"op": "link_upsert", "link": link, "meta": base}

        if etype in ("error", "mission_failed", "validator_reject"):
            return {"op": "event_log", "event": base}

        return {"op": "event_log", "event": base}
