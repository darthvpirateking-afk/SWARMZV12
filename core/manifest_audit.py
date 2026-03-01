"""Audit helpers for manifest updates and feature-flag evaluations."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

SENSITIVE_FIELDS = {"token", "secret", "password", "api_key"}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, nested in value.items():
            if key.lower() in SENSITIVE_FIELDS:
                out[key] = "**REDACTED**"
            else:
                out[key] = _redact(nested)
        return out
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


class ManifestAuditLogger:
    def __init__(self, path: str = "artifacts/manifest-audit.jsonl") -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _append(self, payload: dict[str, Any]) -> None:
        payload = _redact(payload)
        self._path.open("a", encoding="utf-8").write(json.dumps(payload, sort_keys=True) + "\n")

    def log_manifest_update(
        self,
        actor: str,
        manifest_id: str,
        old_value: Any,
        new_value: Any,
        trace_id: str,
        outcome: str = "success",
        full_trace: dict[str, Any] | None = None,
    ) -> None:
        event: dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "actor": actor,
            "manifest_id": manifest_id,
            "flag_id": None,
            "old_value": old_value,
            "new_value": new_value,
            "trace_id": trace_id,
            "outcome": outcome,
        }
        if outcome != "success" and full_trace is not None:
            event["full_trace"] = full_trace
        self._append(event)

    def log_flag_evaluation(
        self,
        actor: str,
        manifest_id: str,
        flag_id: str,
        old_value: Any,
        new_value: Any,
        trace_id: str,
        outcome: str = "success",
        full_trace: dict[str, Any] | None = None,
    ) -> None:
        event: dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "actor": actor,
            "manifest_id": manifest_id,
            "flag_id": flag_id,
            "old_value": old_value,
            "new_value": new_value,
            "trace_id": trace_id,
            "outcome": outcome,
        }
        if outcome != "success" and full_trace is not None:
            event["full_trace"] = full_trace
        self._append(event)
