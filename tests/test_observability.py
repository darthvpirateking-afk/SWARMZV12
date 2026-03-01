"""Observability and agent status/capabilities endpoint tests."""
from __future__ import annotations

import json
import logging

import pytest
from fastapi.testclient import TestClient

from core.observability import AgentEvent, ObservabilityEmitter, inputs_hash, redact


class _Candidate:
    def __init__(self, agent_id: str, composite: float) -> None:
        self.agent_id = agent_id
        self.composite = composite


def test_redact_nested_fields() -> None:
    payload = {
        "token": "abc",
        "nested": {"password": "p", "safe": 1},
        "api_key": "k",
    }
    result = redact(payload)
    assert result["token"] == "**REDACTED**"
    assert result["nested"]["password"] == "**REDACTED**"
    assert result["nested"]["safe"] == 1
    assert result["api_key"] == "**REDACTED**"


def test_inputs_hash_stable() -> None:
    a = inputs_hash({"x": 1, "y": 2})
    b = inputs_hash({"y": 2, "x": 1})
    assert a == b
    assert len(a) == 16


def test_agent_event_to_json_redacts_payload() -> None:
    event = AgentEvent(
        agent_id="helper1",
        trace_id="trace-1",
        event="router.decision",
        decision="selected=helper1",
        inputs_hash="abcd",
        outcome="success",
        payload={"secret": "value", "safe": "ok"},
    )
    data = json.loads(event.to_json())
    assert data["payload"]["secret"] == "**REDACTED**"
    assert data["payload"]["safe"] == "ok"


def test_success_sampling_uses_rate(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    emitter = ObservabilityEmitter(success_sample_rate=0.1)
    event = AgentEvent(
        agent_id="helper1",
        trace_id="trace-1",
        event="capability_router.decision",
        decision="selected=helper1",
        inputs_hash="abcd",
        outcome="success",
    )

    monkeypatch.setattr("core.observability.random.random", lambda: 0.99)
    with caplog.at_level(logging.INFO, logger="nexusmon"):
        emitter.emit(event)
    assert not caplog.records


def test_failure_events_always_emit(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    emitter = ObservabilityEmitter(success_sample_rate=0.0)
    event = AgentEvent(
        agent_id="helper1",
        trace_id="trace-1",
        event="security.violation",
        decision="rejected",
        inputs_hash="",
        outcome="rejected",
    )

    monkeypatch.setattr("core.observability.random.random", lambda: 0.99)
    with caplog.at_level(logging.INFO, logger="nexusmon"):
        emitter.emit(event)
    assert caplog.records


def test_emit_router_decision_logs_structured_payload(caplog: pytest.LogCaptureFixture) -> None:
    emitter = ObservabilityEmitter(success_sample_rate=1.0)
    candidates = [_Candidate("helper1", 0.92), _Candidate("reality_gate", 0.88)]

    with caplog.at_level(logging.INFO, logger="nexusmon"):
        emitter.emit_router_decision(
            agent_id="router",
            trace_id="trace-1",
            task_caps=["data.read"],
            candidates=candidates,
            selected="helper1",
            reason="best score",
            session_id="s1",
        )

    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "capability_router.decision"
    assert payload["payload"]["selected"] == "helper1"


def test_emit_security_violation_always_logged(caplog: pytest.LogCaptureFixture) -> None:
    emitter = ObservabilityEmitter(success_sample_rate=0.0)

    with caplog.at_level(logging.INFO, logger="nexusmon"):
        emitter.emit_security_violation(
            agent_id="helper1",
            trace_id="trace-1",
            violation="capability escalation",
        )

    assert caplog.records
    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "security.violation"
    assert payload["outcome"] == "rejected"


def test_agent_status_and_capabilities_endpoints() -> None:
    try:
        from swarmz_server import app
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"swarmz_server unavailable: {exc}")

    client = TestClient(app)

    status = client.get("/v1/agents/helper1/status")
    assert status.status_code == 200
    status_data = status.json()
    assert status_data["ok"] is True
    assert status_data["agent_id"] == "helper1"
    assert "status" in status_data

    caps = client.get("/v1/agents/helper1/capabilities")
    assert caps.status_code == 200
    cap_data = caps.json()
    assert cap_data["ok"] is True
    assert cap_data["agent_id"] == "helper1"
    assert "data.read" in cap_data["capabilities"]
