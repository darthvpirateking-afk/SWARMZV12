from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from backend.symbolic_manifest_schema import validate_manifest

SYMBOLIC_ROOT = Path(__file__).resolve().parents[1] / "symbolic"

SYMBOLIC_FAMILIES: tuple[str, ...] = (
    "pantheons",
    "grimoires",
    "relics",
    "sigils",
    "archives",
    "federation",
    "cryptids",
    "lost_civilizations",
    "multiverse",
    "trance_modes",
    "synchronicity",
    "altar_modes",
    "lineage",
    "calendars",
    "reconciliation",
    "quantum",
    "xenolinguistics",
)


def _read_manifest(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return validate_manifest(data)


def discover_families() -> List[str]:
    if not SYMBOLIC_ROOT.exists():
        return []
    families = [family for family in SYMBOLIC_FAMILIES if (SYMBOLIC_ROOT / family).exists()]
    return sorted(families)


def get_family_manifest(family: str) -> Dict[str, Any]:
    if family not in SYMBOLIC_FAMILIES:
        raise KeyError("unknown family")
    manifest_path = SYMBOLIC_ROOT / family / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("family manifest not found")
    manifest = _read_manifest(manifest_path)
    return {
        "family": family,
        "path": str(manifest_path.relative_to(SYMBOLIC_ROOT.parent)),
        "manifest": manifest,
    }


def list_family_entries(family: str) -> List[Dict[str, Any]]:
    if family not in SYMBOLIC_FAMILIES:
        raise KeyError("unknown family")

    family_path = SYMBOLIC_ROOT / family
    if not family_path.exists():
        raise FileNotFoundError("family directory not found")

    entries: list[dict[str, Any]] = []
    for manifest_path in sorted(family_path.rglob("manifest.json")):
        if manifest_path == family_path / "manifest.json":
            continue
        relative = manifest_path.relative_to(family_path)
        entry_id = relative.parts[0]
        manifest = _read_manifest(manifest_path)
        entries.append(
            {
                "family": family,
                "entry_id": entry_id,
                "path": str(manifest_path.relative_to(SYMBOLIC_ROOT.parent)),
                "manifest": manifest,
            }
        )
    entries.sort(key=lambda item: (item["entry_id"], item["path"]))
    return entries


def get_entry_manifest(family: str, entry_id: str) -> Dict[str, Any]:
    for entry in list_family_entries(family):
        if entry["entry_id"] == entry_id:
            return entry
    raise FileNotFoundError("entry manifest not found")
