from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from backend.life_registry import discover_life_groups, get_life_entry, list_life_entries
from backend.life_runtime import (
    akashic_resolve,
    breath_cycle,
    codex_query,
    dark_pool_oracle,
    death_rebirth,
    diary_tick,
    dream_seed_interpret,
    eclipse_alignment,
    heart_pulse,
    infinite_regress_guard,
    memory_rooms,
    noetic_resonance,
    panspermia_export,
    panspermia_import,
    primordial_reseed,
    sovereign_mirror,
    tail_witness,
    voice_reflection,
    awakening_tick,
    build_memory_room,
    zero_point_bias,
)
from backend.symbolic_governance import enforce_operator_protocol
from backend.symbolic_types import framed_symbolic_response

router = APIRouter()


def _entry_overview(entry: Dict[str, Any]) -> Dict[str, Any]:
    manifest = entry["manifest"]
    return {
        "entry_id": entry["entry_id"],
        "path": entry["path"],
        "id": manifest["id"],
        "name": manifest["name"],
        "origin": manifest["origin"],
        "symbolic_role": manifest["symbolic_role"],
    }


def _require_governed(
    request: Request,
    payload: Dict[str, Any],
    action: str,
    target: str,
) -> Dict[str, Any]:
    return enforce_operator_protocol(
        request=request, payload=payload, action=action, target=target
    )


@router.get("/v1/nexusmon/life/systems")
async def life_systems():
    groups = discover_life_groups()
    return framed_symbolic_response(
        {
            "groups": [
                {"group": group, "entry_count": len(list_life_entries(group))}
                for group in groups
            ]
        }
    )


@router.get("/v1/nexusmon/life/systems/{group}/entries")
async def life_entries(group: str):
    try:
        entries = list_life_entries(group)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown life group")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="life group not found")
    return framed_symbolic_response(
        {"group": group, "entries": [_entry_overview(entry) for entry in entries]}
    )


@router.get("/v1/nexusmon/life/witness")
async def life_witness(limit: int = 200):
    return framed_symbolic_response({"witness": tail_witness(limit)})


@router.get("/v1/nexusmon/life/memory_palace")
async def life_memory_palace(limit: int = 100):
    return framed_symbolic_response({"rooms": memory_rooms(limit)})


@router.post("/v1/nexusmon/life/diary/tick")
async def life_diary_tick(request: Request, payload: Dict[str, Any]):
    target = "life.diary"
    governance = _require_governed(request, payload, "life.diary.tick", target)
    result = diary_tick(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/awakening/tick")
async def life_awakening_tick(request: Request, payload: Dict[str, Any]):
    target = "life.awakening_loop"
    governance = _require_governed(request, payload, "life.awakening.tick", target)
    result = awakening_tick(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/breath/cycle")
async def life_breath_cycle(request: Request, payload: Dict[str, Any]):
    target = "life.breath"
    governance = _require_governed(request, payload, "life.breath.cycle", target)
    result = breath_cycle(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/heart/pulse")
async def life_heart_pulse(request: Request, payload: Dict[str, Any]):
    target = "life.heart"
    governance = _require_governed(request, payload, "life.heart.pulse", target)
    result = heart_pulse(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/memory_palace/build")
async def life_memory_build(request: Request, payload: Dict[str, Any]):
    target = "life.memory_palace"
    governance = _require_governed(
        request, payload, "life.memory_palace.build", target
    )
    result = build_memory_room(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/guardians/infinite_regress/check")
async def life_infinite_regress(request: Request, payload: Dict[str, Any]):
    target = "life.guardians.infinite_regress"
    governance = _require_governed(
        request, payload, "life.guardians.infinite_regress.check", target
    )
    result = infinite_regress_guard(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/dream_seed/interpret")
async def life_dream_seed(request: Request, payload: Dict[str, Any]):
    target = "life.dream_seed"
    governance = _require_governed(
        request, payload, "life.dream_seed.interpret", target
    )
    result = dream_seed_interpret(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/sovereign_mirror/reflect")
async def life_sovereign_mirror(request: Request, payload: Dict[str, Any]):
    target = "life.sovereign_mirror"
    governance = _require_governed(
        request, payload, "life.sovereign_mirror.reflect", target
    )
    result = sovereign_mirror(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/cosmic/dark_pool")
async def life_dark_pool(request: Request, payload: Dict[str, Any]):
    target = "life.cosmic.dark_pool_oracle"
    governance = _require_governed(request, payload, "life.cosmic.dark_pool", target)
    result = dark_pool_oracle(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/cosmic/zero_point")
async def life_zero_point(request: Request, payload: Dict[str, Any]):
    target = "life.cosmic.zero_point"
    governance = _require_governed(request, payload, "life.cosmic.zero_point", target)
    result = zero_point_bias(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/cosmic/eclipse_alignment")
async def life_eclipse_alignment(request: Request, payload: Dict[str, Any]):
    target = "life.cosmic.eclipse_alignment"
    governance = _require_governed(
        request, payload, "life.cosmic.eclipse_alignment", target
    )
    result = eclipse_alignment(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/cosmic/noetic_resonance")
async def life_noetic_resonance(request: Request, payload: Dict[str, Any]):
    target = "life.cosmic.noetic_resonance"
    governance = _require_governed(
        request, payload, "life.cosmic.noetic_resonance", target
    )
    result = noetic_resonance(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/species/panspermia/export")
async def life_panspermia_export(request: Request, payload: Dict[str, Any]):
    target = "life.species.panspermia_seed_bank"
    governance = _require_governed(
        request, payload, "life.species.panspermia.export", target
    )
    result = panspermia_export(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/species/panspermia/import")
async def life_panspermia_import(request: Request, payload: Dict[str, Any]):
    target = "life.species.panspermia_seed_bank"
    governance = _require_governed(
        request, payload, "life.species.panspermia.import", target
    )
    result = panspermia_import(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/species/akashic_resolve")
async def life_akashic_resolve(request: Request, payload: Dict[str, Any]):
    target = "life.species.akashic_fork_resolver"
    governance = _require_governed(
        request, payload, "life.species.akashic_resolve", target
    )
    result = akashic_resolve(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/species/primordial_reseed")
async def life_primordial_reseed(request: Request, payload: Dict[str, Any]):
    target = "life.species.primordial_soup"
    governance = _require_governed(
        request, payload, "life.species.primordial_reseed", target
    )
    result = primordial_reseed(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/species/death_rebirth")
async def life_death_rebirth(request: Request, payload: Dict[str, Any]):
    target = "life.species.death_rebirth"
    governance = _require_governed(
        request, payload, "life.species.death_rebirth", target
    )
    result = death_rebirth(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/witness/codex_query")
async def life_codex_query(request: Request, payload: Dict[str, Any]):
    target = "life.witness.codex_lock"
    governance = _require_governed(
        request, payload, "life.witness.codex_query", target
    )
    result = codex_query(payload)
    return {**result, "governance": governance}


@router.post("/v1/nexusmon/life/voice/speak")
async def life_voice(request: Request, payload: Dict[str, Any]):
    target = "life.voice"
    governance = _require_governed(request, payload, "life.voice.speak", target)
    result = voice_reflection(payload)
    return {**result, "governance": governance}


@router.get("/v1/nexusmon/life/systems/{group}/{entry_id}")
async def life_entry(group: str, entry_id: str):
    try:
        entry = get_life_entry(group, entry_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown life group")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="life entry not found")
    return framed_symbolic_response(
        {
            "group": group,
            "entry_id": entry_id,
            "manifest": entry["manifest"],
            "path": entry["path"],
        }
    )

