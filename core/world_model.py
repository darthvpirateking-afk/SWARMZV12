# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


class WorldModel:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.data_dir / "state_of_life.json"
        self.sources_dir = self.data_dir  # placeholder for local exports
        self.recompute_interval = 24 * 3600  # seconds

    def _gather_file_activity(self, roots: List[Path]) -> Dict[str, Any]:
        now = time.time()
        activity = []
        for root in roots:
            if not root.exists():
                continue
            for p in root.rglob("*"):
                if p.is_file():
                    mtime = p.stat().st_mtime
                    activity.append(now - mtime)
        if not activity:
            return {"recent_hours": 0, "files": 0}
        within_day = sum(1 for a in activity if a <= 86400)
        return {"recent_hours": within_day, "files": len(activity)}

    def _load_perf(self) -> Dict[str, Any]:
        perf_file = self.data_dir / "perf_ledger.jsonl"
        entries = []
        if perf_file.exists():
            with open(perf_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            entries.append(json.loads(line))
                        except Exception:
                            continue
        if not entries:
            return {
                "throughput": 0.0,
                "failure_rate": 0.0,
                "latency": 0.0,
                "resource_usage": 0.0,
            }
        successes = sum(1 for e in entries if e.get("success_bool"))
        failures = len(entries) - successes
        latency = sum(e.get("runtime_ms", 0.0) for e in entries) / max(len(entries), 1)
        resource = sum(e.get("cost_estimate", 0.0) for e in entries) / max(len(entries), 1)
        throughput = len(entries) / max((entries and 24.0) or 1.0, 1.0)
        return {
            "throughput": throughput,
            "failure_rate": failures / max(len(entries), 1),
            "latency": latency,
            "resource_usage": resource,
        }

    def _recent_outputs(self) -> List[str]:
        audit_file = self.data_dir / "audit.jsonl"
        outputs = []
        if audit_file.exists():
            with open(audit_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                        evt = row.get("event_type") or row.get("event")
                        mid = row.get("mission_id")
                        outputs.append(f"{evt}:{mid}")
                    except Exception:
                        continue
        return outputs[-10:]

    def _trend(self, series: List[float]) -> float:
        if len(series) < 4:
            return 0.0
        half = len(series) // 2
        prev = sum(series[:half]) / max(half, 1)
        recent = sum(series[half:]) / max(len(series) - half, 1)
        return recent - prev

    def _strategy_variance(self) -> float:
        evo_file = self.data_dir / "evolution_history.jsonl"
        by_strat = {}
        if evo_file.exists():
            with open(evo_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                        st = row.get("strategy_used", "baseline")
                        by_strat.setdefault(st, []).append(float(row.get("score", 0.0)))
                    except Exception:
                        continue
        scores = [sum(v) / max(len(v), 1) for v in by_strat.values()] or [0.0]
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / max(len(scores), 1)
        return min(1.0, variance)

    def _trend_vector(self) -> float:
        evo_file = self.data_dir / "evolution_history.jsonl"
        scores = []
        if evo_file.exists():
            with open(evo_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            scores.append(float(json.loads(line).get("score", 0.0)))
                        except Exception:
                            continue
        return self._trend(scores)

    def recompute(self) -> Dict[str, Any]:
        perf = self._load_perf()
        roots = [self.data_dir.parent / "addons", self.data_dir.parent / "src", self.data_dir.parent / "packs"]
        activity = self._gather_file_activity(roots)
        state = {
            "time_allocation": perf.get("throughput", 0.0),
            "active_projects": activity.get("files", 0),
            "financial_flow": perf.get("resource_usage", 0.0),
            "commitment_load": activity.get("recent_hours", 0),
            "recent_outputs": self._recent_outputs(),
            "idle_vs_execution_ratio": perf.get("throughput", 0.0) / max(perf.get("throughput", 1.0) + 1, 1),
            "strategy_variance": self._strategy_variance(),
            "trend_vector": self._trend_vector(),
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        return state

    def maybe_refresh(self) -> Dict[str, Any]:
        if not self.state_file.exists():
            return self.recompute()
        try:
            mtime = self.state_file.stat().st_mtime
            if (time.time() - mtime) > self.recompute_interval:
                return self.recompute()
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self.recompute()

