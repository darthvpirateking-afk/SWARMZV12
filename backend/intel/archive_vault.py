from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

from backend.intel.secret_scanner import scan_file_dict


@dataclass
class ArchiveEntry:
    mission_id: str
    artifact_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


ARCHIVE_PATH = Path("data/intel_archive.jsonl")


def archive_intel(entry: ArchiveEntry) -> None:
    ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ARCHIVE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")


def list_archived_intel(
    mission_id: str | None = None, limit: int = 100
) -> list[dict[str, Any]]:
    if not ARCHIVE_PATH.exists():
        return []

    rows: list[dict[str, Any]] = []
    for raw in ARCHIVE_PATH.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        item = json.loads(raw)
        if mission_id and item.get("mission_id") != mission_id:
            continue
        rows.append(item)
    return rows[-max(1, limit) :]


def get_archive_config(patience: int, protectiveness: int) -> dict[str, Any]:
    return {
        "enabled": patience >= 30,
        "archive_raw_payloads": protectiveness < 80,
        "retention_days": 7 if protectiveness >= 70 else 30,
        "scan_for_secrets_on_archive": True,
    }


def archive_and_scan(
    mission_id: str,
    artifact_type: str,
    payload: dict[str, Any],
    curiosity: int,
    aggression: int,
) -> dict[str, Any]:
    archive_intel(
        ArchiveEntry(
            mission_id=mission_id, artifact_type=artifact_type, payload=payload
        )
    )
    serialized = json.dumps(payload, ensure_ascii=False)
    findings = scan_file_dict(
        path=f"archive://{mission_id}/{artifact_type}",
        content=serialized,
        curiosity=curiosity,
        aggression=aggression,
    )
    return {"archived": True, "secret_findings": findings}
