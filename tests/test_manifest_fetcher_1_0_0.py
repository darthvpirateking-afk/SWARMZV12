"""Auto-generated manifest validation test for fetcher@1.0.0.json."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema


def test_manifest_fetcher_1_0_0() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    schema_path = repo_root / "schemas" / "agent-manifest.v1.json"
    manifest_path = repo_root / "config" / "manifests" / "fetcher@1.0.0.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8-sig"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))

    jsonschema.validate(instance=manifest, schema=schema)

    assert isinstance(manifest.get("inputs"), dict)
    assert isinstance(manifest.get("outputs"), dict)
    assert manifest.get("inputs")
    assert manifest.get("outputs")
