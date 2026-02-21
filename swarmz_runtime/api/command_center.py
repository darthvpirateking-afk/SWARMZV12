# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Command center endpoints — autonomy, shadow mode, evolution, marketplace."""

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from swarmz_runtime.api.models import (
    AutonomyDialRequest,
    EvolutionPromoteRequest,
    LoopTickRequest,
    MarketplacePublishRequest,
    OrganismEvolveRequest,
    ShadowModeRequest,
)

router = APIRouter(prefix="/v1/command-center", tags=["command-center"])

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _ROOT_DIR / "data"


# ---------------------------------------------------------------------------
# JSONL helpers (local, avoids circular imports)
# ---------------------------------------------------------------------------
def _tail_jsonl(path: Path, limit: int) -> list:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        tail = lines[-limit:]
        return [json.loads(line) for line in tail if line.strip()]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# State persistence helpers
# ---------------------------------------------------------------------------
def _command_center_state_path() -> Path:
    return _DATA_DIR / "command_center_state.json"


def _default_command_center_state() -> Dict[str, Any]:
    return {
        "autonomy": {"level": 35, "mode": "assisted"},
        "shadow_mode": {"enabled": False, "lane": "mirror", "last_activation": None},
        "partner": {
            "name": "AegisShade",
            "tier": "Rookie",
            "tier_index": 1,
            "traits": {"logic": 0.60, "empathy": 0.64, "precision": 0.62},
            "autonomy_ceiling": 25,
        },
        "shadow": {
            "name": "NightLegion",
            "tier": "Dormant",
            "tier_index": 0,
            "risk_precision": 0.35,
            "tactical_authority": "operator_approval",
        },
        "autonomy_loop": {
            "sensors": [
                "sales",
                "refunds",
                "support_tickets",
                "fulfillment_delays",
                "spend_rate",
                "conversion_rate",
                "blueprint_performance",
            ],
            "last_tick": None,
            "tick_count": 0,
        },
        "evolution_tree": {
            "tiers": ["seed", "scout", "operator", "architect", "sovereign"],
            "partners": [
                {"partner_id": "alpha", "tier": "scout", "xp": 18},
                {"partner_id": "beta", "tier": "operator", "xp": 42},
            ],
            "history": [],
        },
        "marketplace": {
            "missions": [
                {
                    "listing_id": "mk-001",
                    "mission_type": "recon",
                    "title": "Map runtime blind spots",
                    "reward_points": 150,
                    "tags": ["runtime", "analysis"],
                    "status": "open",
                }
            ]
        },
    }


def _read_command_center_state() -> Dict[str, Any]:
    path = _command_center_state_path()
    if not path.exists():
        state = _default_command_center_state()
        _write_command_center_state(state)
        return state
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    state = _default_command_center_state()
    _write_command_center_state(state)
    return state


def _write_command_center_state(state: Dict[str, Any]) -> None:
    path = _command_center_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _autonomy_mode_from_level(level: int) -> str:
    if level < 25:
        return "manual"
    if level < 55:
        return "assisted"
    if level < 80:
        return "autonomous"
    return "sovereign"


def _partner_tiers() -> List[str]:
    return ["Egg", "Rookie", "Champion", "Ultimate", "Mega", "Ultra"]


def _shadow_tiers() -> List[str]:
    return ["Dormant", "Shade", "Wraith", "Reaper", "General", "Monarch"]


