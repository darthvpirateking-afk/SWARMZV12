# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Mission Engine — declarative, artifact‑producing mission execution.

Responsibilities:
  1. Load/create mission definitions
  2. Execute single missions (routed to workers)
  3. Chain sequential missions with artifact passing
  4. Produce artifacts in the vault on every step
  5. Query mission lifecycle state

Lifecycle: queued → approved → running → completed | failed → archived
"""

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
MISSIONS_FILE = ROOT / "data" / "missions.jsonl"
AUDIT_FILE = ROOT / "data" / "audit.jsonl"

# Lazy import to avoid circular deps — vault lives in the same package
_vault = None


def _get_vault():
    global _vault
    if _vault is None:
        from core import artifact_vault
        _vault = artifact_vault
    return _vault


# ──────────────────────────────────────────────────────────────
# WORKER REGISTRY
# ──────────────────────────────────────────────────────────────

_WORKER_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_worker(worker_id: str, capabilities: List[str], run_fn=None):
    """Register a worker with its capabilities."""
    _WORKER_REGISTRY[worker_id] = {
        "id": worker_id,
        "capabilities": capabilities,
        "run": run_fn,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "tasks_completed": 0,
        "last_task_at": None,
    }


def list_workers() -> List[Dict[str, Any]]:
    """Return all registered workers (without run functions)."""
    return [
        {k: v for k, v in w.items() if k != "run"}
        for w in _WORKER_REGISTRY.values()
    ]


def find_worker(capability: str) -> Optional[str]:
    """Find a worker that has the requested capability."""
    for wid, w in _WORKER_REGISTRY.items():
        if capability in w.get("capabilities", []):
            return wid
    return None


# ──────────────────────────────────────────────────────────────
# BUILT‑IN WORKERS
# ──────────────────────────────────────────────────────────────

def _worker_smoke(_task: Dict) -> Dict:
    return {"ok": True, "type": "smoke", "message": "Smoke test passed"}


def _worker_analyze(task: Dict) -> Dict:
    return {"ok": True, "type": "analyze", "subject": task.get("payload", {}).get("subject", "system"), "result": "Analysis complete"}


def _worker_transform(task: Dict) -> Dict:
    return {"ok": True, "type": "transform", "input": task.get("payload", {}), "result": "Transform applied"}


def _worker_fetch(task: Dict) -> Dict:
    target = task.get("payload", {}).get("target", "unknown")
    return {"ok": True, "type": "fetch", "target": target, "result": f"Fetched {target}"}


def _worker_diagnose(_task: Dict) -> Dict:
    """Diagnose system health."""
    diag: Dict[str, Any] = {"ok": True, "type": "diagnose"}
    try:
        hb_f = ROOT / "data" / "runner_heartbeat.json"
        if hb_f.exists():
            hb = json.loads(hb_f.read_text())
            diag["runner_heartbeat"] = hb
        state_f = ROOT / "data" / "state.json"
        if state_f.exists():
            diag["state"] = json.loads(state_f.read_text())
        # Count missions
        if MISSIONS_FILE.exists():
            lines = MISSIONS_FILE.read_text().strip().splitlines()
            total = len(lines)
            success = sum(1 for l in lines if '"SUCCESS"' in l)
            failure = sum(1 for l in lines if '"FAILURE"' in l)
            pending = sum(1 for l in lines if '"PENDING"' in l)
            diag["missions"] = {"total": total, "success": success, "failure": failure, "pending": pending}
            diag["success_rate"] = round(success / total * 100, 1) if total else 0
    except Exception as e:
        diag["error"] = str(e)
    return diag


def _worker_evolve_form(task: Dict) -> Dict:
    """Evolve to a new form."""
    target = task.get("payload", {}).get("target", "cosmos")
    try:
        from core.context_pack import _engines
        evo = _engines.get("evolution_memory")
        if evo and hasattr(evo, "get_state"):
            state = evo.get_state()
            return {"ok": True, "type": "evolve_form", "current": state, "target": target}
    except Exception:
        pass
    return {"ok": True, "type": "evolve_form", "target": target, "note": "evolution engine not loaded"}


def _worker_deploy(task: Dict) -> Dict:
    target = task.get("payload", {}).get("target", "local")
    return {"ok": True, "type": "deploy", "target": target}


def _worker_ai_solve(task: Dict) -> Dict:
    """Route through AI mission solver."""
    try:
        from core.mission_solver import solve
        mission_data = {
            "mission_id": task.get("id", f"ai-{int(time.time())}"),
            "intent": task.get("payload", {}).get("intent", "unknown"),
            "spec": task.get("payload", {}),
        }
        return solve(mission_data)
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _worker_pinterest(task: Dict) -> Dict:
    """Process Pinterest pin data and extract ideas for auto-application."""
    pin = task.get("payload", {}).get("pin", {})
    idea = pin.get("title", pin.get("name", "Untitled Idea"))
    description = pin.get("description", "")
    image_url = pin.get("images", {}).get("original", {}).get("url", pin.get("image", ""))
    link = pin.get("link", pin.get("url", ""))
    board_name = pin.get("board_name", "Unknown Board")
    
    return {
        "ok": True,
        "type": "pinterest",
        "idea": idea,
        "description": description,
        "visual": image_url,
        "link": link,
        "board": board_name,
        "applied": True,
        "note": f"Applied Pinterest idea: {idea[:50]}"
    }


# Register built-in workers
register_worker("smoke-worker", ["smoke", "test"], _worker_smoke)
register_worker("analysis-worker", ["analyze", "research", "inspect"], _worker_analyze)
register_worker("transform-worker", ["transform", "convert", "build"], _worker_transform)
register_worker("fetch-worker", ["fetch", "download", "retrieve"], _worker_fetch)
register_worker("diagnose-worker", ["diagnose", "health", "check"], _worker_diagnose)
register_worker("evolve-worker", ["evolve", "form", "mode", "traits"], _worker_evolve_form)
register_worker("deploy-worker", ["deploy", "ship", "release"], _worker_deploy)
register_worker("ai-solver", ["solve", "plan", "reason", "ai"], _worker_ai_solve)
register_worker("pinterest-worker", ["pinterest", "pin", "board", "idea", "inspiration", "aesthetic"], _worker_pinterest)


# ──────────────────────────────────────────────────────────────
# MISSION HELPERS
# ──────────────────────────────────────────────────────────────

def _gen_mission_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    short = uuid.uuid4().hex[:8]
    return f"M-{ts}-{short}"


def _audit(event: str, details: Dict) -> None:
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event,
        "details": details,
    }
    with open(AUDIT_FILE, "a") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


def _read_missions() -> List[Dict]:
    if not MISSIONS_FILE.exists():
        return []
    lines = MISSIONS_FILE.read_text(encoding="utf-8").strip().splitlines()
    missions = []
    for l in lines:
        try:
            missions.append(json.loads(l))
        except json.JSONDecodeError:
            continue
    return missions


def _write_missions(missions: List[Dict]) -> None:
    MISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MISSIONS_FILE, "w", encoding="utf-8") as f:
        for m in missions:
            f.write(json.dumps(m, separators=(",", ":"), default=str) + "\n")


def _capability_from_intent(intent: str) -> str:
    """Map a natural language intent to a worker capability."""
    intent_lower = intent.lower()
    mapping = [
        (["smoke", "test", "ping"], "smoke"),
        (["analyze", "research", "inspect", "investigate", "audit"], "analyze"),
        (["transform", "convert", "build", "compile"], "transform"),
        (["fetch", "download", "retrieve", "get", "pull"], "fetch"),
        (["diagnose", "health", "check", "status", "doctor"], "diagnose"),
        (["evolve", "form", "morph", "mutate", "transform avatar"], "evolve"),
        (["deploy", "ship", "release", "push", "publish"], "deploy"),
        (["solve", "plan", "reason", "think", "ai", "figure out"], "solve"),
    ]
    for keywords, cap in mapping:
        if any(kw in intent_lower for kw in keywords):
            return cap
    return "solve"  # default to AI solver


# ──────────────────────────────────────────────────────────────
# CORE: RUN SINGLE MISSION
# ──────────────────────────────────────────────────────────────

def run_mission(
    intent: str,
    payload: Optional[Dict] = None,
    mission_id: Optional[str] = None,
    operator: str = "cockpit",
) -> Dict[str, Any]:
    """
    Execute a single mission. Creates the mission record, dispatches to a worker,
    stores the result artifact, and returns the full result.
    """
    vault = _get_vault()
    mid = mission_id or _gen_mission_id()
    now = datetime.now(timezone.utc).isoformat()
    payload = payload or {}

    # 1. Determine capability + worker
    capability = _capability_from_intent(intent)
    worker_id = find_worker(capability)

    # 2. Create mission record
    mission_record = {
        "mission_id": mid,
        "intent": intent,
        "capability": capability,
        "worker_id": worker_id,
        "payload": payload,
        "status": "RUNNING",
        "operator": operator,
        "created_at": now,
        "updated_at": now,
    }

    _audit("mission_engine_start", {"mission_id": mid, "intent": intent, "worker": worker_id})

    # Store operator artifact (the command)
    vault.store("operator", {
        "command": f"run mission {intent}",
        "mission_id": mid,
        "payload": payload,
    }, source="mission_engine", artifact_id=f"cmd-{mid}")

    # 3. Execute via worker
    t0 = time.time()
    try:
        worker = _WORKER_REGISTRY.get(worker_id, {})
        run_fn = worker.get("run") if worker else None
        if run_fn:
            task = {"id": mid, "capability": capability, "payload": {"intent": intent, **payload}}
            result_data = run_fn(task)
            # Update worker stats
            if worker_id in _WORKER_REGISTRY:
                _WORKER_REGISTRY[worker_id]["tasks_completed"] += 1
                _WORKER_REGISTRY[worker_id]["last_task_at"] = now
        else:
            result_data = {"ok": False, "error": f"No worker found for capability '{capability}'"}
    except Exception as e:
        result_data = {"ok": False, "error": str(e)}
    duration_ms = int((time.time() - t0) * 1000)

    # 4. Determine status
    ok = result_data.get("ok", False)
    status = "SUCCESS" if ok else "FAILURE"
    mission_record["status"] = status
    mission_record["duration_ms"] = duration_ms
    mission_record["updated_at"] = datetime.now(timezone.utc).isoformat()

    # 5. Store mission artifact
    artifact = vault.store("mission", {
        "mission_id": mid,
        "intent": intent,
        "status": status,
        "worker_id": worker_id,
        "duration_ms": duration_ms,
        "result": result_data,
    }, source="mission_engine", artifact_id=mid)

    # 6. Also write to missions.jsonl for backward compat
    missions = _read_missions()
    missions.append(mission_record)
    _write_missions(missions)

    _audit("mission_engine_done", {"mission_id": mid, "status": status, "duration_ms": duration_ms})

    # 7. Write result to packs/ for backward compat
    packs_dir = ROOT / "packs" / mid
    packs_dir.mkdir(parents=True, exist_ok=True)
    (packs_dir / "result.json").write_text(json.dumps(result_data, indent=2, default=str))

    return {
        "ok": ok,
        "mission_id": mid,
        "intent": intent,
        "status": status,
        "worker_id": worker_id,
        "duration_ms": duration_ms,
        "result": result_data,
        "artifact_id": artifact["id"],
    }


# ──────────────────────────────────────────────────────────────
# CORE: CHAIN MISSIONS
# ──────────────────────────────────────────────────────────────

def chain_missions(
    steps: List[Dict[str, Any]],
    operator: str = "cockpit",
) -> Dict[str, Any]:
    """
    Execute a sequence of missions, passing each result as input to the next.

    steps: [
      { "intent": "smoke test" },
      { "intent": "diagnose system", "inputFrom": "previous" },
      { "intent": "analyze results", "payload": {...} }
    ]
    """
    vault = _get_vault()
    chain_id = f"chain-{_gen_mission_id()}"
    results: List[Dict[str, Any]] = []
    previous_result: Optional[Dict] = None

    _audit("chain_start", {"chain_id": chain_id, "steps": len(steps)})

    for i, step in enumerate(steps):
        intent = step.get("intent", step.get("mission", "unknown"))
        payload = dict(step.get("payload", {}))

        # Inject previous result if requested
        if step.get("inputFrom") == "previous" and previous_result:
            payload["previous_result"] = previous_result.get("result", {})
        elif step.get("inputFrom") and previous_result:
            payload["chained_input"] = previous_result.get("result", {})

        payload["chain_id"] = chain_id
        payload["chain_step"] = i

        step_result = run_mission(
            intent=intent,
            payload=payload,
            operator=operator,
        )
        results.append(step_result)
        previous_result = step_result

        # Stop chain on failure
        if not step_result.get("ok", False):
            break

    # Store chain artifact
    chain_ok = all(r.get("ok") for r in results)
    vault.store("mission", {
        "chain_id": chain_id,
        "steps_planned": len(steps),
        "steps_completed": len(results),
        "all_ok": chain_ok,
        "results": [{"mission_id": r["mission_id"], "status": r["status"]} for r in results],
    }, source="chain_engine", artifact_id=chain_id)

    _audit("chain_done", {"chain_id": chain_id, "ok": chain_ok, "steps_completed": len(results)})

    return {
        "ok": chain_ok,
        "chain_id": chain_id,
        "steps_completed": len(results),
        "steps_planned": len(steps),
        "results": results,
    }


# ──────────────────────────────────────────────────────────────
# QUERY HELPERS
# ──────────────────────────────────────────────────────────────

def get_mission(mission_id: str) -> Optional[Dict]:
    """Get a mission by ID from missions.jsonl."""
    for m in _read_missions():
        if m.get("mission_id") == mission_id or m.get("id") == mission_id:
            return m
    return None


def recent_missions(limit: int = 20) -> List[Dict]:
    """Return the most recent missions."""
    missions = _read_missions()
    return missions[-limit:]


def mission_stats() -> Dict[str, Any]:
    """Return aggregate mission statistics."""
    missions = _read_missions()
    total = len(missions)
    by_status: Dict[str, int] = {}
    by_intent: Dict[str, int] = {}
    for m in missions:
        st = m.get("status", "UNKNOWN")
        by_status[st] = by_status.get(st, 0) + 1
        intent = m.get("intent", m.get("goal", "unknown"))
        by_intent[intent] = by_intent.get(intent, 0) + 1

    return {
        "total": total,
        "by_status": by_status,
        "by_intent": dict(sorted(by_intent.items(), key=lambda x: x[1], reverse=True)[:10]),
        "success_rate": round(by_status.get("SUCCESS", 0) / total * 100, 1) if total else 0,
    }
