"""Hot reload and CI-gate behavior tests for registry updates."""
from __future__ import annotations

import json
from pathlib import Path

from core.registry import ManifestRegistry


def _manifest() -> dict:
    return {
        "id": "hotreload@1.0.0",
        "version": "1.0.0",
        "capabilities": ["data.read"],
        "inputs": {"query": {"type": "string"}},
        "outputs": {"result": {"type": "object"}},
        "spawn_policy": "manual",
        "constraints": {},
        "error_modes": {},
        "feature_flags": {"enabled": True, "rollout_policy": {}},
        "extensions": {},
    }


def test_hot_update_applies_when_ci_artifact_passes(tmp_path: Path) -> None:
    reg = ManifestRegistry()

    status = tmp_path / "status.json"
    status.write_text(json.dumps({"status": "pass", "sha": ""}), encoding="utf-8")

    ok, reason = reg.apply_update(
        manifest_id="hotreload@1.0.0",
        manifest=_manifest(),
        actor="test",
        ci_status_path=str(status),
        enforce_ci_gate=True,
    )
    assert ok is True
    assert reason == "applied"
    assert reg.get("hotreload@1.0.0") is not None


def test_hot_update_blocked_when_ci_artifact_fails(tmp_path: Path) -> None:
    reg = ManifestRegistry()

    status = tmp_path / "status.json"
    status.write_text(json.dumps({"status": "fail", "sha": ""}), encoding="utf-8")

    ok, reason = reg.apply_update(
        manifest_id="hotreload@1.0.0",
        manifest=_manifest(),
        actor="test",
        ci_status_path=str(status),
        enforce_ci_gate=True,
    )
    assert ok is False
    assert reason == "ci_gate_blocked"
