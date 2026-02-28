from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from swarmz_runtime.avatar.summons.digital import (
    CodePhantom,
    DataWraith,
    FirewallSerpent,
    PacketSwarm,
)
from swarmz_runtime.avatar.summons.monarch import (
    ShadowArcher,
    ShadowColossus,
    ShadowKnight,
    ShadowMage,
)
from swarmz_runtime.avatar.summons.pantheon import (
    AetherGuardian,
    SolarWarden,
    StormHerald,
)
from swarmz_runtime.avatar.summons.relic import AegisSentinel, ChronoKnight, PrismGolem
from swarmz_runtime.avatar.summons.sigil import FractalDragon, GlyphSerpent, RuneWolf
from swarmz_runtime.storage.jsonl_utils import append_jsonl

_FORM_ORDER = [
    "AvatarOmega",
    "AvatarInfinity",
    "AvatarOmegaPlus",
    "AvatarSovereign",
    "AvatarMonarch",
]
_FORM_INDEX = {form: index for index, form in enumerate(_FORM_ORDER)}


class SummonWitnessLogger:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path("observatory") / "witness" / "avatar_summon_events.jsonl"

    def log_event(self, payload: dict[str, Any]) -> None:
        append_jsonl(self._path, payload)


class SummonEngine:
    def __init__(self, avatar: Any, witness: SummonWitnessLogger | None = None) -> None:
        self.avatar = avatar
        self.witness = witness or SummonWitnessLogger()
        self.registry = self._load_registry()
        self.active_summons: list[Any] = []

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _form_index(form: str) -> int:
        return _FORM_INDEX.get(form, 0)

    def _current_form(self) -> str:
        return str(getattr(self.avatar, "current_form", "AvatarOmega") or "AvatarOmega")

    def _load_registry(self) -> dict[str, Any]:
        summons = [
            SolarWarden(),
            StormHerald(),
            AetherGuardian(),
            GlyphSerpent(),
            RuneWolf(),
            FractalDragon(),
            AegisSentinel(),
            ChronoKnight(),
            PrismGolem(),
            ShadowKnight(),
            ShadowArcher(),
            ShadowMage(),
            ShadowColossus(),
            FirewallSerpent(),
            DataWraith(),
            CodePhantom(),
            PacketSwarm(),
        ]
        return {summon.id: summon for summon in summons}

    def _find_active(self, summon_id: str) -> Any | None:
        token = str(summon_id or "").strip()
        for summon in self.active_summons:
            if getattr(summon, "id", "") == token:
                return summon
        return None

    def _form_allows_summon(self, summon: Any) -> bool:
        required = str(getattr(summon, "form_required", "AvatarOmega") or "AvatarOmega")
        return self._form_index(self._current_form()) >= self._form_index(required)

    def _log_summon_event(self, event_type: str, summon_id: str) -> None:
        self.witness.log_event(
            {
                "type": "summon_event",
                "event": event_type,
                "summon": summon_id,
                "timestamp": self._now(),
                "form": self._current_form(),
            }
        )

    def spawn(self, summon_id: str) -> dict[str, Any]:
        summon = self.registry.get(str(summon_id or "").strip())
        if summon is None:
            return {"ok": False, "executed": False, "error": f"unknown summon '{summon_id}'"}
        if not self._form_allows_summon(summon):
            return {
                "ok": True,
                "executed": False,
                "summon": summon.id,
                "reason": "form_locked",
                "required_form": summon.form_required,
                "current_form": self._current_form(),
            }
        if self._find_active(summon.id) is not None:
            return {"ok": True, "executed": False, "summon": summon.id, "reason": "already_active"}
        self.active_summons.append(summon)
        summon.on_spawn()
        self._log_summon_event("spawn", summon.id)
        return {"ok": True, "executed": True, "summon": summon.id, "active_count": len(self.active_summons)}

    def dismiss(self, summon_id: str) -> dict[str, Any]:
        summon = self._find_active(summon_id)
        if summon is None:
            return {"ok": True, "executed": False, "summon": summon_id, "reason": "not_active"}
        summon.on_dismiss()
        self.active_summons.remove(summon)
        self._log_summon_event("dismiss", summon.id)
        return {"ok": True, "executed": True, "summon": summon.id, "active_count": len(self.active_summons)}

    def command_all(self, command: str) -> dict[str, Any]:
        token = str(command or "").strip().upper()
        if not self.active_summons:
            return {"ok": True, "executed": False, "reason": "no_active_summons"}
        issued: list[dict[str, Any]] = []
        for summon in self.active_summons:
            issued.append(summon.on_command(token))
            self._log_summon_event(token.lower(), summon.id)
        return {"ok": True, "executed": True, "command": token, "count": len(issued), "results": issued}

    def legion(self) -> dict[str, Any]:
        if self._current_form() != "AvatarMonarch":
            return {"ok": True, "executed": False, "reason": "monarch_required"}
        ids = ["ShadowKnight", "ShadowArcher", "ShadowMage", "ShadowColossus"]
        results = [self.spawn(summon_id) for summon_id in ids]
        return {
            "ok": True,
            "executed": any(r.get("executed") for r in results),
            "mode": "LEGION",
            "results": results,
        }

    def get_state(self) -> dict[str, Any]:
        return {
            "active_summons": [summon.to_dict() for summon in self.active_summons],
            "registry_count": len(self.registry),
            "current_form": self._current_form(),
        }
