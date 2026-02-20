# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any


class DivergenceEngine:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.data_dir / "divergence_log.jsonl"
        self.state = {
            "divergence_score": 0.0,
            "branching_factor": 1.0,
            "planning_horizon": 1.0,
            "commitment_weight": 1.0,
        }

    def _count_prepared(self, hours: float = 24.0) -> int:
        base = self.data_dir.parent / "prepared_actions"
        count = 0
        cutoff = time.time() - hours * 3600
        for sub in ["messages", "schedules", "commands", "purchases"]:
            root = base / sub
            if not root.exists():
                continue
            for p in root.glob("**/*"):
                if p.is_file() and p.stat().st_mtime >= cutoff:
                    count += 1
        return count

    def _count_executed(self, hours: float = 24.0) -> int:
        perf_file = self.data_dir / "perf_ledger.jsonl"
        if not perf_file.exists():
            return 0
        cutoff = time.time() - hours * 3600
        count = 0
        with open(perf_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    ts = row.get("timestamp")
                    if ts:
                        try:
                            t = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                        except Exception:
                            continue
                        if t >= cutoff:
                            count += 1
                except Exception:
                    continue
        return count

    def update(self) -> Dict[str, Any]:
        planned = self._count_prepared()
        executed = self._count_executed()
        divergence = max(planned - executed, 0)
        prev = self.state.get("divergence_score", 0.0)
        self.state["divergence_score"] = divergence

        if divergence > prev:
            self.state["branching_factor"] = max(0.5, self.state.get("branching_factor", 1.0) * 0.8)
            self.state["planning_horizon"] = max(0.5, self.state.get("planning_horizon", 1.0) * 0.9)
            self.state["commitment_weight"] = min(3.0, self.state.get("commitment_weight", 1.0) * 1.2)
        else:
            self.state["branching_factor"] = min(2.0, self.state.get("branching_factor", 1.0) * 1.05)
            self.state["planning_horizon"] = min(2.0, self.state.get("planning_horizon", 1.0) * 1.05)
            self.state["commitment_weight"] = max(1.0, self.state.get("commitment_weight", 1.0) * 0.98)

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "planned": planned,
            "executed": executed,
            "divergence_score": divergence,
            "state": self.state,
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, separators=(",", ":")) + "\n")
        return self.state

    def get_adjustments(self) -> Dict[str, float]:
        return {
            "branching_factor": self.state.get("branching_factor", 1.0),
            "planning_horizon": self.state.get("planning_horizon", 1.0),
            "commitment_weight": self.state.get("commitment_weight", 1.0),
        }

