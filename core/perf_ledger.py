import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class PerfLedger:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.file = self.data_dir / "perf_ledger.jsonl"
        if not self.file.exists():
            self.file.touch()

    def append(self, mission_id: str, runtime_ms: float, success_bool: bool, cost_estimate: float,
               agent_work_time: float = 0.0, agent_wait_time: float = 0.0) -> None:
        record: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mission_id": mission_id,
            "runtime_ms": runtime_ms,
            "success_bool": bool(success_bool),
            "cost_estimate": float(cost_estimate),
            "agent_work_time": float(agent_work_time),
            "agent_wait_time": float(agent_wait_time),
        }
        with open(self.file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")

    def load_recent(self, limit: int = 200) -> list:
        entries = []
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    entries.append(json.loads(line))
        except Exception:
            return []
        return entries[-max(1, limit):]
