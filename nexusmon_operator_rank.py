"""
NEXUSMON — Operator Rank Progression System (Phase 15)
Operator XP → Rank → Permissions → Traits → Evolution Unlocks

Storage: data/operator_rank.json
Fusion: fuse_operator_rank(app)
"""

import json
import os
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

# ─── Constants ───────────────────────────────────────────────────────────────

DATA_DIR = os.environ.get("DATA_DIR", "data")
RANK_FILE = os.path.join(DATA_DIR, "operator_rank.json")

RANKS = ["E", "D", "C", "B", "A", "S"]

RANK_THRESHOLDS = {
    "E": 0,
    "D": 50,
    "C": 150,
    "B": 400,
    "A": 800,
    "S": 1500,
}

# XP awarded per action (called internally by other subsystems)
XP_TABLE = {
    "complete_mission_E": 10,
    "complete_mission_D": 25,
    "complete_mission_C": 50,
    "complete_mission_B": 100,
    "complete_mission_A": 200,
    "complete_mission_S": 500,
    "approve_artifact": 5,
    "reject_artifact": 5,
    "log_prediction": 5,
    "log_cognition_error": 5,
    "decision_autopsy": 15,
    "evolution_sync": 10,
    "spawn_worker": 3,
    "create_belief": 5,
}

# Traits unlocked at each rank
RANK_TRAITS = {
    "E": [],
    "D": ["Worker Control", "Artifact Review"],
    "C": ["Evolution Sync", "Mission Governance"],
    "B": ["Module Activation", "Multi-Worker Coordination"],
    "A": ["Full Governance", "System-Level Reasoning"],
    "S": ["Organism Override", "Evolution Tier Unlock"],
}

# Permission matrix: minimum rank required for each action
PERMISSION_MATRIX = {
    "run_mission_E": "E",
    "run_mission_D": "D",
    "run_mission_C": "C",
    "run_mission_B": "B",
    "run_mission_A": "A",
    "run_mission_S": "S",
    "approve_artifact": "D",
    "reject_artifact": "D",
    "approve_mission": "C",
    "spawn_worker": "D",
    "activate_module": "B",
    "evolution_sync": "C",
    "full_organism_control": "S",
}


# ─── Storage ─────────────────────────────────────────────────────────────────

def _default_state():
    return {
        "xp": 0,
        "xp_history": [],
        "created_at": time.time(),
        "updated_at": time.time(),
    }


