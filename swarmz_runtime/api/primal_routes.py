import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from swarmz_runtime.core.fusion_registry import FusionRegistry
from swarmz_runtime.core.operator_ecosystem import OperatorEcosystem


router = APIRouter()
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_DOCTRINE_PATH = _ROOT_DIR / "config" / "doctrine_primal_block.json"
_STATE_SLATE_PATH = _ROOT_DIR / "config" / "primal_state_slate.json"
_ecosystem = OperatorEcosystem(_ROOT_DIR)
_fusion_registry = FusionRegistry(_ROOT_DIR)


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _state_for_path(relative_path: str) -> str:
    return "LINKED" if (_ROOT_DIR / relative_path).exists() else "MISSING"


def _default_primal_state_slate() -> Dict[str, Any]:
    doctrine = _read_json(_DOCTRINE_PATH)
    systems = doctrine.get("systems", {}) if isinstance(doctrine, dict) else {}
    channels = doctrine.get("channels", {}) if isinstance(doctrine, dict) else {}
    artifacts = doctrine.get("artifacts", {}) if isinstance(doctrine, dict) else {}

    runtime_map = {
        "PARTNER_PRIME": "swarmz_runtime/core/brain.py",
        "LEGION_UMBRA": "swarmz_runtime/shadow_ledger/shadow_ledger.py",
        "FORGE_HEARTH": "swarmz_runtime/api/operator_ecosystem_routes.py",
        "RIFTWALK": "swarmz_runtime/core/mission_engine_v4.py",
        "SIGILSTACK": "swarmz_runtime/api/fusion_routes.py",
        "NEXUSFRAME": "web/index.html",
        "DATAVEIN": "swarmz_runtime/storage/db.py",
    }

    mapped_systems: Dict[str, Any] = {}
    warnings: List[str] = []
    for key in systems.keys() if isinstance(systems, dict) else runtime_map.keys():
        runtime_path = runtime_map.get(key, "")
        state = _state_for_path(runtime_path) if runtime_path else "MISSING"
        if state == "MISSING":
            warnings.append(f"missing_runtime_path:{key}")
        mapped_systems[key] = {
            "runtime_path": runtime_path,
            "state": state,
        }

    mapped_channels = {
        "MINDLINE": "LOGIC_PORT:8012",
        "CODELINE": "DATA_PORT:8012",
        "SIGHTLINE": "UI_PORT:8012",
        "PATHLINE": "MISSION_PORT:8012",
        "GHOSTLINE": "SIM_PORT:8012",
    }
    if isinstance(channels, dict):
        for key in channels.keys():
            mapped_channels.setdefault(key, "PORT:8012")

    return {
        "PRIMAL_STATE_SLATE": {
            "SYSTEM_STATUS": "READY" if not warnings else "DEGRADED",
            "SYSTEMS": mapped_systems,
            "CHANNELS": mapped_channels,
            "ARTIFACTS": artifacts,
            "ENDPOINTS": {
                "health": "/v1/health",
                "dispatch": "/v1/dispatch",
                "runtime_status": "/v1/runtime/status",
                "runtime_scoreboard": "/v1/runtime/scoreboard",
                "prime_state": "/v1/operator-os/prime-state",
                "riftwalk_trace": "/v1/riftwalk/trace",
                "sigilstack_registry": "/v1/sigilstack/registry",
            },
            "WARNINGS": warnings,
            "NEXT_ACTIONS": ["SEEDRUN_01", "SEEDRUN_02", "SEEDRUN_03"],
        }
    }


def _load_primal_state_slate() -> Dict[str, Any]:
    configured = _read_json(_STATE_SLATE_PATH)
    if configured.get("PRIMAL_STATE_SLATE"):
        return configured
    return _default_primal_state_slate()


def _extract_mission_id(row: Dict[str, Any]) -> Optional[str]:
    details = row.get("details", {}) if isinstance(row.get("details"), dict) else {}
    mission_id = details.get("mission_id") or row.get("mission_id")
    if mission_id is None:
        return None
    mid = str(mission_id).strip()
    return mid if mid else None


def _mission_trace_rows(mission_id: Optional[str], limit: int) -> List[Dict[str, Any]]:
    events = _ecosystem.list_timeline()
    missions = _ecosystem.list_missions()

    traces: Dict[str, Dict[str, Any]] = {}
    for row in events:
        mid = _extract_mission_id(row)
        if not mid:
            continue
        if mission_id and mid != mission_id:
            continue
        trace = traces.setdefault(mid, {"mission_id": mid, "steps": [], "result": {}})
        trace["steps"].append(
            {
                "event_type": row.get("event_type"),
                "domain": row.get("domain"),
                "risk": row.get("risk"),
                "created_at": row.get("created_at"),
                "details": row.get("details", {}),
            }
        )

    for row in missions:
        mid = str(row.get("mission_id", "")).strip()
        if not mid:
            continue
        if mission_id and mid != mission_id:
            continue
        trace = traces.setdefault(mid, {"mission_id": mid, "steps": [], "result": {}})
        trace["result"] = {
            "status": row.get("status"),
            "risk_level": row.get("risk_level"),
            "budget_cents": row.get("budget_cents"),
            "policy_profile": row.get("policy_profile"),
            "agents": row.get("agents", []),
            "updated_at": row.get("updated_at"),
        }

    rows = list(traces.values())
    rows.sort(key=lambda item: item.get("result", {}).get("updated_at") or "")
    return rows[-limit:]


def _infer_tier(tags: List[str]) -> int:
    for tag in tags:
        lowered = str(tag).lower()
        if lowered.startswith("tier:") or lowered.startswith("tier-"):
            candidate = lowered.split(":")[-1].split("-")[-1]
            if candidate.isdigit():
                return int(candidate)
    return 1


def _infer_type(source: str, tags: List[str]) -> str:
    lowered = f"{source} {' '.join(tags)}".lower()
    if "attack" in lowered:
        return "ATTACK"
    if "defense" in lowered:
        return "DEFENSE"
    if "field" in lowered:
        return "FIELD"
    return "UTILITY"


@router.get("/riftwalk/trace")
def riftwalk_trace(
    mission_id: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
):
    rows = _mission_trace_rows(mission_id=mission_id, limit=limit)
    return {"ok": True, "trace": rows, "count": len(rows)}


@router.get("/sigilstack/registry")
def sigilstack_registry():
    rows = _fusion_registry.list_entries()
    items: List[Dict[str, Any]] = []
    for row in rows:
        payload = row.get("payload", {}) if isinstance(row, dict) else {}
        tags = payload.get("tags", []) if isinstance(payload.get("tags"), list) else []
        source = str(payload.get("source", ""))
        items.append(
            {
                "id": payload.get("entry_id"),
                "name": payload.get("title"),
                "tier": _infer_tier(tags),
                "type": _infer_type(source, [str(t) for t in tags]),
                "tags": tags,
            }
        )
    return {"ok": True, "registry": items, "count": len(items)}
