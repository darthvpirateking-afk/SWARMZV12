from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSET_MAP = ROOT / "cockpit" / "assets" / "asset_map.json"


def test_asset_map_exists() -> None:
    assert ASSET_MAP.exists()


def test_all_referenced_assets_exist() -> None:
    payload = json.loads(ASSET_MAP.read_text(encoding="utf-8-sig"))
    for key in ("js_bundles", "css_bundles", "images", "mode_components"):
        for path in payload.get(key, []):
            target = ROOT / str(path).lstrip("/")
            assert target.exists(), path


def test_no_broken_references() -> None:
    payload = json.loads(ASSET_MAP.read_text(encoding="utf-8-sig"))
    broken: list[str] = []
    for key in ("js_bundles", "css_bundles", "images", "mode_components"):
        for path in payload.get(key, []):
            target = ROOT / str(path).lstrip("/")
            if not target.exists():
                broken.append(path)
    assert not broken
