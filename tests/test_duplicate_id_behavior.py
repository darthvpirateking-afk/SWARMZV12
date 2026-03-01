"""Duplicate manifest id behavior tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.registry import ManifestRegistry


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
        "feature_flags": {},
        "extensions": {},
    }


def test_duplicate_ids_rejected_by_default(tmp_path: Path) -> None:
    payload = _manifest("dup@1.0.0")
    (tmp_path / "a.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps(payload), encoding="utf-8")

    reg = ManifestRegistry()
    with pytest.raises(ValueError, match="Duplicate manifest id"):
        reg.load_all(str(tmp_path), reject_duplicates=True)


def test_duplicate_ids_ignored_when_reject_disabled(tmp_path: Path) -> None:
    payload = _manifest("dup@1.0.0")
    (tmp_path / "a.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps(payload), encoding="utf-8")

    reg = ManifestRegistry()
    loaded = reg.load_all(str(tmp_path), reject_duplicates=False)
    assert len(loaded) == 1
