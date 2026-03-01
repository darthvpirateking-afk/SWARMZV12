from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = PROJECT_ROOT / "core" / "manifests" / "registry.json"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class ManifestRecord:
    id: str | None
    path: str
    absolute_path: str
    schema_valid: bool
    error: str | None


def _looks_like_unified_manifest(payload: dict[str, Any]) -> bool:
    required = {
        "id",
        "name",
        "origin",
        "symbolic_role",
        "domains",
        "entities",
        "correspondences",
        "geometry",
        "runtime_hooks",
        "cockpit_modes",
        "operator_approval_required",
    }
    return required.issubset(payload.keys())


def _scan_manifest(path: Path) -> ManifestRecord:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return ManifestRecord(
            id=None,
            path=str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            absolute_path=str(path.resolve()),
            schema_valid=False,
            error=f"json-parse-error: {exc}",
        )

    manifest_id = payload.get("id") if isinstance(payload, dict) else None
    if isinstance(payload, dict) and _looks_like_unified_manifest(payload):
        valid = True
        error = None
        try:
            from backend.symbolic_manifest_schema import validate_manifest

            validate_manifest(payload)
        except Exception as exc:
            valid = False
            error = str(exc)
    else:
        valid = False
        error = "not-unified-manifest-schema"

    return ManifestRecord(
        id=str(manifest_id) if manifest_id else None,
        path=str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        absolute_path=str(path.resolve()),
        schema_valid=valid,
        error=error,
    )


def build_registry() -> dict[str, Any]:
    manifests = sorted(PROJECT_ROOT.rglob("manifest.json"))
    records = [_scan_manifest(path) for path in manifests]
    records.sort(key=lambda item: item.path)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "project_root": str(PROJECT_ROOT.resolve()),
        "count": len(records),
        "entries": [asdict(record) for record in records],
    }


def main() -> int:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    registry = build_registry()
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {REGISTRY_PATH} with {registry['count']} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