def _cockpit_feed(state: Dict[str, Any]) -> Dict[str, Any]:
    from jsonl_utils import read_jsonl

    missions_file = _DATA_DIR / "missions.jsonl"
    runs_file = _DATA_DIR / "runs.jsonl"
    missions_result = read_jsonl(missions_file)
    runs_result = read_jsonl(runs_file)

    if isinstance(missions_result, tuple):
        missions = missions_result[0]
    elif isinstance(missions_result, list):
        missions = missions_result
    else:
        missions = []

    if isinstance(runs_result, tuple):
        runs = runs_result[0]
    elif isinstance(runs_result, list):
        runs = runs_result
    else:
        runs = []

    queued = sum(
        1
        for m in missions
        if str(m.get("status", "")).upper() in {"PENDING", "QUEUED", "CREATED"}
    )
    completed = sum(
        1
        for m in missions
        if str(m.get("status", "")).upper() in {"SUCCESS", "COMPLETED", "DONE"}
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "queue_depth": queued,
        "completed_count": completed,
        "recent_runs": runs[-5:],
        "autonomy": state.get("autonomy", {}),
        "shadow_mode": state.get("shadow_mode", {}),
        "organism": {
            "partner_tier": state.get("partner", {}).get("tier", "Rookie"),
            "shadow_tier": state.get("shadow", {}).get("tier", "Dormant"),
        },
        "partner_summary": state.get("evolution_tree", {}).get("partners", []),
        "ledger": {
            "missions_total": len(missions),
            "runs_total": len(runs),
            "audit_events_last_20": len(_tail_jsonl(_DATA_DIR / "audit.jsonl", 20)),
        },
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/state")
def command_center_state():
    state = _read_command_center_state()
    return {
        "ok": True,
        "cockpit": _cockpit_feed(state),
        "shadow_mode": state.get("shadow_mode", {}),
        "partner": state.get("partner", {}),
        "shadow": state.get("shadow", {}),
        "autonomy_loop": state.get("autonomy_loop", {}),
        "evolution_tree": state.get("evolution_tree", {}),
        "autonomy": state.get("autonomy", {}),
        "marketplace": state.get("marketplace", {}),
        "lore": {
            "world_bible": "docs/WORLD_BIBLE.md",
            "status": "loaded",
        },
        "deploy": {
            "entrypoint": "SWARMZ_ONE_BUTTON_DEPLOY.ps1",
            "status": "ready",
        },
    }


@router.get("/organism/state")
def organism_state():
    state = _read_command_center_state()
    return {
        "ok": True,
        "partner": state.get("partner", {}),
        "shadow": state.get("shadow", {}),
        "autonomy": state.get("autonomy", {}),
        "loop": state.get("autonomy_loop", {}),
    }


@router.post("/autonomy")
def set_autonomy_dial(payload: AutonomyDialRequest):
    state = _read_command_center_state()
    level = int(payload.level)
    partner = state.setdefault("partner", _default_command_center_state()["partner"])
    autonomy_cap = int(partner.get("autonomy_ceiling", 25))
    bounded_level = min(level, autonomy_cap)
    state["autonomy"] = {
        "level": bounded_level,
        "mode": _autonomy_mode_from_level(bounded_level),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "requested_level": level,
    }
    _write_command_center_state(state)
    return {"ok": True, "autonomy": state["autonomy"]}


@router.post("/shadow")
def set_shadow_mode(payload: ShadowModeRequest):
    state = _read_command_center_state()
    state["shadow_mode"] = {
        "enabled": bool(payload.enabled),
        "lane": payload.lane,
        "last_activation": (
            datetime.now(timezone.utc).isoformat() if payload.enabled else None
        ),
    }
    _write_command_center_state(state)
    return {"ok": True, "shadow_mode": state["shadow_mode"]}


@router.post("/partner/evolve")
def evolve_partner(payload: OrganismEvolveRequest):
    state = _read_command_center_state()
    partner = state.setdefault("partner", _default_command_center_state()["partner"])
    tiers = _partner_tiers()
    current_tier = partner.get("tier", tiers[0])
    current_index = tiers.index(current_tier) if current_tier in tiers else 0
    next_index = min(current_index + 1, len(tiers) - 1)
    partner["tier"] = tiers[next_index]
    partner["tier_index"] = next_index
    partner["autonomy_ceiling"] = min(100, 25 + (next_index * 15))

    partner.setdefault(
        "traits", {"logic": 0.60, "empathy": 0.64, "precision": 0.62, "stability": 0.70}
    )
    partner["traits_mode"] = "deterministic_static"

    history = state.setdefault("evolution_tree", {}).setdefault("history", [])
    history.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entity": "partner",
            "from": current_tier,
            "to": partner["tier"],
            "reason": payload.reason,
        }
    )
    _write_command_center_state(state)
    return {"ok": True, "partner": partner, "history": history[-10:]}


