# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import json
import gzip
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

USEFULNESS_DECAY = 0.995


class RelevanceEngine:
    """Tiered memory manager that scores usefulness and compresses noise."""

    def __init__(self, data_dir: str, evolution, counterfactual=None):
        self.data_dir = Path(data_dir)
        self.mem_dir = self.data_dir / "memory"
        self.hot_dir = self.mem_dir / "hot"
        self.warm_dir = self.mem_dir / "warm"
        self.cold_dir = self.mem_dir / "cold"
        self.archive_dir = self.mem_dir / "archive"
        for d in [self.mem_dir, self.hot_dir, self.warm_dir, self.cold_dir, self.archive_dir]:
            d.mkdir(parents=True, exist_ok=True)
        self.lessons_file = self.data_dir / "lessons.jsonl"
        self.cognitive_file = self.data_dir / "cognitive_load.txt"
        self.evolution = evolution
        self.counterfactual = counterfactual
        self._counter = 0

    # ---------- Public hooks ----------
    def after_outcome(
        self,
        mission_id: str,
        inputs_hash: str,
        strategy: str,
        score: float,
        success: bool,
        runtime_ms: float,
    ) -> None:
        usefulness = self._compute_usefulness(inputs_hash, strategy, score, success)
        tier = self._tier_for(usefulness)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "mission_id": mission_id,
            "inputs_hash": inputs_hash,
            "strategy": strategy,
            "score": score,
            "success": success,
            "runtime_ms": runtime_ms,
            "usefulness": usefulness,
            "tier": tier,
        }
        self._persist_record(record, tier)
        self._counter += 1
        if self._counter % 10 == 0:
            self._rebalance()
        if self._counter % 100 == 0:
            self._emit_cognitive_load()

    def get_attention_bundle(self, limit: int = 20) -> Dict[str, Any]:
        hot = self._tail_jsonl_dir(self.hot_dir, limit)
        lessons = self._tail_jsonl(self.lessons_file, 20)
        return {"hot": hot, "lessons": lessons}

    # ---------- Scoring & tiering ----------
    def _compute_usefulness(self, inputs_hash: str, strategy: str, score: float, success: bool) -> float:
        impact = max(score, 0.0)
        accuracy = 0.0
        regret = 0.0
        if self.counterfactual:
            cf_tail = self._tail_jsonl(self.data_dir / "counterfactual_log.jsonl", 50)
            matching = [e for e in cf_tail if e.get("inputs_hash") == inputs_hash and e.get("selected_strategy") == strategy]
            if matching:
                deltas = [abs(e.get("predicted_vs_actual_delta", 0.0)) for e in matching]
                accuracy = max(0.0, 1.0 - (sum(deltas) / max(len(deltas), 1)))
                regret = max(e.get("regret_score", 0.0) for e in matching)
        freq = self._recurrence(inputs_hash, strategy)
        age_penalty = USEFULNESS_DECAY ** max(len(self.evolution._history_cache), 1)
        base = impact + accuracy + freq - regret
        return round(max(0.0, base) * age_penalty, 4)

    def _recurrence(self, inputs_hash: str, strategy: str) -> float:
        hist = self.evolution.history_tail(limit=200)
        hits = sum(1 for h in hist if h.get("inputs_hash") == inputs_hash and h.get("strategy_used") == strategy)
        return min(1.0, hits / 20.0)

    def _tier_for(self, usefulness: float) -> str:
        if usefulness >= 1.2:
            return "hot"
        if usefulness >= 0.6:
            return "warm"
        if usefulness >= 0.2:
            return "cold"
        return "archive"

    # ---------- Persistence helpers ----------
    def _persist_record(self, record: Dict[str, Any], tier: str) -> None:
        if tier == "hot":
            self._append_jsonl(self.hot_dir / "hot.jsonl", record)
        elif tier == "warm":
            self._append_jsonl(self.warm_dir / "warm.jsonl", record)
        elif tier == "cold":
            # compress cold entries
            compressed_path = self.cold_dir / "cold.jsonl.gz"
            self._append_gzip_jsonl(compressed_path, record)
            self._emit_lesson(record, compressed=True)
        else:
            self._append_jsonl(self.archive_dir / "archive.jsonl", {"hash": record.get("inputs_hash"), "ts": record.get("timestamp")})

    def _append_jsonl(self, path: Path, row: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, separators=(',', ':')) + "\n")

    def _append_gzip_jsonl(self, path: Path, row: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, "at", encoding="utf-8") as f:
            f.write(json.dumps(row, separators=(',', ':')) + "\n")

    def _tail_jsonl(self, path: Path, limit: int) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        rows: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        continue
        return rows[-limit:]

    def _tail_jsonl_dir(self, dir_path: Path, limit: int) -> List[Dict[str, Any]]:
        latest_file = None
        for cand in [dir_path / "hot.jsonl", dir_path / "warm.jsonl"]:
            if cand.exists():
                latest_file = cand
                break
        if not latest_file:
            return []
        return self._tail_jsonl(latest_file, limit)

    # ---------- Rebalancing & lessons ----------
    def _rebalance(self) -> None:
        warm = self._tail_jsonl(self.warm_dir / "warm.jsonl", 200)
        cold = []
        cold_path = self.cold_dir / "cold.jsonl.gz"
        if cold_path.exists():
            try:
                with gzip.open(cold_path, "rt", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            cold.append(json.loads(line))
            except Exception:
                pass
        for rec in warm[-10:]:
            self._emit_lesson(rec, compressed=False)
        for rec in cold[-5:]:
            self._emit_lesson(rec, compressed=True)

    def _emit_lesson(self, rec: Dict[str, Any], compressed: bool) -> None:
        lesson = {
            "timestamp": rec.get("timestamp"),
            "situation_pattern": rec.get("inputs_hash"),
            "effective_action": rec.get("strategy"),
            "ineffective_action": None if rec.get("success") else rec.get("strategy"),
            "confidence_weight": max(0.1, rec.get("usefulness", 0.1)) * (0.5 if compressed else 1.0),
        }
        self._append_jsonl(self.lessons_file, lesson)

    # ---------- Cognitive load ----------
    def _emit_cognitive_load(self) -> None:
        hot_size = self._count_lines(self.hot_dir / "hot.jsonl")
        warm_size = self._count_lines(self.warm_dir / "warm.jsonl")
        cold_size = self._count_gzip_lines(self.cold_dir / "cold.jsonl.gz")
        latency = self._avg_runtime()
        signal, noise = self._signal_noise()
        lines = [
            f"Cognitive Load @ {datetime.now(timezone.utc).isoformat()}Z",
            f"active_memory_size: hot={hot_size} warm={warm_size} cold={cold_size}",
            f"decision_latency_ms: {latency}",
            f"signal_ratio: {signal}",
            f"noise_ratio: {noise}",
        ]
        if noise > signal:
            lines.append("compression_aggressiveness: increase")
        self.cognitive_file.write_text("\n".join(lines))

    def _count_lines(self, path: Path) -> int:
        if not path.exists():
            return 0
        return sum(1 for _ in open(path, "r", encoding="utf-8"))

    def _count_gzip_lines(self, path: Path) -> int:
        if not path.exists():
            return 0
        try:
            return sum(1 for _ in gzip.open(path, "rt", encoding="utf-8"))
        except Exception:
            return 0

    def _avg_runtime(self) -> float:
        perf = self._tail_jsonl(self.data_dir / "perf_ledger.jsonl", 100)
        if not perf:
            return 0.0
        return round(sum(e.get("runtime_ms", 0.0) for e in perf) / max(len(perf), 1), 2)

    def _signal_noise(self) -> Tuple[float, float]:
        hist = self.evolution.history_tail(limit=200)
        if not hist:
            return (0.0, 0.0)
        signals = sum(1 for h in hist if h.get("score", 0.0) >= 0.5)
        noise = len(hist) - signals
        total = max(len(hist), 1)
        return (round(signals / total, 3), round(noise / total, 3))

