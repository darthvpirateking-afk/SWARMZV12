from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


@dataclass
class WhyEntry:
    mission_id: str
    decision: str
    rationale: str
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


WHY_LOG_PATH = Path("data/why_layer.jsonl")


def log_why(entry: WhyEntry) -> None:
    WHY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with WHY_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")


def get_why_history(mission_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    if not WHY_LOG_PATH.exists():
        return []

    rows: list[dict[str, Any]] = []
    for raw in WHY_LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        item = json.loads(raw)
        if mission_id and item.get("mission_id") != mission_id:
            continue
        rows.append(item)

    return rows[-max(1, limit):]


def suggest_next_step(current_phase: str, findings_count: int, protectiveness: int) -> str:
    if protectiveness >= 70 and findings_count > 0:
        return "Pause for operator review before active exploitation."
    if current_phase.upper() in {"SETUP", "RECON"} and findings_count == 0:
        return "Expand reconnaissance depth and validate target assumptions."
    if findings_count >= 5:
        return "Prioritize high-severity findings and generate remediation deltas."
    return "Continue mission pipeline with standard safeguards."
