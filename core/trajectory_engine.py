# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List
import time  # For profiling

DEFAULT_FUTURE_STATE = {
    "north_star_description": "Reliable, adaptive operator companion",
    "time_horizon_days": 90,
    "priority_axes": {
        "stability": 0.7,
        "growth": 0.6,
        "optionality": 0.5,
        "recovery_capacity": 0.7,
    },
    "drift_tolerance": 0.1,
    "last_updated": None,
}


class TrajectoryEngine:
    def __init__(
        self,
        data_dir: str,
        evolution,
        perf_ledger,
        world_model=None,
        divergence=None,
        entropy=None,
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.future_state_file = self.data_dir / "future_state.json"
        self.current_state_file = self.data_dir / "current_state.json"
        self.drift_log = self.data_dir / "drift_log.jsonl"
        self.commitments_file = self.data_dir / "commitments.json"
        self.reflection_file = self.data_dir / "reflection.txt"
        self.daily_brief_file = self.data_dir / "daily_brief.txt"

        self.evolution = evolution
        self.perf_ledger = perf_ledger
        self.world_model = world_model
        self.divergence = divergence
        self.entropy = entropy
        self.future_state = self._load_future_state()
        self.commitments = self._load_commitments()
        self._drift_counter = 0
        self._drift_threshold = 5
        self.bias_weight = 0.25
        self.evolution.set_commitments(self.commitments)

    # ---------- Persistence helpers ----------
    def _load_future_state(self) -> Dict[str, Any]:
        if self.future_state_file.exists():
            try:
                with open(self.future_state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    DEFAULT_FUTURE_STATE.update(
                        {k: v for k, v in data.items() if k in DEFAULT_FUTURE_STATE}
                    )
            except Exception:
                pass
        if DEFAULT_FUTURE_STATE["last_updated"] is None:
            DEFAULT_FUTURE_STATE["last_updated"] = (
                datetime.now(timezone.utc).isoformat() + "Z"
            )
        with open(self.future_state_file, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_FUTURE_STATE, f, indent=2)
        return DEFAULT_FUTURE_STATE

    def _load_commitments(self) -> Dict[str, float]:
        if self.commitments_file.exists():
            try:
                with open(self.commitments_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {k: float(v) for k, v in data.items()}
            except Exception:
                return {}
        return {}

    def _save_commitments(self) -> None:
        with open(self.commitments_file, "w", encoding="utf-8") as f:
            json.dump(self.commitments, f, indent=2)
        self.evolution.set_commitments(self.commitments)

    def _write_current_state(self, state: Dict[str, Any]) -> None:
        with open(self.current_state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def _append_drift(self, event: Dict[str, Any]) -> None:
        with open(self.drift_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, separators=(",", ":")) + "\n")

    # ---------- Metric computation ----------
    def _compute_axis_estimates(
        self, current_state: Dict[str, Any]
    ) -> Dict[str, float]:
        failure_rate = current_state.get("failure_rate", 0.0)
        throughput = current_state.get("throughput", 0.0)
        latency = current_state.get("latency", 0.0)
        variance = current_state.get("strategy_variance", 0.0)

        stability = max(0.0, min(1.0, 1.0 - failure_rate))
        growth = max(0.0, min(1.0, throughput / 10.0))
        optionality = max(0.0, min(1.0, variance))
        recovery_capacity = 1.0 / (1.0 + latency / 10000.0)
        return {
            "stability": stability,
            "growth": growth,
            "optionality": optionality,
            "recovery_capacity": recovery_capacity,
        }

    def _distance(self, axes: Dict[str, float]) -> float:
        weights = self.future_state.get("priority_axes", {})
        dist = 0.0
        for axis, target in weights.items():
            dist += abs(axes.get(axis, 0.0) - float(target)) * max(
                0.1, float(weights.get(axis, 0.1))
            )
        return dist

    def _recent_trend(self, scores: List[float]) -> float:
        if len(scores) < 4:
            return 0.0
        mid = len(scores) // 2
        prev_avg = sum(scores[:mid]) / max(mid, 1)
        recent_avg = sum(scores[mid:]) / max(len(scores) - mid, 1)
        return recent_avg - prev_avg

    def _compute_current_state(self) -> Dict[str, Any]:
        hist = self.evolution.history_tail(limit=200)
        perf_entries = self.perf_ledger.load_recent(limit=200)
        if perf_entries:
            start_ts = perf_entries[0].get("timestamp")
            end_ts = perf_entries[-1].get("timestamp")
            try:
                start_dt = (
                    datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
                    if start_ts
                    else datetime.now(timezone.utc)
                )
                end_dt = (
                    datetime.fromisoformat(end_ts.replace("Z", "+00:00"))
                    if end_ts
                    else datetime.now(timezone.utc)
                )
                elapsed_hours = max((end_dt - start_dt).total_seconds() / 3600.0, 0.001)
            except Exception:
                elapsed_hours = 1.0
        else:
            elapsed_hours = 1.0

        successes = sum(1 for e in perf_entries if e.get("success_bool"))
        failures = len(perf_entries) - successes
        failure_rate = failures / max(len(perf_entries), 1)
        throughput = len(perf_entries) / elapsed_hours
        latency = sum(e.get("runtime_ms", 0.0) for e in perf_entries) / max(
            len(perf_entries), 1
        )
        resource_usage = sum(e.get("cost_estimate", 0.0) for e in perf_entries) / max(
            len(perf_entries), 1
        )

        scores = [h.get("score", 0.0) for h in hist]
        trend = self._recent_trend(scores)

        # Strategy variance based on score variance per strategy
        by_strat = {}
        for h in hist:
            st = h.get("strategy_used", "baseline")
            by_strat.setdefault(st, []).append(h.get("score", 0.0))
        strat_scores = [sum(v) / max(len(v), 1) for v in by_strat.values()] or [0.0]
        mean = sum(strat_scores) / len(strat_scores)
        variance = sum((s - mean) ** 2 for s in strat_scores) / max(
            len(strat_scores), 1
        )
        variance = min(1.0, variance)

        return {
            "throughput": throughput,
            "failure_rate": failure_rate,
            "latency": latency,
            "resource_usage": resource_usage,
            "strategy_variance": variance,
            "recent_trend_vector": trend,
            "last_updated": datetime.now(timezone.utc).isoformat() + "Z",
        }

    # ---------- Public hooks ----------
    def trajectory_score(self, action_projection: Dict[str, Any]) -> float:
        start_time = time.perf_counter()  # Start profiling
        if not self.current_state_file.exists():
            current_state = self._compute_current_state()
        else:
            try:
                current_state = json.loads(self.current_state_file.read_text())
            except Exception:
                current_state = self._compute_current_state()
        axes_before = self._compute_axis_estimates(current_state)
        distance_before = self._distance(axes_before)

        # apply projection deltas
        projected_state = dict(current_state)
        for key, delta in action_projection.items():
            if key in projected_state and isinstance(delta, (int, float)):
                projected_state[key] = projected_state.get(key, 0.0) + delta
        axes_after = self._compute_axis_estimates(projected_state)
        distance_after = self._distance(axes_after)

        trajectory_delta = distance_before - distance_after
        performance_score = float(action_projection.get("performance_score", 0.0))
        result = performance_score + trajectory_delta * self.bias_weight
        end_time = time.perf_counter()  # End profiling
        print(f"Trajectory score computation took {end_time - start_time:.6f} seconds.")
        return result

    def strategy_bias(self, strategy: str, avg_score: float) -> float:
        projection = {"performance_score": avg_score}
        # incorporate divergence and entropy pressure
        adj = self.divergence.get_adjustments() if self.divergence else {}
        ent = self.entropy.get_adjustments() if self.entropy else {}
        bias = self.trajectory_score(projection)
        bias *= adj.get("branching_factor", 1.0)
        bias *= adj.get("commitment_weight", 1.0)
        bias += ent.get("exploration_bias_delta", 0.0)
        return bias

    def after_outcome(
        self, success: bool, score: float, runtime_ms: float, strategy: str
    ) -> None:
        current_state = self._compute_current_state()
        self._write_current_state(current_state)

        if self.world_model:
            self.world_model.maybe_refresh()
        if self.divergence:
            self.divergence.update()
        if self.entropy:
            self.entropy.update()

        # Drift detection
        trend = current_state.get("recent_trend_vector", 0.0)
        if trend < -abs(self.future_state.get("drift_tolerance", 0.1)):
            self._drift_counter += 1
        else:
            self._drift_counter = max(0, self._drift_counter - 1)
        if self._drift_counter >= self._drift_threshold:
            event = {
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "trend": trend,
                "message": "trajectory drifting away from north star",
            }
            self._append_drift(event)
            self.evolution.bump_exploration_bias(0.05)
            self._drift_counter = 0

        # Commitment pressure
        if strategy not in self.commitments:
            self.commitments[strategy] = 1.0
        if score > 0:
            self.commitments[strategy] = min(self.commitments[strategy] + 0.1, 5.0)
        else:
            self.commitments[strategy] = max(self.commitments[strategy] * 0.9, 0.1)
        self._save_commitments()

        # Daily reflection
        self._maybe_reflect()
        self._maybe_daily_brief()

    def _maybe_reflect(self) -> None:
        now = datetime.now(timezone.utc)
        if self.reflection_file.exists():
            mtime = datetime.fromtimestamp(
                os.path.getmtime(self.reflection_file), tz=timezone.utc
            )
            if (now - mtime) < timedelta(hours=24):
                return

        hist = self.evolution.history_tail(limit=50)
        improvements = [h for h in hist if h.get("score", 0) > 0.5]
        regressions = [h for h in hist if h.get("score", 0) <= 0.5]
        lines = []
        lines.append(f"Reflection @ {now.isoformat()}Z")
        lines.append("Improved trajectory strategies:")
        for h in improvements[-5:]:
            lines.append(f"  {h.get('strategy_used')} score={h.get('score')}")
        lines.append("Degraded trajectory strategies:")
        for h in regressions[-5:]:
            lines.append(f"  {h.get('strategy_used')} score={h.get('score')}")
        lines.append("Reinforce:")
        for h in improvements[-3:]:
            lines.append(f"  {h.get('strategy_used')}")
        with open(self.reflection_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _maybe_daily_brief(self) -> None:
        now = datetime.now(timezone.utc)
        if self.daily_brief_file.exists():
            mtime = datetime.fromtimestamp(
                os.path.getmtime(self.daily_brief_file), tz=timezone.utc
            )
            if (now - mtime) < timedelta(hours=24):
                return

        state_of_life = {}
        if self.world_model and self.world_model.state_file.exists():
            try:
                state_of_life = json.loads(self.world_model.state_file.read_text())
            except Exception:
                state_of_life = {}
        divergence_state = self.divergence.state if self.divergence else {}
        entropy_state = self.entropy.state if self.entropy else {}

        value_entries = []
        value_file = self.data_dir / "value_ledger.jsonl"
        if value_file.exists():
            with open(value_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            value_entries.append(json.loads(line))
                        except Exception:
                            continue
        high_value = sorted(
            value_entries[-20:],
            key=lambda x: x.get("future_option_value", 0.0),
            reverse=True,
        )[:5]
        wasted = [v for v in value_entries[-20:] if v.get("direct_money_change", 0) < 0]

        lines = []
        lines.append(f"Daily Brief @ {now.isoformat()}Z")
        lines.append("State changes:")
        lines.append(f"  State of life trend: {state_of_life.get('trend_vector')}")
        lines.append(f"  Divergence score: {divergence_state.get('divergence_score')}")
        lines.append(f"  Entropy mode: {entropy_state.get('mode')}")
        lines.append("High value actions:")
        for v in high_value:
            lines.append(f"  {v.get('project','?')} +{v.get('future_option_value',0)}")
        lines.append("Wasted effort patterns:")
        for v in wasted[-3:]:
            lines.append(
                f"  {v.get('project','?')} delta {v.get('direct_money_change',0)}"
            )
        lines.append("Recommended focus shift:")
        if entropy_state.get("mode") == "CONSOLIDATE":
            lines.append("  Consolidate and finish pending commitments.")
        elif divergence_state.get("divergence_score", 0) > 0:
            lines.append("  Reduce branching and execute prepared actions.")
        else:
            lines.append("  Explore adjacent options with controlled branching.")

        with open(self.daily_brief_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
