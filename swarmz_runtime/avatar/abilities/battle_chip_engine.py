from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from swarmz_runtime.avatar.abilities.chip import BattleChip
from swarmz_runtime.storage.jsonl_utils import append_jsonl

_FORM_ORDER = [
    "AvatarOmega",
    "AvatarInfinity",
    "AvatarOmegaPlus",
    "AvatarSovereign",
    "AvatarMonarch",
]
_FORM_INDEX = {form: index for index, form in enumerate(_FORM_ORDER)}

_EVOLUTION_BONUS = {
    "AvatarOmega": {"damage_pct": 0.0, "speed_pct": 0.0},
    "AvatarInfinity": {"damage_pct": 10.0, "speed_pct": 5.0},
    "AvatarOmegaPlus": {"damage_pct": 20.0, "speed_pct": 10.0},
    "AvatarSovereign": {"damage_pct": 35.0, "speed_pct": 20.0},
}

_MONARCH_VARIANTS = ["Abyssal Rend", "Cosmic Rift", "Shadow Collapse"]


class ChipWitnessLogger:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path("observatory") / "witness" / "avatar_chip_execution.jsonl"

    def log_event(self, payload: dict[str, Any]) -> None:
        append_jsonl(self._path, payload)


class BattleChipEngine:
    def __init__(self, avatar: Any, witness: ChipWitnessLogger | None = None) -> None:
        self.avatar = avatar
        self.witness = witness or ChipWitnessLogger()
        self.registry = self._load_registry()
        self._recent_executions: list[dict[str, Any]] = []

    def _registry_path(self) -> Path:
        return Path("swarmz_runtime/avatar/abilities/battle_chips.json")

    def _load_registry(self) -> dict[str, BattleChip]:
        path = self._registry_path()
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            payload = {"chips": []}
        chips: list[dict[str, Any]] = payload.get("chips", []) if isinstance(payload, dict) else []
        registry: dict[str, BattleChip] = {}
        for raw in chips:
            if not isinstance(raw, dict):
                continue
            chip = BattleChip.from_dict(raw)
            if chip.chip_id:
                registry[chip.chip_id] = chip
        return registry

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _current_form(self) -> str:
        return str(getattr(self.avatar, "current_form", "AvatarOmega") or "AvatarOmega")

    def _effective_evolution_form(self) -> str:
        form = self._current_form()
        if form == "AvatarMonarch":
            return "AvatarSovereign"
        return form if form in _EVOLUTION_BONUS else "AvatarOmega"

    def _form_allows_chip(self, chip: BattleChip) -> bool:
        current = self._current_form()
        required = chip.min_form if chip.min_form in _FORM_INDEX else "AvatarOmega"
        return _FORM_INDEX.get(current, 0) >= _FORM_INDEX[required]

    @staticmethod
    def _apply_percent(value: float, pct: float) -> float:
        return value * (1.0 + (pct / 100.0))

    def _apply_evolution_modifiers(self, chip: BattleChip) -> dict[str, float]:
        form = self._effective_evolution_form()
        profile = _EVOLUTION_BONUS.get(form, _EVOLUTION_BONUS["AvatarOmega"])
        stats = {
            "damage": self._apply_percent(chip.base_damage, profile.get("damage_pct", 0.0)),
            "speed": self._apply_percent(chip.base_speed, profile.get("speed_pct", 0.0)),
            "cost": chip.base_cost,
        }
        per_chip = chip.evolution_modifiers.get(form, {})
        stats["damage"] = self._apply_percent(stats["damage"], float(per_chip.get("damage_pct", 0.0)))
        stats["speed"] = self._apply_percent(stats["speed"], float(per_chip.get("speed_pct", 0.0)))
        stats["cost"] = self._apply_percent(stats["cost"], float(per_chip.get("cost_pct", 0.0)))
        return {k: round(v, 3) for k, v in stats.items()}

    def _apply_monarch_modifiers(self, stats: dict[str, float], chip: BattleChip) -> dict[str, float]:
        updated = dict(stats)
        updated["damage"] = self._apply_percent(updated["damage"], 50.0)
        updated["speed"] = self._apply_percent(updated["speed"], 25.0)
        per_chip = chip.monarch_modifiers or {}
        updated["damage"] = self._apply_percent(updated["damage"], float(per_chip.get("damage_pct", 0.0)))
        updated["speed"] = self._apply_percent(updated["speed"], float(per_chip.get("speed_pct", 0.0)))
        updated["cost"] = self._apply_percent(updated["cost"], float(per_chip.get("cost_pct", 0.0)))
        return {k: round(v, 3) for k, v in updated.items()}

    def _run_ability(self, chip: BattleChip, stats: dict[str, float]) -> dict[str, Any]:
        monarch_mode = self._current_form() == "AvatarMonarch"
        result = chip.execute(stats, self._current_form(), monarch_mode)
        if monarch_mode:
            result["special_variants"] = list(_MONARCH_VARIANTS)
        return result

    def _log_chip_use(self, chip_id: str, stats: dict[str, float]) -> None:
        payload = {
            "type": "chip_execution",
            "chip": chip_id,
            "stats": stats,
            "timestamp": self._now(),
        }
        self.witness.log_event(payload)
        self._recent_executions.append(payload)
        self._recent_executions = self._recent_executions[-50:]

    def execute_chip(self, chip_id: str) -> dict[str, Any]:
        chip = self.registry.get(str(chip_id or "").strip())
        if chip is None:
            return {"ok": False, "executed": False, "error": f"unknown chip '{chip_id}'"}
        if not self._form_allows_chip(chip):
            return {
                "ok": True,
                "executed": False,
                "chip": chip.chip_id,
                "reason": "form_locked",
                "required_form": chip.min_form,
                "current_form": self._current_form(),
            }
        stats = self._apply_evolution_modifiers(chip)
        if self._current_form() == "AvatarMonarch":
            stats = self._apply_monarch_modifiers(stats, chip)
        result = self._run_ability(chip, stats)
        self._log_chip_use(chip.chip_id, stats)
        return {"ok": True, "executed": True, **result}

    def _valid_chips(self) -> list[BattleChip]:
        return [chip for chip in self.registry.values() if self._form_allows_chip(chip)]

    def burst(self) -> dict[str, Any]:
        candidates = self._valid_chips()
        if not candidates:
            return {"ok": True, "executed": False, "reason": "no_available_chip"}
        selected = max(
            candidates,
            key=lambda c: (_FORM_INDEX.get(c.min_form, 0), c.base_damage, c.base_speed),
        )
        result = self.execute_chip(selected.chip_id)
        return {"ok": True, "executed": bool(result.get("executed")), "mode": "BURST", "chip_result": result}

    def chain(self) -> dict[str, Any]:
        candidates = sorted(
            self._valid_chips(),
            key=lambda c: (_FORM_INDEX.get(c.min_form, 0), c.base_damage, c.base_speed),
            reverse=True,
        )[:3]
        sequence: list[dict[str, Any]] = []
        for chip in candidates:
            sequence.append(self.execute_chip(chip.chip_id))
        return {
            "ok": True,
            "executed": len(sequence) > 0,
            "mode": "CHAIN",
            "count": len(sequence),
            "sequence": sequence,
        }

    def get_state(self) -> dict[str, Any]:
        by_category: dict[str, list[dict[str, Any]]] = {}
        available: list[dict[str, Any]] = []
        locked: list[dict[str, Any]] = []

        for chip in sorted(self.registry.values(), key=lambda c: (c.category, c.chip_id)):
            is_locked = not self._form_allows_chip(chip)
            entry = chip.to_public_dict(locked=is_locked)
            by_category.setdefault(chip.category, []).append(entry)
            if is_locked:
                locked.append(entry)
            else:
                available.append(entry)

        return {
            "available": available,
            "locked": locked,
            "categories": by_category,
            "recent_executions": list(self._recent_executions[-10:]),
            "monarch_mode": self._current_form() == "AvatarMonarch",
            "special_variants": list(_MONARCH_VARIANTS) if self._current_form() == "AvatarMonarch" else [],
        }