def _load_state() -> dict:
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(RANK_FILE):
        try:
            with open(RANK_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return _default_state()


def _save_state(state: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    state["updated_at"] = time.time()
    with open(RANK_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ─── Core Logic ──────────────────────────────────────────────────────────────

def rank_from_xp(xp: int) -> str:
    """Derive rank from XP. Rank is always computed, never stored directly."""
    current = "E"
    for rank in RANKS:
        if xp >= RANK_THRESHOLDS[rank]:
            current = rank
    return current


def next_rank_info(xp: int) -> dict:
    """Return next rank and XP needed. Returns None if already S."""
    current = rank_from_xp(xp)
    idx = RANKS.index(current)
    if idx >= len(RANKS) - 1:
        return {"next_rank": None, "xp_needed": 0, "progress": 1.0}
    next_rank = RANKS[idx + 1]
    threshold = RANK_THRESHOLDS[next_rank]
    current_threshold = RANK_THRESHOLDS[current]
    span = threshold - current_threshold
    progress_in_tier = xp - current_threshold
    return {
        "next_rank": next_rank,
        "xp_needed": threshold - xp,
        "progress": round(progress_in_tier / span, 3) if span > 0 else 1.0,
    }


def traits_for_xp(xp: int) -> list:
    """Return all unlocked traits up to current rank."""
    current = rank_from_xp(xp)
    idx = RANKS.index(current)
    traits = []
    for i in range(idx + 1):
        traits.extend(RANK_TRAITS[RANKS[i]])
    return traits


def has_permission(xp: int, action: str) -> bool:
    """Check if operator has permission for an action."""
    if action not in PERMISSION_MATRIX:
        return True  # unknown actions are allowed by default
    required_rank = PERMISSION_MATRIX[action]
    current_rank = rank_from_xp(xp)
    return RANKS.index(current_rank) >= RANKS.index(required_rank)


def award_xp(action: str, detail: str = "") -> dict:
    """Award XP for an action. Returns updated rank state."""
    amount = XP_TABLE.get(action, 0)
    if amount == 0:
        return {"awarded": 0, "reason": f"unknown action: {action}"}

    state = _load_state()
    old_rank = rank_from_xp(state["xp"])
    state["xp"] += amount

    # Keep last 100 XP events
    state["xp_history"].append({
        "action": action,
        "xp": amount,
        "detail": detail,
        "timestamp": time.time(),
    })
    state["xp_history"] = state["xp_history"][-100:]

    new_rank = rank_from_xp(state["xp"])
    ranked_up = old_rank != new_rank

    _save_state(state)

    result = {
        "awarded": amount,
        "action": action,
        "total_xp": state["xp"],
        "rank": new_rank,
        "ranked_up": ranked_up,
    }
    if ranked_up:
        result["old_rank"] = old_rank
        result["new_rank"] = new_rank
        result["new_traits"] = RANK_TRAITS.get(new_rank, [])
    return result


def get_operator_rank_state() -> dict:
    """Full operator rank state for API responses."""
    state = _load_state()
    xp = state["xp"]
    rank = rank_from_xp(xp)
    nri = next_rank_info(xp)
    return {
        "rank": rank,
        "xp": xp,
        "next_rank": nri["next_rank"],
        "xp_needed": nri["xp_needed"],
        "progress": nri["progress"],
        "traits": traits_for_xp(xp),
        "permissions": {
            action: has_permission(xp, action)
            for action in PERMISSION_MATRIX
        },
        "updated_at": state.get("updated_at"),
    }


# ─── Rank Gate Middleware ────────────────────────────────────────────────────

def rank_gate(action: str):
    """
    Dependency that checks operator rank before allowing an action.
    Usage in routes:
        @router.post("/v1/some/action")
        async def some_action(gate=Depends(rank_gate("approve_mission"))):
            ...
    """
    from fastapi import Depends

    async def _check():
        state = _load_state()
        xp = state["xp"]
        current = rank_from_xp(xp)
        if not has_permission(xp, action):
            required = PERMISSION_MATRIX.get(action, "?")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "insufficient_rank",
                    "message": f"Action '{action}' requires rank {required}. Current rank: {current}.",
                    "current_rank": current,
                    "required_rank": required,
                    "current_xp": xp,
                    "xp_needed": RANK_THRESHOLDS.get(required, 0) - xp,
                }
            )
        return {"rank": current, "xp": xp, "action": action}

    return Depends(_check)


# ─── Request Models ──────────────────────────────────────────────────────────

class AwardXPRequest(BaseModel):
    action: str
    detail: Optional[str] = ""


# ─── Routes ──────────────────────────────────────────────────────────────────

router = APIRouter(tags=["operator-rank"])


@router.get("/v1/operator/rank")
async def get_rank():
    """Current operator rank, XP, progress, traits, permissions, and mission stats."""
    data = get_operator_rank_state()
    # Inject live mission stats for avatar polling
    try:
        from datetime import datetime, timezone
        from nexusmon_mission_engine import list_missions, mission_xp_total
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        all_missions = list_missions()
        running = [m for m in all_missions if m.get("status") == "RUNNING"]
        # Mission progress: % of tasks completed in latest running mission
        progress_pct = 0.0
        if running:
            tasks = running[-1].get("tasks", [])
            if tasks:
                done = sum(1 for t in tasks if t.get("status") == "COMPLETED")
                progress_pct = round(done / len(tasks) * 100, 1)
        elif all_missions:
            completed_count = sum(1 for m in all_missions if m.get("status") == "COMPLETED")
            progress_pct = round(completed_count / len(all_missions) * 100, 1)
        data["missions"] = {
            "active_missions": len(running),
            "completed_today": len([m for m in all_missions if m.get("completed_at", "").startswith(today)]),
            "total_xp_from_missions": mission_xp_total(),
            "latest_completed_goal": next(
                (m["goal"] for m in reversed(all_missions) if m.get("status") == "COMPLETED"), None
            ),
            "progress_pct": progress_pct,
        }
    except Exception:
        data["missions"] = {"active_missions": 0, "completed_today": 0,
                            "total_xp_from_missions": 0, "latest_completed_goal": None,
                            "progress_pct": 0.0}
    return data


@router.get("/v1/operator/traits")
async def get_traits():
    """Unlocked traits for current rank."""
    state = _load_state()
    xp = state["xp"]
    return {
        "rank": rank_from_xp(xp),
        "traits": traits_for_xp(xp),
    }


@router.get("/v1/operator/permissions")
async def get_permissions():
    """Full permission matrix for current rank."""
    state = _load_state()
    xp = state["xp"]
    rank = rank_from_xp(xp)
    return {
        "rank": rank,
        "permissions": {
            action: has_permission(xp, action)
            for action in PERMISSION_MATRIX
        },
    }


@router.get("/v1/operator/xp/history")
async def get_xp_history():
    """Recent XP events (last 100)."""
    state = _load_state()
    return {
        "total_xp": state["xp"],
        "rank": rank_from_xp(state["xp"]),
        "history": state.get("xp_history", []),
    }


@router.post("/v1/operator/xp")
async def post_award_xp(req: AwardXPRequest):
    """Award XP for an action. Called internally by mission engine, vault, cognition, etc."""
    if req.action not in XP_TABLE:
        raise HTTPException(status_code=400, detail={
            "error": "invalid_action",
            "message": f"Unknown XP action: {req.action}",
            "valid_actions": list(XP_TABLE.keys()),
        })
    result = award_xp(req.action, req.detail)
    return result


@router.get("/v1/operator/leaderboard")
async def get_leaderboard():
    """Rank progression ladder — thresholds, XP table, current position."""
    state = _load_state()
    xp = state["xp"]
    rank = rank_from_xp(xp)
    return {
        "current": {"rank": rank, "xp": xp},
        "thresholds": RANK_THRESHOLDS,
        "xp_table": XP_TABLE,
        "ranks": [
            {
                "rank": r,
                "xp_required": RANK_THRESHOLDS[r],
                "traits": RANK_TRAITS[r],
                "unlocked": RANKS.index(rank) >= RANKS.index(r),
            }
            for r in RANKS
        ],
    }


# ─── Evolution Tier Mirroring ────────────────────────────────────────────────

EVOLUTION_TIERS = ["DORMANT", "INITIATED", "ACTIVE", "EVOLVED", "ASCENDED"]

RANK_TO_TIER = {
    "E": "DORMANT", "D": "INITIATED", "C": "ACTIVE",
    "B": "EVOLVED", "A": "ASCENDED", "S": "ASCENDED",
}

TIER_MODULES = {
    "DORMANT":   [],
    "INITIATED": ["Worker Node v1"],
    "ACTIVE":    ["Worker Node v1", "Vault Indexer", "Cognition Calibrator"],
    "EVOLVED":   ["Worker Node v1", "Vault Indexer", "Cognition Calibrator", "Parallel Worker Node v2"],
    "ASCENDED":  ["Worker Node v1", "Vault Indexer", "Cognition Calibrator", "Parallel Worker Node v2", "Evolution Engine v2"],
}

TIER_TRAITS = {
    "DORMANT":   [],
    "INITIATED": ["Stable Execution", "Basic Parallelism"],
    "ACTIVE":    ["Stable Execution", "Basic Parallelism", "Artifact Awareness", "Mission Memory"],
    "EVOLVED":   ["Stable Execution", "Basic Parallelism", "Artifact Awareness", "Mission Memory",
                  "Autonomous Draft Mode", "Multi-Worker Coordination"],
    "ASCENDED":  ["Stable Execution", "Basic Parallelism", "Artifact Awareness", "Mission Memory",
                  "Autonomous Draft Mode", "Multi-Worker Coordination",
                  "System-Level Reasoning", "Governance Reflex"],
}

TIER_UNLOCK_REQUIREMENTS = {
    "DORMANT":   "Starting tier",
    "INITIATED": "Complete 5 E-rank missions",
    "ACTIVE":    "Complete 3 D-rank missions",
    "EVOLVED":   "Complete 2 C-rank missions",
    "ASCENDED":  "Complete 1 B-rank + 1 A-rank mission",
}


def tier_from_rank(rank: str) -> str:
    return RANK_TO_TIER.get(rank, "DORMANT")


@router.get("/v1/operator/evolution")
async def get_operator_evolution():
    """Evolution tier, modules, and traits derived from operator rank."""
    state = _load_state()
    rank = rank_from_xp(state["xp"])
    tier = tier_from_rank(rank)
    return {
        "rank": rank,
        "tier": tier,
        "modules": TIER_MODULES.get(tier, []),
        "evolution_traits": TIER_TRAITS.get(tier, []),
        "unlock_requirement": TIER_UNLOCK_REQUIREMENTS.get(tier, ""),
        "all_tiers": [
            {
                "tier": t,
                "modules": TIER_MODULES[t],
                "traits": TIER_TRAITS[t],
                "requirement": TIER_UNLOCK_REQUIREMENTS[t],
                "unlocked": EVOLUTION_TIERS.index(tier) >= EVOLUTION_TIERS.index(t),
            }
            for t in EVOLUTION_TIERS
        ],
    }


# ─── Fusion ──────────────────────────────────────────────────────────────────

def fuse_operator_rank(app):
    """Mount operator rank routes into the FastAPI app."""
    app.include_router(router)
    print("[NEXUSMON] Operator rank system fused.")
