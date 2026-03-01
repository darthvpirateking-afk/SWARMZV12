from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from backend.symbolic_manifest_schema import validate_manifest

LIFE_ROOT = Path(__file__).resolve().parents[1] / "life"

LIFE_SYSTEM_GROUPS: tuple[str, ...] = (
    "diary",
    "breath",
    "heart",
    "memory_palace",
    "awakening_loop",
    "witness",
    "guardians",
    "dream_seed",
    "sovereign_mirror",
    "cosmic",
    "species",
    "voice",
)


def _read_manifest(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return validate_manifest(data)


def discover_life_groups() -> List[str]:
    if not LIFE_ROOT.exists():
        return []
    return sorted(
        group for group in LIFE_SYSTEM_GROUPS if (LIFE_ROOT / group).exists()
    )


def list_life_entries(group: str) -> List[Dict[str, Any]]:
    if group not in LIFE_SYSTEM_GROUPS:
        raise KeyError("unknown life group")

    group_path = LIFE_ROOT / group
    if not group_path.exists():
        raise FileNotFoundError("life group not found")

    entries: list[dict[str, Any]] = []
    for manifest_path in sorted(group_path.rglob("manifest.json")):
        relative = manifest_path.relative_to(group_path)
        if len(relative.parts) == 1:
            entry_id = "__root__"
        else:
            entry_id = relative.parts[0]
        manifest = _read_manifest(manifest_path)
        entries.append(
            {
                "group": group,
                "entry_id": entry_id,
                "path": str(manifest_path.relative_to(LIFE_ROOT.parent)),
                "manifest": manifest,
            }
        )
    entries.sort(key=lambda item: (item["entry_id"], item["path"]))
    return entries


def get_life_entry(group: str, entry_id: str) -> Dict[str, Any]:
    for entry in list_life_entries(group):
        manifest = entry["manifest"]
        if (
            entry["entry_id"] == entry_id
            or manifest.get("id") == entry_id
            or (entry_id == "manifest" and entry["entry_id"] == "__root__")
        ):
            return entry
    raise FileNotFoundError("life entry not found")

