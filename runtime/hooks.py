from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from backend.life_runtime import (
    akashic_resolve,
    awakening_tick,
    breath_cycle,
    codex_query,
    dark_pool_oracle,
    death_rebirth,
    diary_tick,
    dream_seed_interpret,
    eclipse_alignment,
    heart_pulse,
    infinite_regress_guard,
    primordial_reseed,
    sovereign_mirror,
    tail_witness,
    voice_reflection,
    zero_point_bias,
)
from backend.symbolic_runtime import dispatch_hook as dispatch_symbolic_hook
from backend.symbolic_types import ALLOWED_SYMBOLIC_HOOKS, framed_symbolic_response
from runtime.events import EVENT_BUS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = PROJECT_ROOT / "core" / "manifests" / "registry.json"

HOOK_ALIAS_TO_CANONICAL: dict[str, str] = {
    "invoke": "on_invoke",
    "consult": "on_consult",
    "interpret": "on_symbolic_interpretation",
    "generate_geometry": "on_generate_geometry",
    "trigger_anomaly": "on_trigger_anomaly",
    "resolve_correspondence": "on_resolve_correspondence",
    "render_altar_mode": "on_render_altar_mode",
    "simulate_branch": "on_simulate_branch",
}
CANONICAL_HOOK_TO_EVENT: dict[str, str] = {
    value: key for key, value in HOOK_ALIAS_TO_CANONICAL.items()
}


@dataclass(frozen=True)
class RegisteredSystem:
    system_id: str
    manifest_path: str
    manifest: Dict[str, Any]
    lane: str
    family_or_group: str


