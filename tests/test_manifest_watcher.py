"""Manifest watcher event and hot-reload tests."""
from __future__ import annotations

import json
from pathlib import Path

from core.manifest_watcher import ManifestWatcher, attach_registry_hot_reload
from core.registry import registry


def _manifest(manifest_id: str) -> dict:
    return {
        "id": manifest_id,
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


def test_watcher_emits_update_and_registry_applies_with_passed_ci(tmp_path: Path) -> None:
    registry.clear()

    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    status_path = tmp_path / "manifest-validation-status.json"
    status_path.write_text(json.dumps({"status": "pass", "sha": ""}), encoding="utf-8")

    manifest_id = "watcher-test@1.0.0"
    manifest_path = manifests_dir / "watcher-test.json"
    manifest_path.write_text(json.dumps(_manifest(manifest_id)), encoding="utf-8")

    seen: list[tuple[str, str]] = []
    watcher = ManifestWatcher(
        manifests_path=str(manifests_dir),
        poll_seconds=0.1,
        ci_status_path=str(status_path),
    )
    attach_registry_hot_reload(watcher)
    watcher.add_listener(lambda event, mid, _payload: seen.append((event, mid)))

    watcher.poll_once()

    assert ("manifest.updated", manifest_id) in seen
    assert registry.get(manifest_id) is not None


def test_watcher_does_not_apply_invalid_manifest(tmp_path: Path) -> None:
    registry.clear()

    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    status_path = tmp_path / "manifest-validation-status.json"
    status_path.write_text(json.dumps({"status": "pass", "sha": ""}), encoding="utf-8")

    manifest_path = manifests_dir / "invalid.json"
    invalid = _manifest("invalid-test@1.0.0")
    invalid["spawn_policy"] = "invalid"
    manifest_path.write_text(json.dumps(invalid), encoding="utf-8")

    watcher = ManifestWatcher(
        manifests_path=str(manifests_dir),
        poll_seconds=0.1,
        ci_status_path=str(status_path),
    )
    attach_registry_hot_reload(watcher)

    watcher.poll_once()

    assert registry.get("invalid-test@1.0.0") is None
