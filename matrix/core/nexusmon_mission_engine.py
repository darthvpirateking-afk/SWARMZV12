# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
NEXUSMON Mission Engine
───────────────────────
DAG-based mission decomposition and execution.

Wire into swarmz_server.py after fuse_cognition:

    try:
        from nexusmon_mission_engine import fuse_mission_engine
        fuse_mission_engine(app)
    except Exception as e:
        print(f"Warning: mission engine failed: {e}")
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# STORAGE HELPERS  (mirror nexusmon_organism.py exactly)
# ══════════════════════════════════════════════════════════════

def _data_dir() -> Path:
    db = os.environ.get("DATABASE_URL", "data/nexusmon.db")
    d = Path(db).parent
    d.mkdir(parents=True, exist_ok=True)
    return d


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def _append_jsonl(path: Path, record: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _rewrite_jsonl(path: Path, records: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


# ══════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════

_MISSIONS_FILE = "missions_v2.jsonl"   # never touch missions.jsonl

_XP_MAP: Dict[str, int] = {
    "E": 10, "D": 25, "C": 50, "B": 100, "A": 200, "S": 500,
}

_RISK_MAP: Dict[str, str] = {
    "E": "LOW", "D": "LOW",
    "C": "MEDIUM", "B": "MEDIUM",
    "A": "HIGH", "S": "CRITICAL",
}

# E/D auto-run; C/B run but flag; A/S need approval first
_AUTO_RANKS = {"E", "D"}
_FLAG_RANKS  = {"C", "B"}
_GATE_RANKS  = {"A", "S"}

VALID_RANKS   = set(_XP_MAP.keys())
VALID_TASK_TYPES = {"RESEARCH", "WRITE", "ANALYZE", "CODE", "CALL_API", "DECIDE"}
VALID_STATUSES   = {"PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"}


# ══════════════════════════════════════════════════════════════
# MISSION CRUD
# ══════════════════════════════════════════════════════════════

def _missions_path() -> Path:
    return _data_dir() / _MISSIONS_FILE


def _load_missions() -> List[Dict]:
    return _load_jsonl(_missions_path())


def _save_mission(mission: Dict) -> None:
    missions = _load_missions()
    idx = next((i for i, m in enumerate(missions) if m["id"] == mission["id"]), None)
    if idx is not None:
        missions[idx] = mission
        _rewrite_jsonl(_missions_path(), missions)
    else:
        _append_jsonl(_missions_path(), mission)


# ══════════════════════════════════════════════════════════════
# AI DECOMPOSITION
# ══════════════════════════════════════════════════════════════

def _decompose_goal(goal: str, rank: str) -> List[Dict]:
    """Break a goal string into typed tasks using AI. Falls back gracefully."""
    prompt = (
        f"You are a mission decomposition engine. Break this goal into typed tasks.\n"
        f"Goal: {goal}\n"
        f"Rank: {rank} (risk: {_RISK_MAP.get(rank, 'LOW')})\n\n"
        "Return ONLY valid JSON — no markdown, no explanation:\n"
        '{"tasks": [{"type": "RESEARCH|WRITE|ANALYZE|CODE|CALL_API|DECIDE", '
        '"description": "...", "dependencies": [], "worker_type": "..."}]}'
    )
    try:
        from core.model_router import call as _llm_call
        result = _llm_call(
            messages=[{"role": "user", "content": prompt}],
            system="You are a structured task planner. Output only JSON.",
            max_tokens=800,
        )
        text = result.get("text", "")
        # Strip markdown fences if present
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text.strip())
        raw_tasks = parsed.get("tasks", [])
        if not raw_tasks:
            raise ValueError("empty task list")
        return raw_tasks
    except Exception as exc:
        logger.warning("Mission decomposition AI failed (%s) — using fallback", exc)
        return [
            {
                "type": "ANALYZE",
                "description": f"Analyze and execute: {goal}",
                "dependencies": [],
                "worker_type": "ANALYST",
            }
        ]


# ══════════════════════════════════════════════════════════════
# DAG UTILITIES
# ══════════════════════════════════════════════════════════════

def _build_tasks(raw_tasks: List[Dict], mission_id: str) -> tuple[List[Dict], List[Dict]]:
    """Create Task dicts and DAG edge list from raw AI output."""
    tasks: List[Dict] = []
    id_map: Dict[int, str] = {}  # index → task id

    for i, rt in enumerate(raw_tasks):
        tid = f"{mission_id[:8]}-t{i}"
        id_map[i] = tid
        tasks.append({
            "id": tid,
            "mission_id": mission_id,
            "type": str(rt.get("type", "ANALYZE")).upper(),
            "description": str(rt.get("description", "")),
            "status": "PENDING",
            "dependencies": [],  # filled in after all IDs are assigned
            "worker_type": str(rt.get("worker_type", "GENERAL")),
            "input": {},
            "output": {},
            "error": "",
            "started_at": "",
            "completed_at": "",
            "_raw_deps": rt.get("dependencies", []),  # temp field
        })

    # Resolve dependency references (indices or names) to task IDs
    dag_edges: List[Dict] = []
    for i, task in enumerate(tasks):
        raw_deps = task.pop("_raw_deps", [])
        resolved: List[str] = []
        for dep in raw_deps:
            if isinstance(dep, int) and dep < len(tasks):
                resolved.append(id_map[dep])
            elif isinstance(dep, str):
                # Match by index string or description prefix
                for j, t2 in enumerate(tasks):
                    if str(j) == dep or t2["description"].startswith(dep):
                        resolved.append(id_map[j])
                        break
        task["dependencies"] = resolved
        for dep_id in resolved:
            dag_edges.append({"from": dep_id, "to": task["id"]})

    return tasks, dag_edges


def _detect_cycles(tasks: List[Dict]) -> List[List[str]]:
    """
    Detect cycles in task dependency graph using Tarjan's SCC algorithm.
    
    Returns list of strongly connected components (SCCs) with size > 1.
    Each SCC represents a cycle.
    """
    graph: Dict[str, List[str]] = {t["id"]: t.get("dependencies", []) for t in tasks}
    
    index_counter = [0]
    stack: List[str] = []
    indices: Dict[str, int] = {}
    lowlinks: Dict[str, int] = {}
    on_stack: Dict[str, bool] = {}
    sccs: List[List[str]] = []
    
    def strongconnect(node: str):
        indices[node] = index_counter[0]
        lowlinks[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)
        on_stack[node] = True
        
        for dep in graph.get(node, []):
            if dep not in graph:
                continue  # Skip external dependencies
            if dep not in indices:
                strongconnect(dep)
                lowlinks[node] = min(lowlinks[node], lowlinks[dep])
            elif on_stack.get(dep, False):
                lowlinks[node] = min(lowlinks[node], indices[dep])
        
        if lowlinks[node] == indices[node]:
            component: List[str] = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                component.append(w)
                if w == node:
                    break
            if len(component) > 1:
                sccs.append(component)
    
    for node in graph:
        if node not in indices:
            strongconnect(node)
    
    return sccs


def _topo_order(tasks: List[Dict]) -> List[str]:
    """
    Return task IDs in topological execution order (Kahn's algorithm).
    
    Raises ValueError if cyclic dependencies detected.
    """
    id_to_task = {t["id"]: t for t in tasks}
    in_degree: Dict[str, int] = {t["id"]: 0 for t in tasks}
    children: Dict[str, List[str]] = {t["id"]: [] for t in tasks}

    for task in tasks:
        for dep in task.get("dependencies", []):
            if dep in in_degree:
                in_degree[task["id"]] = in_degree[task["id"]] + 1
                children[dep].append(task["id"])

    queue = [tid for tid, deg in in_degree.items() if deg == 0]
    order: List[str] = []
    while queue:
        tid = queue.pop(0)
        order.append(tid)
        for child in children[tid]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    # Detect cycles: if not all tasks processed, there's a cycle
    if len(order) != len(tasks):
        cycles = _detect_cycles(tasks)
        cycle_desc = "; ".join([" → ".join(c) for c in cycles])
        raise ValueError(f"Cyclic dependencies detected in mission DAG: {cycle_desc}")
    
    return order


# ══════════════════════════════════════════════════════════════
# PUBLIC FUNCTIONS
# ══════════════════════════════════════════════════════════════

def create_mission(goal: str, rank: str = "E", metadata: Optional[Dict] = None) -> Dict:
    """Decompose a goal into tasks and persist the mission."""
    rank = rank.upper()
    if rank not in VALID_RANKS:
        rank = "E"

    mid = str(uuid4())
    raw_tasks = _decompose_goal(goal, rank)
    tasks, dag_edges = _build_tasks(raw_tasks, mid)

    mission: Dict[str, Any] = {
        "id": mid,
        "goal": goal,
        "rank": rank,
        "status": "PENDING",
        "tasks": tasks,
        "dag_edges": dag_edges,
        "artifact_ids": [],
        "operator_approved": rank not in _GATE_RANKS,  # pre-approved for E/D/C/B
        "risk_level": _RISK_MAP.get(rank, "LOW"),
        "created_at": _utc(),
        "started_at": "",
        "completed_at": "",
        "xp_awarded": 0,
        "metadata": metadata or {},
    }
    _save_mission(mission)
    logger.info("Mission created: %s rank=%s tasks=%d", mid, rank, len(tasks))
    return mission


def approve_mission(mission_id: str) -> Dict:
    mission = get_mission(mission_id)
    if not mission:
        raise ValueError(f"Mission not found: {mission_id}")
    mission["operator_approved"] = True
    _save_mission(mission)
    return mission


def run_mission(mission_id: str) -> Dict:
    """Execute a mission's tasks in DAG order."""
    mission = get_mission(mission_id)
    if not mission:
        raise ValueError(f"Mission not found: {mission_id}")

    if mission["status"] in ("COMPLETED", "CANCELLED"):
        return mission

    rank = mission.get("rank", "E")

    # Gate A/S missions until approved
    if rank in _GATE_RANKS and not mission.get("operator_approved"):
        mission["status"] = "PENDING"
        mission["metadata"] = {
            **mission.get("metadata", {}),
            "blocked_reason": f"Rank {rank} missions require operator approval",
        }
        _save_mission(mission)
        return mission

    # Flag C/B for review but continue
    if rank in _FLAG_RANKS:
        logger.info("Mission %s rank=%s flagged for operator review (proceeding)", mission_id, rank)

    mission["status"] = "RUNNING"
    mission["started_at"] = _utc()
    _save_mission(mission)

    tasks: List[Dict] = mission.get("tasks", [])
    task_map = {t["id"]: t for t in tasks}
    order = _topo_order(tasks)

    all_ok = True
    for tid in order:
        task = task_map.get(tid)
        if not task:
            continue

        # Check all dependencies completed
        deps_ok = all(
            task_map.get(dep, {}).get("status") == "COMPLETED"
            for dep in task.get("dependencies", [])
        )
        if not deps_ok:
            task["status"] = "FAILED"
            task["error"] = "dependency not completed"
            all_ok = False
            continue

        task["status"] = "RUNNING"
        task["started_at"] = _utc()
        _save_mission(mission)

        try:
            output = _execute_task(task, mission)
            task["output"] = output
            task["status"] = "COMPLETED"
            task["completed_at"] = _utc()
        except Exception as exc:
            task["status"] = "FAILED"
            task["error"] = str(exc)
            task["completed_at"] = _utc()
            all_ok = False
            logger.warning("Task %s failed: %s", tid, exc)

        _save_mission(mission)

    xp = _XP_MAP.get(rank, 10) if all_ok else 0
    mission["xp_awarded"] = xp
    mission["status"] = "COMPLETED" if all_ok else "FAILED"
    mission["completed_at"] = _utc()
    _save_mission(mission)

    # Notify entity of XP gain
    if xp:
        try:
            from nexusmon.entity import get_entity
            get_entity().award_xp(xp)
        except Exception:
            pass

    # Award operator rank XP
    if all_ok:
        try:
            from nexusmon_operator_rank import award_xp as _rank_xp
            _rank_xp(f"complete_mission_{rank}", detail=mission_id)
        except Exception:
            pass

    return mission


def _execute_task(task: Dict, mission: Dict) -> Dict:
    """Execute a single task. Returns output dict."""
    task_type = task.get("type", "ANALYZE")
    description = task.get("description", "")

    try:
        from core.model_router import call as _llm_call
        result = _llm_call(
            messages=[{"role": "user", "content": description}],
            system=(
                f"You are executing a {task_type} task for mission: {mission.get('goal', '')}. "
                "Be concise and precise."
            ),
            max_tokens=500,
        )
        return {"text": result.get("text", ""), "ok": result.get("ok", False)}
    except Exception as exc:
        return {"text": f"Task executed (no AI): {description}", "ok": True, "note": str(exc)}


def get_mission(mission_id: str) -> Optional[Dict]:
    missions = _load_missions()
    return next((m for m in missions if m["id"] == mission_id), None)


def list_missions(
    status: Optional[str] = None,
    rank: Optional[str] = None,
    limit: int = 50,
) -> List[Dict]:
    missions = _load_missions()
    if status:
        missions = [m for m in missions if m.get("status") == status.upper()]
    if rank:
        missions = [m for m in missions if m.get("rank") == rank.upper()]
    return missions[-limit:]


def cancel_mission(mission_id: str) -> Dict:
    mission = get_mission(mission_id)
    if not mission:
        raise ValueError(f"Mission not found: {mission_id}")
    if mission["status"] in ("COMPLETED", "FAILED"):
        raise ValueError(f"Cannot cancel mission in state {mission['status']}")
    mission["status"] = "CANCELLED"
    mission["completed_at"] = _utc()
    _save_mission(mission)
    return mission


def mission_xp_total() -> int:
    return sum(m.get("xp_awarded", 0) for m in _load_missions())


# ══════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ══════════════════════════════════════════════════════════════

class MissionCreate(BaseModel):
    goal: str = Field(..., min_length=3)
    rank: str = Field("E", pattern="^[EDCBAS]$")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ══════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════

router = APIRouter(prefix="/v1/engine", tags=["mission-engine"])


@router.get("/missions/stats")
def get_stats():
    missions = _load_missions()
    total = len(missions)
    by_status: Dict[str, int] = {}
    by_rank: Dict[str, int] = {}
    total_xp = 0
    durations: List[float] = []

    for m in missions:
        s = m.get("status", "PENDING")
        by_status[s] = by_status.get(s, 0) + 1
        r = m.get("rank", "E")
        by_rank[r] = by_rank.get(r, 0) + 1
        total_xp += m.get("xp_awarded", 0)
        if m.get("started_at") and m.get("completed_at"):
            try:
                t0 = datetime.fromisoformat(m["started_at"].replace("Z", "+00:00"))
                t1 = datetime.fromisoformat(m["completed_at"].replace("Z", "+00:00"))
                durations.append((t1 - t0).total_seconds())
            except Exception:
                pass

    completed = by_status.get("COMPLETED", 0)
    completion_rate = round(completed / total * 100, 1) if total else 0.0
    avg_duration = round(sum(durations) / len(durations), 1) if durations else 0.0

    return {
        "ok": True,
        "total": total,
        "by_status": by_status,
        "by_rank": by_rank,
        "completion_rate_pct": completion_rate,
        "avg_duration_seconds": avg_duration,
        "total_xp": total_xp,
    }


@router.post("/missions")
def create_mission_endpoint(payload: MissionCreate):
    try:
        mission = create_mission(payload.goal, payload.rank, payload.metadata)
        return {"ok": True, "mission": mission}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/missions")
def list_missions_endpoint(status: Optional[str] = None, rank: Optional[str] = None, limit: int = 50):
    missions = list_missions(status=status, rank=rank, limit=limit)
    return {"ok": True, "missions": missions, "count": len(missions)}


@router.get("/missions/{mission_id}")
def get_mission_endpoint(mission_id: str):
    mission = get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return {"ok": True, "mission": mission}


@router.post("/missions/{mission_id}/approve")
def approve_mission_endpoint(mission_id: str):
    try:
        mission = approve_mission(mission_id)
        return {"ok": True, "mission": mission}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/missions/{mission_id}/run")
def run_mission_endpoint(mission_id: str):
    try:
        mission = run_mission(mission_id)
        return {"ok": True, "mission": mission}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/missions/{mission_id}")
def cancel_mission_endpoint(mission_id: str):
    try:
        mission = cancel_mission(mission_id)
        return {"ok": True, "mission": mission}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ══════════════════════════════════════════════════════════════
# FUSE
# ══════════════════════════════════════════════════════════════

def fuse_mission_engine(app: FastAPI) -> None:
    """Wire mission engine routes into the FastAPI app."""
    app.include_router(router)
    logger.info(
        "Mission engine fused. %d missions on disk. Total XP: %d",
        len(_load_missions()),
        mission_xp_total(),
    )
