from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


@dataclass
class ExperimentRun:
    mission_id: str
    variant: str
    metrics: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ExperimentTracker:
    def __init__(self, path: str = "data/experiments.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log_run(self, run: ExperimentRun) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(run), ensure_ascii=False) + "\n")

    def list_runs(self, mission_id: str | None = None) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for raw in self.path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            item = json.loads(raw)
            if mission_id and item.get("mission_id") != mission_id:
                continue
            rows.append(item)
        return rows
