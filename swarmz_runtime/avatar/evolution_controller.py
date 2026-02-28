from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nexusmon_operator_rank import get_current_rank
from swarmz_runtime.storage.jsonl_utils import append_jsonl

EVOLUTION_ORDER = [
    "AvatarOmega",        # Base
    "AvatarInfinity",     # Champion
    "AvatarOmegaPlus",    # Ultimate
    "AvatarSovereign",    # Final
]

RANK_REQUIREMENTS = {
    "AvatarOmega": "E",
    "AvatarInfinity": "C",
    "AvatarOmegaPlus": "A",
    "AvatarSovereign": "Sovereign",
}


class RankSystemAdapter:
    _RANK_LADDER = ["E", "D", "C", "B", "A", "S", "Sovereign"]

    def __init__(self) -> None:
        self.current_rank = self._load_rank()

    @classmethod
    def _normalize_rank(cls, rank: str) -> str:
        token = str(rank or "").strip()
        if not token:
            return "E"
        upper = token.upper()
        if upper == "N":
            return "Sovereign"
        if upper == "SOVEREIGN":
            return "Sovereign"
        if upper in {"E", "D", "C", "B", "A", "S"}:
            return upper
        return "E"

    def _load_rank(self) -> str:
        try:
            return self._normalize_rank(get_current_rank())
        except Exception:
            return "E"

    def refresh_rank(self) -> str:
        self.current_rank = self._load_rank()
        return self.current_rank

    def rank_at_least(self, required_rank: str) -> bool:
        current = self._normalize_rank(self.current_rank)
        required = self._normalize_rank(required_rank)
        return self._RANK_LADDER.index(current) >= self._RANK_LADDER.index(required)


class WitnessLogger:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path("observatory") / "witness" / "avatar_evolution.jsonl"

    def log_event(self, payload: dict[str, Any]) -> None:
        append_jsonl(self._path, payload)


class EvolutionController:
    def __init__(
        self,
        matrix: Any,
        rank_system: RankSystemAdapter,
        witness: WitnessLogger,
    ) -> None:
        self._matrix = matrix
        self.rank_system = rank_system
        self.witness = witness
        self.current_form = "AvatarOmega"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_next_form(self) -> str | None:
        if self.current_form not in EVOLUTION_ORDER:
            return None
        current_index = EVOLUTION_ORDER.index(self.current_form)
        if current_index >= len(EVOLUTION_ORDER) - 1:
            return None
        return EVOLUTION_ORDER[current_index + 1]

    def can_evolve_to(self, target_form: str | None) -> bool:
        if not target_form or target_form not in RANK_REQUIREMENTS:
            return False
        self.rank_system.refresh_rank()
        required_rank = RANK_REQUIREMENTS[target_form]
        return self.rank_system.rank_at_least(required_rank)

    def evolve(self) -> bool:
        if self.current_form not in EVOLUTION_ORDER:
            return False

        current_index = EVOLUTION_ORDER.index(self.current_form)
        if current_index == len(EVOLUTION_ORDER) - 1:
            return False  # already Sovereign

        next_form = EVOLUTION_ORDER[current_index + 1]
        if not self.can_evolve_to(next_form):
            return False  # rank too low

        self.current_form = next_form
        self._log_evolution(next_form)
        return True

    def unlock_sovereign(self) -> bool:
        self.rank_system.refresh_rank()
        if self.rank_system.rank_at_least("Sovereign"):
            self.current_form = "AvatarSovereign"
            self._log_evolution("AvatarSovereign")
            return True
        return False

    def can_enter_monarch_mode(self) -> bool:
        return self.current_form == "AvatarSovereign"

    def operator_trigger(self, command: str) -> bool:
        token = str(command or "").strip().upper()
        if token == "ASCEND":
            return self.evolve()
        if token == "SOVEREIGN":
            return self.unlock_sovereign()
        if token == "MONARCH":
            if self.can_enter_monarch_mode():
                self.current_form = "AvatarMonarch"
                self._log_evolution("AvatarMonarch")
                return True
        return False

    def _log_evolution(self, form: str) -> None:
        self.witness.log_event(
            {
                "type": "avatar_evolution",
                "new_form": form,
                "timestamp": self._now(),
            }
        )
