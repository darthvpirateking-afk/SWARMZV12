# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from core.operator_anchor import compute_record_hash


class CounterfactualEngine:
    def __init__(self, data_dir: str, evolution, trajectory=None, world_model=None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_file = self.data_dir / "decision_snapshots.jsonl"
        self.cf_log_file = self.data_dir / "counterfactual_log.jsonl"
        self.report_file = self.data_dir / "decision_quality_report.txt"
        self.evolution = evolution
        self.trajectory = trajectory
        self.world_model = world_model
        if not self.snapshots_file.exists():
            self.snapshots_file.touch()
        if not self.cf_log_file.exists():
            self.cf_log_file.touch()

    # ---------- Helpers ----------
    def _append_jsonl(self, file_path: Path, entry: Dict[str, Any]) -> None:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")

    def _hash_payload(self, payload: Dict[str, Any]) -> str:
        try:
            raw = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=True)
            return compute_record_hash({"payload": raw}, previous_hash="")
        except Exception:
            return ""

    def state_of_life_hash(self) -> str:
        state = {}
        if self.world_model and getattr(self.world_model, "state_file", None):
            try:
                if self.world_model.state_file.exists():
                    state = json.loads(self.world_model.state_file.read_text())
            except Exception:
                state = {}
        return self._hash_payload(state)

    def get_trend_vector(self) -> float:
        try:
            if self.world_model and getattr(self.world_model, "state_file", None) and self.world_model.state_file.exists():
                state = json.loads(self.world_model.state_file.read_text())
                return float(state.get("trend_vector", 0.0))
        except Exception:
            return 0.0
        return 0.0

    # ---------- Decision snapshot ----------
    def record_snapshot(
        self,
        inputs_hash: str,
        selected_strategy: str,
        candidate_strategies: List[str],
        expected_outcome_projection: Dict[str, Any],
        state_of_life_hash: str,
        personality_vector: Dict[str, Any],
    ) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inputs_hash": inputs_hash,
            "state_of_life_hash": state_of_life_hash,
            "personality_vector": personality_vector,
            "selected_strategy": selected_strategy,
            "candidate_strategies": candidate_strategies,
            "expected_outcome_projection": expected_outcome_projection,
        }
        self._append_jsonl(self.snapshots_file, entry)

    # ---------- Counterfactual evaluation ----------
    def evaluate(
        self,
        mission_id: str,
        inputs_hash: str,
        selected_strategy: str,
        candidate_strategies: List[str],
        actual_score: float,
        success: bool,
        trend_vector: float,
    ) -> None:
        predictions: Dict[str, float] = {}
        for strat in candidate_strategies:
            base = self.evolution.strategy_average(inputs_hash, strat)
            adjusted = base + trend_vector * 0.05
            predictions[strat] = round(adjusted, 4)
        selected_pred = predictions.get(selected_strategy, 0.0)
        predicted_vs_actual_delta = actual_score - selected_pred
        best_alt = selected_pred
        for strat, pred in predictions.items():
            if strat == selected_strategy:
                continue
            if pred > best_alt:
                best_alt = pred
        regret_score = max(0.0, best_alt - actual_score)
        surprise_score = abs(predicted_vs_actual_delta)

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mission_id": mission_id,
            "inputs_hash": inputs_hash,
            "selected_strategy": selected_strategy,
            "predictions": predictions,
            "actual_score": actual_score,
            "predicted_vs_actual_delta": predicted_vs_actual_delta,
            "regret_score": regret_score,
            "surprise_score": surprise_score,
            "trend_vector": trend_vector,
            "success": success,
        }
        self._append_jsonl(self.cf_log_file, log_entry)

        self.evolution.update_reliability(selected_strategy, selected_pred, actual_score, surprise_score)
        if regret_score > 0.0:
            self.evolution.bump_exploration_bias(min(0.05, regret_score * 0.1))
        if surprise_score < 0.1:
            self.evolution.bump_confidence(0.02)
        else:
            self.evolution.update_uncertainty(surprise_score)

        self._maybe_emit_report()

    # ---------- Reporting ----------
    def _load_cf_log(self) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        try:
            with open(self.cf_log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            entries.append(json.loads(line))
                        except Exception:
                            continue
        except FileNotFoundError:
            return []
        return entries

    def _prediction_accuracy_trend(self, deltas: List[float]) -> float:
        if len(deltas) < 4:
            return 0.0
        mid = len(deltas) // 2
        first = sum(abs(d) for d in deltas[:mid]) / max(mid, 1)
        second = sum(abs(d) for d in deltas[mid:]) / max(len(deltas) - mid, 1)
        return first - second  # positive means improving (lower error)

    def _most_misleading(self, entries: List[Dict[str, Any]]) -> List[str]:
        sorted_entries = sorted(entries[-50:], key=lambda e: e.get("surprise_score", 0.0), reverse=True)
        return [f"{e.get('mission_id')}:{e.get('selected_strategy')} surprise={round(e.get('surprise_score', 0.0),3)}" for e in sorted_entries[:3]]

    def _most_reliable(self) -> List[str]:
        reliab = getattr(self.evolution, "_reliability", {})
        ranked = []
        for strat, rec in reliab.items():
            cnt = max(rec.get("count", 1), 1)
            acc = rec.get("accurate", 0) / cnt
            over = rec.get("overconfident", 0) / cnt
            ranked.append((acc - over * 0.2, strat, acc, over))
        ranked.sort(reverse=True)
        lines = []
        for item in ranked[:3]:
            lines.append(f"{item[1]} accuracy={round(item[2],3)} overconfidence={round(item[3],3)}")
        return lines

    def _maybe_emit_report(self) -> None:
        entries = self._load_cf_log()
        if not entries or (len(entries) % 50 != 0):
            return
        regrets = [e.get("regret_score", 0.0) for e in entries]
        deltas = [e.get("predicted_vs_actual_delta", 0.0) for e in entries]
        avg_regret = sum(regrets) / max(len(regrets), 1)
        accuracy_trend = self._prediction_accuracy_trend(deltas)
        misleading = self._most_misleading(entries)
        reliable = self._most_reliable()

        lines = []
        lines.append(f"Decision Quality Report @ {datetime.now(timezone.utc).isoformat()}")
        lines.append(f"Missions evaluated: {len(entries)}")
        lines.append(f"Average regret: {round(avg_regret, 4)}")
        lines.append(f"Prediction accuracy trend (positive improves): {round(accuracy_trend, 4)}")
        lines.append("Most misleading patterns:")
        for row in misleading or ["None"]:
            lines.append(f"  {row}")
        lines.append("Most reliable contexts:")
        for row in reliable or ["None"]:
            lines.append(f"  {row}")

        with open(self.report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

