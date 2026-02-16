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
    provenance.append_audit("factory_intake", {"mission_id": mission_id, "guild": guild})
    return row


def list_missions(limit: int = 200) -> List[Dict[str, Any]]:
    rows = _read_jsonl(FACTORY_FILE)
    return rows[-limit:]


def get_mission(mid: str) -> Dict[str, Any] | None:
    for m in _read_jsonl(FACTORY_FILE):
        if m.get("id") == mid:
            return m
    return None


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
    provenance.append_audit("decision_recorded", {"mission_id": mission_id, "decision_id": decision["decision_id"]})
    return decision


def latest_decision() -> Dict[str, Any] | None:
    decs = _read_jsonl(DECISIONS_FILE)
    return decs[-1] if decs else None


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
