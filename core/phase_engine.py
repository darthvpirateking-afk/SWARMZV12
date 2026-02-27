# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List


class PhaseEngine:
    """Detect temporal phase transitions and suggest preemptive actions."""

    def __init__(
        self,
        data_dir: str,
        world_model=None,
        divergence=None,
        entropy=None,
        trajectory=None,
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "phase_history.jsonl"
        self.patterns_file = self.data_dir / "phase_patterns.json"
        self.interventions_file = self.data_dir / "phase_interventions.jsonl"
        self.report_file = self.data_dir / "phase_report.txt"
        self.preemptive_dir = self.data_dir.parent / "prepared_actions" / "preemptive"
        self.preemptive_dir.mkdir(parents=True, exist_ok=True)
        self.world_model = world_model
        self.divergence = divergence
        self.entropy = entropy
        self.trajectory = trajectory
        self._sequence_window = 6

    # ---------- Hooks ----------
    def after_outcome(
        self,
        success: bool,
        score: float,
        runtime_ms: float,
        strategy: str,
    ) -> None:
        state_hash = self._state_of_life_hash()
        ent_level = 0.0
        div_score = 0.0
        if self.entropy:
            ent_level = self.entropy.state.get("mode_value", 0.0)
        if self.divergence:
            div_score = self.divergence.state.get("divergence_score", 0.0)
        success_rate = self._recent_success_rate()
        work_intensity = self._recent_work_intensity()
        cluster_id = self._cluster_id(success_rate, div_score, ent_level)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "state_of_life_hash": state_hash,
            "entropy_level": ent_level,
            "divergence_score": div_score,
            "success_rate_recent": success_rate,
            "work_intensity": work_intensity,
            "context_cluster_id": cluster_id,
        }
        self._append_jsonl(self.history_file, entry)
        patterns = self._detect_patterns()
        self._maybe_preempt(patterns, entry)
        self._maybe_amplify(entry)
        self._learn_confidence(patterns, success)
        self._maybe_report(entry, patterns)

    # ---------- Internals ----------
    def _state_of_life_hash(self) -> str:
        state = {}
        if self.world_model and getattr(self.world_model, "state_file", None):
            try:
                if self.world_model.state_file.exists():
                    state = json.loads(self.world_model.state_file.read_text())
            except Exception:
                state = {}
        raw = json.dumps(state, sort_keys=True, default=str)
        return str(abs(hash(raw)))

    def _recent_success_rate(self) -> float:
        perf_file = self.data_dir / "perf_ledger.jsonl"
        if not perf_file.exists():
            return 0.0
        rows = []
        with open(perf_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        continue
        rows = rows[-50:]
        if not rows:
            return 0.0
        successes = sum(1 for r in rows if r.get("success_bool"))
        return round(successes / max(len(rows), 1), 3)

    def _recent_work_intensity(self) -> float:
        perf_file = self.data_dir / "perf_ledger.jsonl"
        if not perf_file.exists():
            return 0.0
        rows = []
        with open(perf_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        continue
        rows = rows[-50:]
        return round(sum(r.get("runtime_ms", 0.0) for r in rows) / max(len(rows), 1), 3)

    def _cluster_id(
        self, success_rate: float, divergence_score: float, entropy_level: float
    ) -> str:
        if success_rate < 0.3 and divergence_score > 0.2:
            return "risk_drift"
        if success_rate < 0.3:
            return "at_risk"
        if entropy_level > 0.6:
            return "expanding"
        if entropy_level < 0.2:
            return "stabilizing"
        return "steady"

    def _detect_patterns(self) -> Dict[str, Any]:
        seqs = self._load_sequences()
        patterns: Dict[str, Any] = {}
        for label, windows in seqs.items():
            patterns[label] = {
                "count": len(windows),
                "confidence": round(min(1.0, len(windows) / 10.0), 3),
                "recent": windows[-1] if windows else [],
            }
        self.patterns_file.write_text(json.dumps(patterns, indent=2))
        return patterns

    def _load_sequences(self) -> Dict[str, List[List[str]]]:
        entries = self._tail_jsonl(self.history_file, 120)
        labels: Dict[str, List[List[str]]] = {
            "failure_clusters": [],
            "abandoned": [],
            "slowdowns": [],
            "recoveries": [],
            "bursts": [],
        }
        outcomes = {
            "failure_clusters": lambda e: e.get("success_rate_recent", 0.0) < 0.25,
            "abandoned": lambda e: e.get("divergence_score", 0.0) > 0.5,
            "slowdowns": lambda e: e.get("work_intensity", 0.0) > 8000,
            "recoveries": lambda e: (
                e.get("success_rate_recent", 0.0) > 0.6
                and e.get("entropy_level", 0.0) < 0.4
            ),
            "bursts": lambda e: (
                e.get("success_rate_recent", 0.0) > 0.7
                and e.get("entropy_level", 0.0) > 0.4
            ),
        }
        for i in range(len(entries)):
            window = entries[max(0, i - self._sequence_window + 1) : i + 1]
            labels_for_window = []
            for name, fn in outcomes.items():
                if any(fn(e) for e in window):
                    labels_for_window.append(name)
            cluster_ids = [e.get("context_cluster_id") for e in window]
            for name in labels_for_window:
                labels[name].append(cluster_ids)
        return labels

    def _maybe_preempt(self, patterns: Dict[str, Any], current: Dict[str, Any]) -> None:
        for label, info in patterns.items():
            conf = info.get("confidence", 0.0)
            if conf < 0.2:
                continue
            if label in {"failure_clusters", "abandoned", "slowdowns"}:
                plan = {
                    "timestamp": current.get("timestamp"),
                    "detected_pattern": label,
                    "probable_outcome": label,
                    "preventive_action": self._preventive_action(label),
                    "confidence": conf,
                }
                fname = (
                    self.preemptive_dir
                    / f"plan_{int(datetime.now(timezone.utc).timestamp())}.json"
                )
                fname.write_text(json.dumps(plan, indent=2))

    def _preventive_action(self, label: str) -> str:
        mapping = {
            "failure_clusters": "narrow scope and add validation gate",
            "abandoned": "recommit to top project and freeze branching",
            "slowdowns": "split tasks into smaller batches and timebox",
        }
        return mapping.get(label, "stabilize")

    def _maybe_amplify(self, current: Dict[str, Any]) -> None:
        # Positive phase amplification record
        if (
            current.get("context_cluster_id") in {"steady", "stabilizing"}
            and current.get("success_rate_recent", 0.0) > 0.6
        ):
            intervention = {
                "timestamp": current.get("timestamp"),
                "action": "reduce friction and batch high-value tasks",
                "context_cluster_id": current.get("context_cluster_id"),
                "entropy": current.get("entropy_level"),
            }
            self._append_jsonl(self.interventions_file, intervention)

    def _learn_confidence(self, patterns: Dict[str, Any], success: bool) -> None:
        data = patterns or {}
        for name, info in data.items():
            conf = info.get("confidence", 0.0)
            if success:
                conf = min(1.0, conf + 0.05)
            else:
                conf = max(0.0, conf - 0.05)
            info["confidence"] = round(conf, 3)
            data[name] = info
        if data:
            self.patterns_file.write_text(json.dumps(data, indent=2))

    def _maybe_report(self, current: Dict[str, Any], patterns: Dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        if self.report_file.exists():
            try:
                mtime = datetime.fromtimestamp(self.report_file.stat().st_mtime)
                if (now - mtime) < timedelta(hours=24):
                    return
            except Exception:
                pass
        probable_next = self._probable_next(patterns)
        stance = self._stance(probable_next)
        lines = [
            f"Phase Report @ {current.get('timestamp')}",
            f"current_phase: {current.get('context_cluster_id')}",
            f"probable_next_phase: {probable_next}",
            f"recommended_stance: {stance}",
        ]
        self.report_file.write_text("\n".join(lines))

    def _probable_next(self, patterns: Dict[str, Any]) -> str:
        if patterns.get("failure_clusters", {}).get("confidence", 0) > 0.4:
            return "failure_clusters"
        if patterns.get("abandoned", {}).get("confidence", 0) > 0.4:
            return "abandoned"
        if patterns.get("bursts", {}).get("confidence", 0) > 0.4:
            return "bursts"
        return "steady"

    def _stance(self, next_phase: str) -> str:
        if next_phase in {"failure_clusters", "abandoned", "slowdowns"}:
            return "stabilize"
        if next_phase == "bursts":
            return "expand"
        return "recover" if next_phase == "recoveries" else "steady"

    # ---------- IO helpers ----------
    def _append_jsonl(self, file_path: Path, row: Dict[str, Any]) -> None:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")

    def _tail_jsonl(self, file_path: Path, limit: int) -> List[Dict[str, Any]]:
        if not file_path.exists():
            return []
        rows: List[Dict[str, Any]] = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        continue
        return rows[-limit:]
