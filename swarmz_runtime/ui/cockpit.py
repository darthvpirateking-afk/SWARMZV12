from fastapi import APIRouter

router = APIRouter()


@router.get("/cockpit/panels")
def get_cockpit_panels():
    return {
        "panels": [
            "Avatar Panel",
            "Mission Console",
            "Swarm Grid v2",
            "Cosmology Map v2",
            "Patchpack Timeline",
            "System Health + Governor Status",
            "Operator Session Panel",
            "Shadow-Ledger Alerts",
        ]
    }


@router.get("/cockpit/layout")
def get_cockpit_layout():
    return {
        "layout": {
            "top_bar": ["avatar presence", "operator rank", "session state"],
            "left_rail": ["missions", "swarm", "cosmology", "patchpack", "system"],
            "main_canvas": "dynamic panel",
            "right_rail": ["mission log", "swarm events", "patchpack events"],
        }
    }


@router.get("/cockpit/status")
def get_cockpit_status():
    """Live cockpit status: health, avatar state, realm summary, swarm tier, mission rank."""
    from datetime import datetime, timezone

    from swarmz_runtime.avatar.avatar_matrix import get_avatar_matrix
    from swarmz_runtime.core.mission_ranks import list_ranks
    from swarmz_runtime.core.realms import get_realm_registry
    from swarmz_runtime.core.swarm_tiers import list_tiers
    from swarmz_runtime.core.throne import get_throne

    throne = get_throne()
    avatar = get_avatar_matrix()
    realms = get_realm_registry()
    avatar_state = avatar.get_matrix_state()

    return {
        "ok": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "throne": throne.get_state(),
        "avatar": {
            "active_variant": avatar_state["active_variant"],
            "current_state": avatar_state["current_state"],
        },
        "realms": {
            "total": len(realms.list_realms()),
            "active": sum(1 for r in realms.list_realms() if r["active"]),
        },
        "swarm_tiers": {"total_tiers": len(list_tiers())},
        "mission_ranks": {"total_ranks": len(list_ranks())},
        "panels": [
            "Avatar Panel",
            "Mission Console",
            "Swarm Grid v2",
            "Cosmology Map v2",
            "Patchpack Timeline",
            "System Health + Governor Status",
            "Operator Session Panel",
            "Shadow-Ledger Alerts",
        ],
    }
