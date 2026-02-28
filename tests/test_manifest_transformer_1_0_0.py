"""Auto-generated manifest validation test for transformer@1.0.0.json."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema


def test_manifest_transformer_1_0_0() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    schema = json.loads((repo_root / "schemas" / "agent-manifest.v1.json").read_text(encoding="utf-8-sig"))
    manifest = json.loads((repo_root / "config" / "manifests" / "transformer@1.0.0.json").read_text(encoding="utf-8-sig"))

    jsonschema.validate(instance=manifest, schema=schema)

    assert isinstance(manifest.get("inputs"), dict)
    assert isinstance(manifest.get("outputs"), dict)
    assert manifest.get("inputs")
    assert manifest.get("outputs")
