"""Additional branch coverage for registry hot-reload and CI gate logic."""
from __future__ import annotations

import json
from pathlib import Path

from core.registry import ManifestRegistry


def _manifest(manifest_id: str = "coverage@1.0.0") -> dict[str, object]:
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


def test_all_remove_clear_and_alias_get_path() -> None:
    reg = ManifestRegistry()
    payload = _manifest("aliased@1.0.0")
    payload["extensions"] = {"legacy_alias": "legacy_aliased"}

    ok, reason = reg.apply_update(
        manifest_id="aliased@1.0.0",
        manifest=payload,
        enforce_ci_gate=False,
    )
    assert ok is True
    assert reason == "applied"
    assert reg.get("legacy_aliased") is not None
    assert reg.all()
    assert reg.remove("missing@1.0.0") is False
    assert reg.remove("aliased@1.0.0") is True
    reg.clear()
    assert reg.all() == []


def test_validate_manifest_includes_source_and_json_path() -> None:
    reg = ManifestRegistry()
    bad = _manifest("bad@1.0.0")
    bad["spawn_policy"] = "not-valid"
    errors = reg.validate_manifest(bad, source="bad-file.json")
    assert errors
    assert "bad-file.json" in errors[0]
    assert "$.spawn_policy" in errors[0]


def test_current_sha_prefers_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    reg = ManifestRegistry()
    monkeypatch.setenv("GITHUB_SHA", "env-sha")
    assert reg._current_sha() == "env-sha"


def test_current_sha_uses_git_and_handles_exceptions(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    reg = ManifestRegistry()
    monkeypatch.delenv("GITHUB_SHA", raising=False)

    class _Result:
        stdout = "git-sha\n"

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: _Result())
    assert reg._current_sha() == "git-sha"

    def _raise(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("git unavailable")

    monkeypatch.setattr("subprocess.run", _raise)
    assert reg._current_sha() is None


def test_ci_gate_status_paths(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    reg = ManifestRegistry()
    status_path = tmp_path / "status.json"

    assert reg._ci_gate_allows(str(status_path)) is False

    status_path.write_text("{bad-json", encoding="utf-8")
    assert reg._ci_gate_allows(str(status_path)) is False

    status_path.write_text(json.dumps({"status": "fail", "sha": ""}), encoding="utf-8")
    assert reg._ci_gate_allows(str(status_path)) is False

    monkeypatch.setattr(reg, "_current_sha", lambda: "abc123")
    status_path.write_text(json.dumps({"status": "pass", "sha": "other"}), encoding="utf-8")
    assert reg._ci_gate_allows(str(status_path)) is False

    status_path.write_text(json.dumps({"status": "pass", "sha": "abc123"}), encoding="utf-8")
    assert reg._ci_gate_allows(str(status_path)) is True

    status_path.write_text(json.dumps({"status": "pass", "sha": ""}), encoding="utf-8")
    assert reg._ci_gate_allows(str(status_path)) is True


def test_apply_update_rejects_mismatch_and_validation_failure() -> None:
    reg = ManifestRegistry()
    payload = _manifest("wrong@1.0.0")

    ok, reason = reg.apply_update(
        manifest_id="different@1.0.0",
        manifest=payload,
        enforce_ci_gate=False,
    )
    assert ok is False
    assert reason == "manifest_id mismatch"

    bad = _manifest("bad@1.0.0")
    bad["spawn_policy"] = "invalid"
    ok2, reason2 = reg.apply_update(
        manifest_id="bad@1.0.0",
        manifest=bad,
        enforce_ci_gate=False,
    )
    assert ok2 is False
    assert reason2.startswith("validation_failed:")


def test_apply_update_listener_and_handle_manifest_updated(tmp_path: Path) -> None:
    reg = ManifestRegistry()
    status_path = tmp_path / "status.json"
    status_path.write_text(json.dumps({"status": "pass", "sha": ""}), encoding="utf-8")

    seen: list[str] = []

    def _ok_listener(actor: str, payload: dict[str, object]) -> None:
        seen.append(f"{actor}:{payload['id']}")

    def _bad_listener(actor: str, payload: dict[str, object]) -> None:
        raise RuntimeError("listener failure")

    reg.add_listener(_ok_listener)
    reg.add_listener(_bad_listener)

    ok, reason = reg.handle_manifest_updated(
        manifest_id="coverage@1.0.0",
        manifest=_manifest(),
        actor="watcher",
        ci_status_path=str(status_path),
    )
    assert ok is True
    assert reason == "applied"
    assert "watcher:coverage@1.0.0" in seen

    reg.remove_listener(_bad_listener)
    reg.remove_listener(_bad_listener)
