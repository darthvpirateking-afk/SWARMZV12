"""
NEXUSMON - Observability baseline.
Structured JSON logs. Trace IDs. Sampling. Redaction.
Core module: log field additions OK; removals require ADR.
"""
from __future__ import annotations

import hashlib
import json
import logging
import random
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("nexusmon")

REDACTED_FIELDS: frozenset[str] = frozenset({"password", "token", "secret", "api_key"})


def redact(payload: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact known-sensitive fields."""
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if key.lower() in REDACTED_FIELDS:
            out[key] = "**REDACTED**"
        elif isinstance(value, dict):
            out[key] = redact(value)
        else:
            out[key] = value
    return out


def inputs_hash(inputs: dict[str, Any]) -> str:
    """Stable SHA-256 hash of inputs for correlation without raw data."""
    serialized = json.dumps(inputs, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


@dataclass
class AgentEvent:
    """Base structured log event emitted by agent/runtime components."""

    agent_id: str
    trace_id: str
    event: str
    decision: str
    inputs_hash: str
    outcome: str
    error_mode: str | None = None
    session_id: str | None = None
    payload: dict[str, Any] | None = None

    def to_json(self) -> str:
        data = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "agent_id": self.agent_id,
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "event": self.event,
            "decision": self.decision,
            "inputs_hash": self.inputs_hash,
            "outcome": self.outcome,
            "error_mode": self.error_mode,
            "payload": redact(self.payload or {}),
        }
        compact = {k: v for k, v in data.items() if v is not None}
        return json.dumps(compact, separators=(",", ":"), sort_keys=True)


class ObservabilityEmitter:
    """
    Emits structured log events with configurable sampling.
    Failures are always emitted at 100%. Successes are sampled.
    """

    def __init__(self, success_sample_rate: float = 0.1) -> None:
        if not 0.0 <= success_sample_rate <= 1.0:
            raise ValueError("success_sample_rate must be between 0 and 1")
        self._success_sample_rate = success_sample_rate

    def emit(self, event: AgentEvent) -> None:
        """Emit a structured event with failure-priority sampling policy."""
        is_failure = event.outcome in ("failure", "fallback", "error", "rejected")
        should_emit = is_failure or (random.random() < self._success_sample_rate)
        if should_emit:
            logger.info(event.to_json())
            # Mirror events into cockpit telemetry feed
            try:
                import requests

                requests.post(
                    "http://localhost:8000/v1/canonical/cockpit/trace_feed",
                    json=json.loads(event.to_json()),
                    timeout=0.05,
                )
            except Exception:
                pass

    def emit_router_decision(
        self,
        agent_id: str,
        trace_id: str,
        task_caps: list[str],
        candidates: list[Any],
        selected: str,
        reason: str,
        session_id: str | None = None,
    ) -> None:
        self.emit(
            AgentEvent(
                agent_id=agent_id,
                trace_id=trace_id,
                session_id=session_id,
                event="capability_router.decision",
                decision=f"selected={selected}",
                inputs_hash=inputs_hash({"task_capabilities": task_caps}),
                outcome="success",
                payload={
                    "task_capabilities": task_caps,
                    "candidates": [
                        {"agent_id": candidate.agent_id, "composite": round(candidate.composite, 4)}
                        for candidate in candidates[:5]
                    ],
                    "selected": selected,
                    "reason": reason,
                },
            )
        )

    def emit_security_violation(
        self,
        agent_id: str,
        trace_id: str,
        violation: str,
        session_id: str | None = None,
    ) -> None:
        """Security violations are always logged at 100%."""
        self.emit(
            AgentEvent(
                agent_id=agent_id,
                trace_id=trace_id,
                session_id=session_id,
                event="security.violation",
                decision="rejected",
                inputs_hash="",
                outcome="rejected",
                error_mode="security_gate",
                payload={"violation": violation},
            )
        )
