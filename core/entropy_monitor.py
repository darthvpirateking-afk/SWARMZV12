# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class EntropyMonitor:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.data_dir / "entropy_log.jsonl"
        self.state = {
            "mode": "EXPAND",
            "error_rate": 0.0,
            "task_switch_frequency": 0.0,
            "abandoned_actions": 0,
            "completion_latency": 0.0,
            "retry_counts": 0,
        }

    def _load_perf(self):
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
        return entries

    def _compute_metrics(self) -> Dict[str, Any]:
        entries = self._load_perf()
        if not entries:
            return self.state
        errors = sum(1 for e in entries if not e.get("success_bool"))
        error_rate = errors / max(len(entries), 1)
        durations = [e.get("runtime_ms", 0.0) for e in entries]
        completion_latency = sum(durations) / max(len(durations), 1)
        retry_counts = sum(1 for e in entries if e.get("success_bool") is False)
        # task switch frequency approximated by number of missions per hour
        timestamps = []
        for e in entries:
            ts = e.get("timestamp")
            if ts:
                try:
                    timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
                except Exception:
                    continue
        timestamps.sort()
        switch_freq = 0.0
        if len(timestamps) > 1:
            deltas = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            avg_delta = sum(deltas) / len(deltas)
            if avg_delta > 0:
                switch_freq = min(10.0, 3600.0 / avg_delta)
        abandoned = max(0, errors - retry_counts)
        return {
            "mode": self.state.get("mode", "EXPAND"),
            "error_rate": error_rate,
            "task_switch_frequency": switch_freq,
            "abandoned_actions": abandoned,
            "completion_latency": completion_latency,
            "retry_counts": retry_counts,
        }

    def update(self) -> Dict[str, Any]:
        metrics = self._compute_metrics()
        if metrics.get("error_rate", 0.0) > 0.25 or metrics.get("task_switch_frequency", 0.0) > 6.0:
            metrics["mode"] = "CONSOLIDATE"
        else:
            metrics["mode"] = "EXPAND"
        self.state = metrics
        event = {"timestamp": datetime.utcnow().isoformat() + "Z", **metrics}
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, separators=(",", ":")) + "\n")
        return self.state

    def get_adjustments(self) -> Dict[str, Any]:
        if self.state.get("mode") == "CONSOLIDATE":
            return {
                "exploration_bias_delta": -0.05,
                "priority_finish": True,
            }
        return {
            "exploration_bias_delta": 0.02,
            "priority_finish": False,
        }

