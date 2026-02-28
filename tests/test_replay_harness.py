"""Replay harness tests for structured trace fixtures."""
from __future__ import annotations

import json
from pathlib import Path

TRACE_DIR = Path(__file__).resolve().parent / "fixtures" / "traces"
REQUIRED_FIELDS = {"ts", "agent_id", "trace_id", "event", "decision", "inputs_hash", "outcome"}


def _iter_trace_events() -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for trace_file in sorted(TRACE_DIR.glob("*.jsonl")):
        for line in trace_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            assert isinstance(payload, dict)
            events.append(payload)
    return events


def test_trace_fixtures_have_required_fields() -> None:
    events = _iter_trace_events()
    assert events
    for event in events:
        assert REQUIRED_FIELDS.issubset(event.keys())


def test_trace_id_chain_parent_child_spawn() -> None:
    events = _iter_trace_events()
    trace_ids = {str(event["trace_id"]) for event in events}
    assert "trace-demo-001" in trace_ids

    spawn_events = [event for event in events if event.get("event") == "agent.spawn"]
    assert spawn_events

    spawn = spawn_events[0]
    payload = spawn.get("payload", {})
    assert isinstance(payload, dict)
    assert payload.get("parent_agent_id") == "mission_engine"
    assert payload.get("child_agent_id") == "helper1"