class RuntimeHookDispatcher:
    """
    Canonical runtime hook dispatcher for symbolic and life systems.

    Behavior:
    - loads and caches core/manifests/registry.json
    - registers systems deterministically
    - enforces operator approval + ritual confirmation gates
    - routes supported hooks to symbolic or life handlers
    - emits normalized runtime events
    """

    def __init__(self, registry_path: Path | None = None) -> None:
        self._registry_path = registry_path or REGISTRY_PATH
        self._registry_mtime: float | None = None
        self._systems: dict[str, RegisteredSystem] = {}

    def _normalize_hook(self, hook: str) -> str:
        raw = str(hook).strip()
        if raw in ALLOWED_SYMBOLIC_HOOKS:
            return raw
        if raw in HOOK_ALIAS_TO_CANONICAL:
            return HOOK_ALIAS_TO_CANONICAL[raw]
        raise ValueError(f"unsupported hook: {hook}")

    def _load_registry_payload(self, force_reload: bool = False) -> Dict[str, Any]:
        if not self._registry_path.exists():
            return {"entries": []}

        mtime = self._registry_path.stat().st_mtime
        if not force_reload and self._registry_mtime == mtime and self._systems:
            return {"entries": []}

        data = json.loads(self._registry_path.read_text(encoding="utf-8-sig"))
        self._registry_mtime = mtime
        return data

    def _infer_lane(self, rel_path: str) -> tuple[str, str]:
        normalized = rel_path.replace("\\", "/")
        parts = normalized.split("/")
        if len(parts) >= 2 and parts[0] == "symbolic":
            return ("symbolic", parts[1])
        if len(parts) >= 2 and parts[0] == "life":
            return ("life", parts[1])
        return ("unknown", "unknown")

    def load_registry(self, force_reload: bool = False) -> dict[str, RegisteredSystem]:
        payload = self._load_registry_payload(force_reload=force_reload)
        entries = payload.get("entries", [])
        if not entries and self._systems:
            return self._systems

        systems: dict[str, RegisteredSystem] = {}
        for item in entries:
            if not isinstance(item, dict):
                continue
            system_id = str(item.get("id") or "").strip()
            rel_path = str(item.get("path") or "").strip()
            absolute_path = str(item.get("absolute_path") or "").strip()
            if not system_id or not rel_path:
                continue
            manifest_path = Path(absolute_path) if absolute_path else (PROJECT_ROOT / rel_path)
            if not manifest_path.exists():
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            except Exception:
                continue
            if not isinstance(manifest, dict) or "runtime_hooks" not in manifest:
                continue
            lane, family_or_group = self._infer_lane(rel_path)
            systems[system_id] = RegisteredSystem(
                system_id=system_id,
                manifest_path=rel_path.replace("\\", "/"),
                manifest=manifest,
                lane=lane,
                family_or_group=family_or_group,
            )

        self._systems = dict(sorted(systems.items(), key=lambda item: item[0]))
        return self._systems

    def registered_systems(self, hook: str | None = None) -> list[str]:
        self.load_registry()
        if hook is None:
            return sorted(self._systems.keys())
        canonical = self._normalize_hook(hook)
        out: list[str] = []
        for system_id, system in self._systems.items():
            hooks = system.manifest.get("runtime_hooks", {})
            if hooks.get(canonical) is True:
                out.append(system_id)
        return sorted(out)

    def _require_operator_gate(
        self,
        manifest: Dict[str, Any],
        payload: Dict[str, Any],
        operator_approved: bool,
    ) -> None:
        if manifest.get("operator_approval_required") is not True:
            return
        if not operator_approved:
            raise PermissionError("operator approval required")
        confirmation = payload.get("ritual_confirmation", {})
        if not isinstance(confirmation, dict) or confirmation.get("confirmed") is not True:
            raise ValueError("ritual confirmation required")

    def _dispatch_life(
        self,
        system_id: str,
        hook: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        if system_id.startswith("life.diary"):
            return diary_tick(payload)
        if system_id.startswith("life.awakening_loop"):
            return awakening_tick(payload)
        if system_id.startswith("life.breath"):
            return breath_cycle(payload)
        if system_id.startswith("life.heart"):
            return heart_pulse(payload)
        if system_id.startswith("life.memory_palace"):
            return framed_symbolic_response(
                {
                    "ok": True,
                    "summary": "Memory palace consult path is symbolic-only in unified dispatcher.",
                    "hook": hook,
                }
            )
        if system_id.startswith("life.guardians.infinite_regress"):
            return infinite_regress_guard(payload)
        if system_id.startswith("life.dream_seed"):
            return dream_seed_interpret(payload)
        if system_id.startswith("life.sovereign_mirror"):
            return sovereign_mirror(payload)
        if system_id.startswith("life.cosmic.dark_pool_oracle"):
            return dark_pool_oracle(payload)
        if system_id.startswith("life.cosmic.zero_point"):
            return zero_point_bias(payload)
        if system_id.startswith("life.cosmic.eclipse_alignment"):
            return eclipse_alignment(payload)
        if system_id.startswith("life.cosmic.noetic_resonance"):
            return noetic_resonance(payload)
        if system_id.startswith("life.species.panspermia_seed_bank"):
            action = str(payload.get("action", "export")).lower()
            if action == "import":
                return framed_symbolic_response(
                    {
                        "ok": True,
                        "summary": "Panspermia import is API-governed; dispatcher returns symbolic marker only.",
                    }
                )
            return framed_symbolic_response(
                {
                    "ok": True,
                    "summary": "Panspermia export is API-governed; dispatcher returns symbolic marker only.",
                }
            )
        if system_id.startswith("life.species.akashic_fork_resolver"):
            return akashic_resolve(payload)
        if system_id.startswith("life.species.primordial_soup"):
            return primordial_reseed(payload)
        if system_id.startswith("life.species.death_rebirth"):
            return death_rebirth(payload)
        if system_id.startswith("life.witness.codex_lock"):
            return codex_query(payload)
        if system_id.startswith("life.witness"):
            return framed_symbolic_response(
                {
                    "ok": True,
                    "summary": "Witness ledger tail returned.",
                    "witness_tail": tail_witness(20),
                }
            )
        if system_id.startswith("life.voice"):
            return voice_reflection(payload)
        return framed_symbolic_response(
            {
                "ok": True,
                "summary": f"Life dispatcher placeholder for {system_id}.",
            }
        )

    def dispatch(
        self,
        hook: str,
        system_id: str,
        payload: Dict[str, Any] | None = None,
        *,
        operator_approved: bool = False,
    ) -> Dict[str, Any]:
        payload = dict(payload or {})
        canonical_hook = self._normalize_hook(hook)

        systems = self.load_registry()
        system = systems.get(system_id)
        if system is None:
            raise KeyError(f"system not registered: {system_id}")

        enabled = bool(system.manifest.get("runtime_hooks", {}).get(canonical_hook, False))
        if not enabled:
            raise ValueError(f"hook disabled for system: {system_id}::{canonical_hook}")

        self._require_operator_gate(system.manifest, payload, operator_approved=operator_approved)

        if system.lane == "symbolic":
            response = dispatch_symbolic_hook(
                hook=canonical_hook,
                family=system.family_or_group,
                manifest=system.manifest,
                payload=payload,
            )
        elif system.lane == "life":
            response = self._dispatch_life(system_id, canonical_hook, payload)
        else:
            response = framed_symbolic_response(
                {
                    "ok": True,
                    "summary": f"No-op dispatcher for lane={system.lane}.",
                }
            )

        event_type = CANONICAL_HOOK_TO_EVENT[canonical_hook]
        EVENT_BUS.publish(
            event_type,
            {
                "system_id": system_id,
                "hook": canonical_hook,
                "lane": system.lane,
                "summary": response.get("result", {}).get("summary")
                if isinstance(response.get("result"), dict)
                else response.get("summary", ""),
            },
        )
        return {
            **response,
            "system_id": system_id,
            "manifest_id": system.manifest.get("id", system_id),
            "hook": canonical_hook,
            "lane": system.lane,
        }


DISPATCHER = RuntimeHookDispatcher()


def dispatch_runtime_hook(
    hook: str,
    system_id: str,
    payload: Dict[str, Any] | None = None,
    *,
    operator_approved: bool = False,
) -> Dict[str, Any]:
    """
    Convenience wrapper for runtime hook dispatch.
    """
    return DISPATCHER.dispatch(
        hook=hook,
        system_id=system_id,
        payload=payload,
        operator_approved=operator_approved,
    )
