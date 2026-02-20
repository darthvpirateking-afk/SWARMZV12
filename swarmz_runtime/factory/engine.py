# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import json
import secrets
import time
from pathlib import Path
from typing import Dict, Any, List

from swarmz_runtime.verify import provenance

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
FACTORY_FILE = DATA_DIR / "factory_missions.jsonl"
DECISIONS_FILE = DATA_DIR / "decisions.jsonl"

GUILDS = ["runtime", "governance", "research", "build", "revenue", "verify"]


def _append(path: Path, row: Dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    return rows


def intake(mission: Dict[str, Any]) -> Dict[str, Any]:
    mission_id = mission.get("id") or f"F-{int(time.time())}-{secrets.token_hex(3)}"
    guild = mission.get("guild") or (GUILDS[hash(mission_id) % len(GUILDS)])
    row = {
        "id": mission_id,
        "created_at": time.time(),
        "intent": mission.get("intent") or mission.get("goal") or "unspecified",
        "domain": mission.get("domain") or "general",
        "input": mission.get("input") or mission.get("scope") or {},
        "constraints": mission.get("constraints") or {},
        "routing": guild,
        "status": "intake",
        "cost": mission.get("cost", 0),
        "artifacts": mission.get("artifacts") or [],
        "verify_ref": None,
        "audit_ref": None,
    }
    _append(FACTORY_FILE, row)
    provenance.append_audit(
        "factory_intake", {"mission_id": mission_id, "guild": guild}
    )
    return row


def list_missions(limit: int = 200) -> List[Dict[str, Any]]:
    rows = _read_jsonl(FACTORY_FILE)
    return rows[-limit:]


def get_mission(mid: str) -> Dict[str, Any]:
    for m in rows:
        if m["id"] == mid:
            return m
    return {}  # Replace None with an empty dictionary


def record_decision(mission_id: str, chosen: str, reason: str = "") -> Dict[str, Any]:
    decision = {
        "decision_id": f"D-{int(time.time())}-{secrets.token_hex(2)}",
        "mission_id": mission_id,
        "options_hash": hash(mission_id),
        "chosen": chosen,
        "reason": reason,
        "score": 1.0,
        "operator_override": False,
        "ts": time.time(),
    }
    _append(DECISIONS_FILE, decision)
    provenance.append_audit(
        "decision_recorded",
        {"mission_id": mission_id, "decision_id": decision["decision_id"]},
    )
    return decision


def latest_decision() -> Dict[str, Any]:
    return decs[-1] if decs else {}  # Replace None with an empty dictionary


def mermaid_graph() -> str:
    missions = list_missions()
    lines = ["graph TD"]
    for m in missions:
        mid = m.get("id")
        guild = m.get("routing")
        lines.append(f"  {mid}[Mission {mid}] --> {guild}")
        lines.append(f"  {guild}[Guild {guild}] --> verify_{mid}")
        lines.append(f"  verify_{mid}[Verify {mid}] --> close_{mid}")
    return "\n".join(lines)


def execute_artifact(
    artifact_id: str,
    parameters: Dict[str, Any],
    operator_key: str,
    safe_mode: bool = True,
) -> Dict[str, Any]:
    """Execute an artifact with manifestation and safety checks."""
    # Find the artifact/mission
    mission = get_mission(artifact_id)
    if not mission:
        raise ValueError(f"Artifact {artifact_id} not found")

    # Safety checks for irreversible propagation
    if not safe_mode and mission.get("status") != "verified":
        raise ValueError("Artifact not verified for unsafe execution")

    # Validate operator sovereignty (would integrate with main engine)
    # For now, basic check
    if not operator_key:
        raise ValueError("Operator key required for artifact execution")

    # Execute based on guild/routing
    guild = mission.get("routing", "runtime")

    execution_result = {
        "artifact_id": artifact_id,
        "guild": guild,
        "status": "executing",
        "safe_mode": safe_mode,
        "parameters": parameters,
        "operator_key": operator_key[:8] + "...",  # Mask for security
        "timestamp": time.time(),
    }

    # Simulate execution based on guild
    if guild == "runtime":
        execution_result.update(
            {"action": "runtime_update", "result": "Runtime configuration updated"}
        )
    elif guild == "governance":
        execution_result.update(
            {"action": "policy_update", "result": "Governance policy applied"}
        )
    elif guild == "research":
        execution_result.update(
            {"action": "research_execution", "result": "Research artifact executed"}
        )
    elif guild == "build":
        execution_result.update(
            {"action": "build_execution", "result": "Build artifact deployed"}
        )
    elif guild == "revenue":
        execution_result.update(
            {"action": "revenue_optimization", "result": "Revenue optimization applied"}
        )
    elif guild == "verify":
        execution_result.update(
            {"action": "verification_run", "result": "Verification completed"}
        )
    else:
        execution_result.update(
            {
                "action": "generic_execution",
                "result": f"Artifact executed in {guild} guild",
            }
        )

    # Record execution
    execution_log = {
        "artifact_id": artifact_id,
        "execution_id": f"exec_{int(time.time())}_{secrets.token_hex(4)}",
        "timestamp": time.time(),
        "operator_key": operator_key[:8] + "...",
        "safe_mode": safe_mode,
        "result": execution_result,
    }

    _append(DATA_DIR / "artifact_executions.jsonl", execution_log)

    # Update mission status
    mission["status"] = "executed"
    mission["last_execution"] = time.time()
    _update_mission(artifact_id, mission)

    provenance.append_audit(
        "artifact_executed",
        {
            "artifact_id": artifact_id,
            "execution_id": execution_log["execution_id"],
            "guild": guild,
            "safe_mode": safe_mode,
        },
    )

    execution_result["execution_id"] = execution_log["execution_id"]
    execution_result["status"] = "completed"

    return execution_result


def _update_mission(mission_id: str, updated_mission: Dict[str, Any]):
    """Update a mission in the factory file."""
    missions = _read_jsonl(FACTORY_FILE)
    for i, m in enumerate(missions):
        if m.get("id") == mission_id:
            missions[i] = updated_mission
            break

    # Rewrite the file
    FACTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with FACTORY_FILE.open("w", encoding="utf-8") as f:
        for m in missions:
            f.write(json.dumps(m, separators=(",", ":")) + "\n")
