from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_agent_contract_mirror_matches_canonical() -> None:
    canonical = _load_json(ROOT / ".continue/agents/nexusmon-builder.json")
    mirror = _load_json(ROOT / "nexusmon-builder.json")
    assert canonical == mirror


def test_registry_mirror_matches_canonical() -> None:
    canonical = _load_json(ROOT / "nexusmon/workers/registry.json")
    mirror = _load_json(ROOT / "registry.json")
    assert canonical == mirror


def test_template_mirror_matches_canonical() -> None:
    canonical = _load_json(ROOT / "nexusmon/missions/templates/build_module.json")
    mirror = _load_json(ROOT / "build_module.json")
    assert canonical == mirror
