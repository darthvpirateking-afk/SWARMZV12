# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from zoneinfo import ZoneInfo

from core.operator_anchor import compute_record_hash, sign_record, verify_signature


class EvolutionMemory:
    """Persistent, append-only evolution history with companion continuity."""

    def __init__(self, data_dir: str = "data", anchor: Optional[Dict[str, Any]] = None, read_only: bool = False):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "evolution_history.jsonl"
        self.state_file = self.data_dir / "companion_state.json"
        self.personality_file = self.data_dir / "personality_vector.json"
        self.reliability_file = self.data_dir / "strategy_reliability.json"
        self.uncertainty_file = self.data_dir / "uncertainty_profile.json"
        self.epochs_dir = self.data_dir / "epochs"
        self.epochs_dir.mkdir(exist_ok=True)
        if not self.history_file.exists():
            self.history_file.touch()

        self.anchor = anchor or {}
        self.allow_write = not read_only
        self.chain_valid = True

        self._state = self._load_companion_state()
        self._personality = self._load_personality()
        self._reliability = self._load_reliability()
        self._uncertainty = self._load_uncertainty()
        self._commitments: Dict[str, float] = {}
        self._history_cache: List[Dict[str, Any]] = []
        self._load_chain()

    @staticmethod
    def compute_inputs_hash(goal: str, category: str, constraints: Dict[str, Any]) -> str:
        payload = {
            "goal": goal or "",
            "category": category or "",
            "constraints": constraints or {},
        }
        raw = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=True)
        return compute_record_hash({"payload": raw}, previous_hash="")

    @staticmethod
    def compute_score(success: bool, total_runtime_ms: float, cost_estimate: float) -> float:
        base = 1.0 if success else 0.0
        speed_factor = 1.0 / (1.0 + max(total_runtime_ms, 0.0) / 10000.0)
        cost_factor = 1.0 / (1.0 + max(cost_estimate, 0.0))
        return round(base * speed_factor * cost_factor, 4)

    # ---------- Chain management ----------
    def _load_chain(self) -> None:
        prev_hash = "GENESIS"
        records: List[Dict[str, Any]] = []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if row.get("previous_hash") != prev_hash:
                        self.chain_valid = False
                        break
                    record_hash = compute_record_hash({k: v for k, v in row.items() if k not in {"record_hash", "signature"}}, prev_hash)
                    if record_hash != row.get("record_hash"):
                        self.chain_valid = False
                        break
                    priv = self.anchor.get("operator_private_key", "")
                    if priv and not verify_signature(priv, record_hash, row.get("signature", "")):
                        self.chain_valid = False
                        break
                    records.append(row)
                    prev_hash = row.get("record_hash")
        except Exception:
            self.chain_valid = False
        if self.chain_valid:
            self._history_cache = records
        else:
            self.allow_write = False
            self._history_cache = []

    def _next_previous_hash(self) -> str:
        if not self._history_cache:
            return "GENESIS"
        return self._history_cache[-1].get("record_hash", "GENESIS")

    def append_record(
        self,
        timestamp: datetime,
        mission_type: str,
        inputs_hash: str,
        strategy_used: str,
        total_runtime_ms: float,
        success_bool: bool,
        cost_estimate: float,
        score: float,
    ) -> None:
        if not (self.allow_write and self.chain_valid):
            return

        base_record = {
            "timestamp": timestamp.isoformat(),
            "mission_type": mission_type,
            "inputs_hash": inputs_hash,
            "strategy_used": strategy_used,
            "total_runtime_ms": total_runtime_ms,
            "success_bool": success_bool,
            "cost_estimate": cost_estimate,
            "score": score,
            "operator_public_key": self.anchor.get("operator_public_key"),
        }
        previous_hash = self._next_previous_hash()
        record_hash = compute_record_hash(base_record, previous_hash)
        signature = sign_record(self.anchor.get("operator_private_key", ""), record_hash)
        full_record = {**base_record, "previous_hash": previous_hash, "record_hash": record_hash, "signature": signature}

        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(full_record, separators=(",", ":")) + "\n")

        self._history_cache.append(full_record)
        self._maybe_emit_epoch()

    def load_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.chain_valid:
            return []
        if limit <= 0:
            return []
        return self._history_cache[-limit:]

    def history_tail(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.load_history(limit=limit)

    # ---------- Strategy aggregation ----------
    def _aggregate_by_strategy(self, inputs_hash: str) -> Dict[str, Dict[str, float]]:
        stats: Dict[str, Dict[str, float]] = {}
        for row in self._history_cache:
            if row.get("inputs_hash") != inputs_hash:
                continue
            strat = row.get("strategy_used", "baseline")
            score = float(row.get("score", 0.0))
            success = bool(row.get("success_bool"))
            rec = stats.setdefault(strat, {"total": 0.0, "count": 0, "success": 0})
            rec["total"] += score
            rec["count"] += 1
            rec["success"] += 1 if success else 0
        for rec in stats.values():
            cnt = max(rec.get("count", 1), 1)
            rec["avg_score"] = rec.get("total", 0.0) / cnt
            rec["success_rate"] = rec.get("success", 0) / cnt
        return stats

    def strategy_average(self, inputs_hash: str, strategy: str) -> float:
        stats = self._aggregate_by_strategy(inputs_hash)
        if strategy in stats:
            return float(stats[strategy].get("avg_score", 0.0))
        return 0.0

    def _weight_with_personality(self, base_score: float) -> float:
        r = self._personality.get("risk_tolerance", 0.5)
        s = self._personality.get("speed_preference", 0.5)
        e = self._personality.get("exploration_bias", 0.5)
        w = base_score * (0.8 + r * 0.2) * (0.8 + s * 0.2)
        return max(w, 0.001) * (1.0 + e * 0.1)

    def set_commitments(self, weights: Dict[str, float]) -> None:
        self._commitments = weights or {}

    def bump_exploration_bias(self, delta: float) -> None:
        self._personality["exploration_bias"] = self._clamp(self._personality.get("exploration_bias", 0.5) + delta)
        self._save_personality()

    def select_strategy(self, inputs_hash: str, default_strategy: str = "baseline", bias_fn=None) -> str:
        stats = self._aggregate_by_strategy(inputs_hash)
        if not stats:
            preferred = self._state.get("preferred_strategies", {})
            if preferred:
                best = sorted(
                    preferred.items(),
                    key=lambda kv: (kv[1].get("avg_score", 0.0), kv[1].get("count", 0)),
                    reverse=True,
                )[0][0]
                return best
            return default_strategy

        strategies = list(stats.keys())
        weights = []
        for strat in strategies:
            sc = stats[strat].get("avg_score", 0.0)
            adj = bias_fn(strat, sc) if bias_fn else None
            weighted = adj if adj is not None else self._weight_with_personality(sc)
            if self._commitments:
                weighted *= self._commitments.get(strat, 1.0)
            weighted *= self._reliability_penalty(strat)
            weighted *= 1.0 - min(0.3, self._uncertainty.get("uncertainty_weight", 0.0) * 0.2)
            weights.append(weighted)
        if sum(weights) <= 0:
            return max(stats.items(), key=lambda kv: kv[1].get("avg_score", 0.0))[0]
        try:
            chosen = random.choices(strategies, weights=weights, k=1)[0]
            return chosen
        except Exception:
            return strategies[0]

    # ---------- Outcomes & personality ----------
    def _update_personality(self, success: bool, runtime_ms: float, score: float) -> None:
        p = self._personality
        delta = 0.02 if success else -0.02
        p["risk_tolerance"] = self._clamp(p.get("risk_tolerance", 0.5) + delta)
        speed_adj = 0.01 if runtime_ms < 5000 else -0.01
        p["speed_preference"] = self._clamp(p.get("speed_preference", 0.5) + speed_adj)
        explore_adj = 0.01 if score < 0.5 else -0.005
        p["exploration_bias"] = self._clamp(p.get("exploration_bias", 0.5) + explore_adj)
        retry_adj = -0.01 if success else 0.015
        p["retry_patience"] = self._clamp(p.get("retry_patience", 0.5) + retry_adj)
        self._personality = p
        self._save_personality()

    def record_outcome(
        self,
        strategy: str,
        score: float,
        success: bool,
        mission_id: str,
        inputs_hash: str,
        previous_avg: float,
        runtime_ms: float = 0.0,
    ) -> None:
        state = self._state
        prefs: Dict[str, Dict[str, Any]] = state.setdefault("preferred_strategies", {})
        entry = prefs.get(strategy, {"avg_score": 0.0, "count": 0, "reinforced": False, "priority": 1.0})
        count = entry.get("count", 0)
        new_avg = ((entry.get("avg_score", 0.0) * count) + score) / max(count + 1, 1)
        improvement = score > previous_avg

        entry.update({
            "avg_score": round(new_avg, 4),
            "count": count + 1,
            "reinforced": bool(improvement),
            "last_score": score,
        })
        if not improvement:
            entry["priority"] = max(entry.get("priority", 1.0) * 0.9, 0.1)
        else:
            entry["priority"] = entry.get("priority", 1.0) + 0.1
        prefs[strategy] = entry

        if not success:
            failures = state.setdefault("recent_failures", [])
            failures.append(mission_id)
            state["recent_failures"] = failures[-10:]

        state["last_active_mission"] = mission_id
        state["confidence_level"] = self._compute_confidence(prefs)
        self._state = state
        self._save_companion_state()
        self._update_personality(success, runtime_ms=runtime_ms, score=score)

    def get_companion_state(self) -> Dict[str, Any]:
        return {
            "last_active_mission": self._state.get("last_active_mission"),
            "preferred_strategies": self._state.get("preferred_strategies", {}),
            "recent_failures": self._state.get("recent_failures", []),
            "confidence_level": self._state.get("confidence_level", 0.5),
            "personality": self._personality,
        }

    def get_scoreboard(self) -> Dict[str, Any]:
        return {
            "records": len(self._history_cache),
            "chain_valid": self.chain_valid,
            "personality": self._personality,
            "companion_state": self.get_companion_state(),
            "commitments": self._commitments,
            "reliability": self._reliability,
            "uncertainty": self._uncertainty,
        }

    def candidate_strategies(self, inputs_hash: str) -> List[str]:
        stats = self._aggregate_by_strategy(inputs_hash)
        if stats:
            return list(stats.keys())
        preferred = self._state.get("preferred_strategies", {})
        if preferred:
            return list(preferred.keys())
        return ["baseline"]

    def update_reliability(self, strategy: str, predicted: float, actual: float, surprise_score: float) -> None:
        rec = self._reliability.get(strategy, {"count": 0, "accurate": 0, "overconfident": 0, "squared_error": 0.0})
        rec["count"] += 1
        error = predicted - actual
        rec["squared_error"] += error * error
        if abs(error) <= 0.1:
            rec["accurate"] += 1
        if error > 0.2:
            rec["overconfident"] += 1
        rec["last_predicted"] = predicted
        rec["last_actual"] = actual
        rec["last_surprise"] = surprise_score
        count = max(rec.get("count", 1), 1)
        rec["variance"] = rec.get("squared_error", 0.0) / count
        rec["prediction_accuracy"] = rec.get("accurate", 0) / count
        rec["overconfidence_rate"] = rec.get("overconfident", 0) / count
        self._reliability[strategy] = rec
        self._save_reliability()

    def _reliability_penalty(self, strategy: str) -> float:
        rec = self._reliability.get(strategy)
        if not rec:
            return 1.0
        over_rate = rec.get("overconfidence_rate")
        if over_rate is None:
            count = max(rec.get("count", 1), 1)
            over_rate = rec.get("overconfident", 0) / count
        penalty = 1.0 - min(0.5, over_rate * 0.5)
        return max(penalty, 0.1)

    def update_uncertainty(self, surprise_score: float) -> None:
        weight = self._uncertainty.get("uncertainty_weight", 0.5)
        weight = self._clamp(weight + surprise_score * 0.1)
        self._uncertainty["uncertainty_weight"] = weight
        self._uncertainty["last_surprise"] = surprise_score
        self._save_uncertainty()

    def bump_confidence(self, delta: float) -> None:
        cur = self._state.get("confidence_level", 0.5)
        self._state["confidence_level"] = self._clamp(cur + delta)
        self._save_companion_state()

    def get_personality(self) -> Dict[str, Any]:
        return dict(self._personality)

    # ---------- Personality / Companion state ----------
    def _clamp(self, value: float, low: float = 0.0, high: float = 1.0) -> float:
        return max(low, min(high, round(value, 4)))

    def _compute_confidence(self, prefs: Dict[str, Dict[str, Any]]) -> float:
        if not prefs:
            return 0.5
        scores = [v.get("avg_score", 0.0) for v in prefs.values()]
        if not scores:
            return 0.5
        avg = sum(scores) / len(scores)
        return self._clamp(0.5 + (avg - 0.5))

    def _load_companion_state(self) -> Dict[str, Any]:
        default_state = {
            "last_active_mission": None,
            "preferred_strategies": {},
            "recent_failures": [],
            "confidence_level": 0.5,
        }
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    default_state.update(loaded)
            except Exception:
                return default_state
        return default_state

    def _save_companion_state(self) -> None:
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2)

    def _load_personality(self) -> Dict[str, Any]:
        defaults = {
            "risk_tolerance": 0.5,
            "speed_preference": 0.5,
            "exploration_bias": 0.5,
            "retry_patience": 0.5,
        }
        if self.personality_file.exists():
            try:
                with open(self.personality_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    defaults.update({k: self._clamp(float(v)) for k, v in data.items() if k in defaults})
            except Exception:
                pass
        return defaults

    def _save_personality(self) -> None:
        with open(self.personality_file, "w", encoding="utf-8") as f:
            json.dump(self._personality, f, indent=2)

    def _load_reliability(self) -> Dict[str, Any]:
        if self.reliability_file.exists():
            try:
                with open(self.reliability_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_reliability(self) -> None:
        with open(self.reliability_file, "w", encoding="utf-8") as f:
            json.dump(self._reliability, f, indent=2)

    def _load_uncertainty(self) -> Dict[str, Any]:
        defaults = {"uncertainty_weight": 0.5, "last_surprise": 0.0}
        if self.uncertainty_file.exists():
            try:
                with open(self.uncertainty_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    defaults.update({k: self._clamp(float(v)) if isinstance(v, (int, float)) else v for k, v in data.items()})
            except Exception:
                return defaults
        return defaults

    def _save_uncertainty(self) -> None:
        with open(self.uncertainty_file, "w", encoding="utf-8") as f:
            json.dump(self._uncertainty, f, indent=2)

    # ---------- Epoch compression ----------
    def _maybe_emit_epoch(self) -> None:
        count = len(self._history_cache)
        if count == 0 or count % 100 != 0:
            return
        epoch_idx = count // 100
        epoch_file = self.epochs_dir / f"epoch_{epoch_idx}.json"
        if epoch_file.exists():
            return

        summary: Dict[str, Any] = {
            "epoch": epoch_idx,
            "records": count,
            "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
            "personality": self._personality,
            "strategies": {},
        }
        strat_totals: Dict[str, Dict[str, Any]] = {}
        for row in self._history_cache[-100:]:
            strat = row.get("strategy_used", "baseline")
            st = strat_totals.setdefault(strat, {"scores": [], "success": 0, "count": 0})
            st["scores"].append(float(row.get("score", 0.0)))
            st["success"] += 1 if row.get("success_bool") else 0
            st["count"] += 1
        for strat, val in strat_totals.items():
            cnt = max(val["count"], 1)
            summary["strategies"][strat] = {
                "avg_score": sum(val["scores"]) / cnt,
                "success_rate": val["success"] / cnt,
                "count": cnt,
            }
        with open(epoch_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