@router.post("/shadow/evolve")
def evolve_shadow(payload: OrganismEvolveRequest):
    state = _read_command_center_state()
    shadow = state.setdefault("shadow", _default_command_center_state()["shadow"])
    tiers = _shadow_tiers()
    current_tier = shadow.get("tier", tiers[0])
    current_index = tiers.index(current_tier) if current_tier in tiers else 0
    next_index = min(current_index + 1, len(tiers) - 1)
    shadow["tier"] = tiers[next_index]
    shadow["tier_index"] = next_index
    shadow["risk_precision"] = min(
        0.99, round(float(shadow.get("risk_precision", 0.35)) + 0.08, 2)
    )
    shadow["tactical_authority"] = (
        "policy_bounded_autonomy" if next_index >= 4 else "operator_approval"
    )

    history = state.setdefault("evolution_tree", {}).setdefault("history", [])
    history.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entity": "shadow",
            "from": current_tier,
            "to": shadow["tier"],
            "reason": payload.reason,
        }
    )
    _write_command_center_state(state)
    return {"ok": True, "shadow": shadow, "history": history[-10:]}


@router.post("/loop/tick")
def tick_autonomy_loop(payload: LoopTickRequest):
    state = _read_command_center_state()
    loop = state.setdefault(
        "autonomy_loop", _default_command_center_state()["autonomy_loop"]
    )
    loop["tick_count"] = int(loop.get("tick_count", 0)) + 1
    loop["last_tick"] = datetime.now(timezone.utc).isoformat()
    loop["last_cycle_label"] = payload.cycle_label
    loop["last_summary"] = {
        "brain": "mission_plan_updated",
        "shadow": "risk_scan_completed",
        "immune": "policy_guardrails_applied",
        "memory": "experience_archive_appended",
        "reproduction": "blueprint_variants_ready",
    }
    _write_command_center_state(state)
    return {"ok": True, "loop": loop}


@router.post("/evolution/promote")
def promote_partner(payload: EvolutionPromoteRequest):
    state = _read_command_center_state()
    evo = state.setdefault(
        "evolution_tree", _default_command_center_state()["evolution_tree"]
    )
    tiers = evo.get("tiers", ["seed", "scout", "operator", "architect", "sovereign"])
    partners = evo.setdefault("partners", [])

    partner = next(
        (p for p in partners if p.get("partner_id") == payload.partner_id), None
    )
    if partner is None:
        partner = {"partner_id": payload.partner_id, "tier": tiers[0], "xp": 0}
        partners.append(partner)

    current_tier = partner.get("tier", tiers[0])
    current_index = tiers.index(current_tier) if current_tier in tiers else 0
    next_index = min(current_index + 1, len(tiers) - 1)
    partner["tier"] = tiers[next_index]
    partner["xp"] = int(partner.get("xp", 0)) + 10

    history = evo.setdefault("history", [])
    history.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "partner_id": payload.partner_id,
            "from": current_tier,
            "to": partner["tier"],
            "reason": payload.reason,
        }
    )

    _write_command_center_state(state)
    return {"ok": True, "partner": partner, "history": history[-10:]}


@router.get("/marketplace/list")
def marketplace_list(status: Optional[str] = Query(default=None)):
    state = _read_command_center_state()
    marketplace = state.setdefault("marketplace", {"missions": []})
    missions = marketplace.setdefault("missions", [])
    if status:
        missions = [
            m for m in missions if str(m.get("status", "")).lower() == status.lower()
        ]
    return {"ok": True, "missions": missions, "count": len(missions)}


@router.post("/marketplace/publish")
def marketplace_publish(payload: MarketplacePublishRequest):
    state = _read_command_center_state()
    marketplace = state.setdefault("marketplace", {"missions": []})
    missions = marketplace.setdefault("missions", [])
    listing = {
        "listing_id": f"mk-{secrets.token_hex(3)}",
        "mission_type": payload.mission_type,
        "title": payload.title,
        "reward_points": int(payload.reward_points),
        "tags": payload.tags,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    missions.append(listing)
    _write_command_center_state(state)
    return {"ok": True, "listing": listing}
