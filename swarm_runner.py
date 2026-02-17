# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
SWARMZ Swarm Runner â€” picks up PENDING missions and runs them.

Writes results to packs/<mission_id>/result.json (or error.json on failure).
Updates data/missions.jsonl with status (RUNNING -> SUCCESS|FAILURE).
Writes a heartbeat to data/runner_heartbeat.json every tick.
AI-eligible missions go through the mission solver for PLAN + PREPARED_ACTIONS.

Designed to run in a daemon thread or standalone process.
"""

import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from jsonl_utils import read_jsonl, write_jsonl

DATA_DIR = Path("data")
MISSIONS_FILE = DATA_DIR / "missions.jsonl"
AUDIT_FILE = DATA_DIR / "audit.jsonl"
HEARTBEAT_FILE = DATA_DIR / "runner_heartbeat.json"
PACKS_DIR = Path("packs")

TICK_INTERVAL = 1  # seconds


# â”€â”€ atomic-ish JSONL helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _rewrite_missions(missions):
    """Rewrite entire missions.jsonl from list (read-all, update, write-temp, replace)."""
    tmp = MISSIONS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for m in missions:
            f.write(json.dumps(m, separators=(",", ":")) + "\n")
    tmp.replace(MISSIONS_FILE)


def _audit(event: str, **kwargs):
    now = datetime.utcnow().isoformat() + "Z"
    entry = {"timestamp": now, "event": event}
    entry.update(kwargs)
    write_jsonl(AUDIT_FILE, entry)


def _write_heartbeat(status="up"):
    now = datetime.utcnow().isoformat() + "Z"
    hb = {"status": status, "last_tick": now}
    HEARTBEAT_FILE.write_text(json.dumps(hb), encoding="utf-8")


# â”€â”€ Stub workers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _worker_smoke(mission: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "type": "smoke"}


def _worker_test_mission(mission: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "note": "stub worker executed"}


def _worker_galileo_run(mission: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from galileo.runner import run as galileo_run
        return galileo_run(mission)
    except Exception:
        return {"ok": True, "note": "galileo stub (import unavailable)"}


def _worker_unknown(mission: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": False, "error": "unknown intent"}


def _worker_ai_solve(mission: Dict[str, Any]) -> Dict[str, Any]:
    """Route mission through the AI mission solver (safe, prepare-only)."""
    try:
        from core.mission_solver import solve
        result = solve(mission)
        return {
            "ok": result.get("ok", False),
            "type": "ai_solve",
            "source": result.get("source", "unknown"),
            "prepared_actions_dir": result.get("prepared_actions_dir", ""),
            "plan_preview": (result.get("plan", ""))[:500],
            "provider": result.get("provider"),
            "model": result.get("model"),
            "latencyMs": result.get("latencyMs"),
        }
    except Exception as exc:
        return {"ok": True, "type": "ai_solve", "source": "error_fallback",
                "note": f"Solver unavailable: {str(exc)[:120]}"}


# Categories that should go through AI solver when available
AI_ELIGIBLE_CATEGORIES = {"build", "solve", "plan", "analyze", "research"}

WORKERS = {
    "smoke": _worker_smoke,
    "test_mission": _worker_test_mission,
    "galileo_run": _worker_galileo_run,
    "ai_solve": _worker_ai_solve,
}


# â”€â”€ Core tick logic â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _process_one():
    """Find first PENDING mission, run it, write results."""
    missions, _, _ = read_jsonl(MISSIONS_FILE)

    # Check QUARANTINE â€” if active, block execution and log
    success_count = sum(1 for m in missions if m.get("status") == "SUCCESS")
    total = len(missions)
    if total >= 10:
        success_rate = success_count / total
        if success_rate < 0.3:
            # QUARANTINE active â€” skip execution
            pending = [m for m in missions if m.get("status") == "PENDING"]
            if pending:
                _audit("quarantine_blocked",
                       pending_count=len(pending),
                       total=total,
                       success_rate=round(success_rate, 3))
            return

    target = None
    for m in missions:
        if m.get("status") == "PENDING":
            target = m
            break
    if target is None:
        return  # nothing to do

    mission_id = target.get("mission_id", "unknown")
    intent = target.get("intent", target.get("goal", "unknown"))
    pack_dir = PACKS_DIR / mission_id
    pack_dir.mkdir(parents=True, exist_ok=True)

    # â”€â”€ Beforeâ€‘mission: gather context + select strategy â”€â”€
    pre_ctx = {}
    try:
        from core.context_pack import before_mission
        pre_ctx = before_mission(target)
    except Exception:
        pass
    strategy = pre_ctx.get("strategy", "baseline")
    inputs_hash = pre_ctx.get("inputs_hash", "")
    candidates = pre_ctx.get("candidates", [])

    # Mark RUNNING
    started_at = datetime.utcnow().isoformat() + "Z"
    target["status"] = "RUNNING"
    target["started_at"] = started_at
    _rewrite_missions(missions)
    _audit("mission_started", mission_id=mission_id, intent=intent, strategy=strategy)

    # Execute worker
    t0 = time.monotonic()
    try:
        worker_fn = WORKERS.get(intent, None)
        # Route AI-eligible missions through ai_solve if no explicit worker
        if worker_fn is None:
            category = target.get("category", "")
            if category in AI_ELIGIBLE_CATEGORIES or intent == "ai_solve":
                worker_fn = _worker_ai_solve
            else:
                worker_fn = _worker_unknown
        result = worker_fn(target)
        duration_ms = int((time.monotonic() - t0) * 1000)

        # Write result
        (pack_dir / "result.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )

        # Determine outcome
        if result.get("ok"):
            target["status"] = "SUCCESS"
        else:
            target["status"] = "FAILURE"

        target["finished_at"] = datetime.utcnow().isoformat() + "Z"
        target["duration_ms"] = duration_ms
        _rewrite_missions(missions)
        _audit(
            "mission_finished",
            mission_id=mission_id,
            outcome=target["status"],
            duration_ms=duration_ms,
        )

        # â”€â”€ Afterâ€‘mission: update ALL engines â”€â”€
        try:
            from core.context_pack import after_mission
            after_mission(
                target, result, duration_ms,
                strategy=strategy,
                inputs_hash=inputs_hash,
                candidates=candidates,
            )
        except Exception:
            pass  # engine updates are best-effort

    except Exception as exc:
        duration_ms = int((time.monotonic() - t0) * 1000)
        tb_tail = traceback.format_exc().splitlines()[-5:]

        # Write error
        (pack_dir / "error.json").write_text(
            json.dumps({"error": str(exc), "traceback": tb_tail}, indent=2),
            encoding="utf-8",
        )

        target["status"] = "FAILURE"
        target["finished_at"] = datetime.utcnow().isoformat() + "Z"
        target["duration_ms"] = duration_ms
        _rewrite_missions(missions)
        _audit(
            "mission_finished",
            mission_id=mission_id,
            outcome="FAILURE",
            duration_ms=duration_ms,
            error=str(exc),
        )


# â”€â”€ Main loop â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run_loop():
    """Infinite runner loop. Call from daemon thread or __main__."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PACKS_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        try:
            _write_heartbeat("up")
            _process_one()
        except Exception:
            # runner must not crash â€” swallow and continue
            pass
        time.sleep(TICK_INTERVAL)


if __name__ == "__main__":
    print("[SWARM RUNNER] Starting standalone runner loop...")
    run_loop()

