# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import json
import time
from pathlib import Path
from typing import Dict, Any

from swarmz_runtime.verify import provenance

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
VERIFY_DIR = DATA_DIR / "verify"
VERIFY_DIR.mkdir(parents=True, exist_ok=True)


def _read_jsonl(path: Path) -> list:
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


def replay_audit(audit_path: Path | None = None) -> Dict[str, Any]:
    audit_path = audit_path or (DATA_DIR / "audit.jsonl")
    entries = _read_jsonl(audit_path)
    state = {
        "mission_ids": set(),
        "events": len(entries),
        "hash_ok": provenance.verify_chain(audit_path)[0],
    }
    for e in entries:
        mid = e.get("details", {}).get("mission_id") or e.get("mission_id")
        if mid:
            state["mission_ids"].add(mid)
    state["mission_ids"] = sorted(state["mission_ids"])
    state["mission_count"] = len(state["mission_ids"])
    state["events"] = len(entries)
    state["replay_hash"] = hash(json.dumps(entries, sort_keys=True))
    return state


def verify_invariants(data_dir: Path = DATA_DIR) -> Dict[str, Any]:
    missions = _read_jsonl(data_dir / "missions.jsonl")
    seen = set()
    dupes = []
    invalid_status = []
    for m in missions:
        mid = m.get("id") or m.get("mission_id")
        if not mid:
            continue
        if mid in seen:
            dupes.append(mid)
        seen.add(mid)
        status = (m.get("status") or "").lower()
        if status not in {"pending", "active", "completed", "failed", "offline"}:
            invalid_status.append(mid)
    return {
        "missions": len(missions),
        "duplicates": dupes,
        "invalid_status": invalid_status,
        "ok": not dupes and not invalid_status,
    }


def run_verify() -> Dict[str, Any]:
    started = time.time()
    replay_state = replay_audit()
    invariants = verify_invariants()
    chain_ok, chain_count = provenance.verify_chain()
    report = {
        "started": started,
        "duration_sec": round(time.time() - started, 3),
        "replay": replay_state,
        "invariants": invariants,
        "chain_ok": chain_ok,
        "chain_count": chain_count,
        "ok": chain_ok and invariants.get("ok", False),
    }
    ts = int(started)
    out_path = VERIFY_DIR / f"report-{ts}.json"
    out_path.write_text(json.dumps(report, indent=2))
    provenance.append_audit("verify_run", {"ok": report["ok"], "report": str(out_path)})
    return report


def run_status() -> Dict[str, Any]:
    chain_ok, count = provenance.verify_chain()
    latest_report = None
    reports = sorted(VERIFY_DIR.glob("report-*.json"))
    if reports:
        latest_report = reports[-1].name
    return {
        "chain_ok": chain_ok,
        "chain_entries": count,
        "latest_report": latest_report,
    }

