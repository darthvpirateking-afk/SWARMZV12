import json
import time
from pathlib import Path
from typing import Dict, Any, Callable

from swarmz_runtime.verify import runner, provenance

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SCHED_FILE = DATA_DIR / "scheduler.json"
RUNS_FILE = DATA_DIR / "scheduler_runs.jsonl"

TASKS: Dict[str, Callable[[], Dict[str, Any]]] = {
    "verify_pending_missions": runner.run_verify,
    "replay_check": runner.replay_audit,
    "perf_snapshot": lambda: {"ok": True, "note": "placeholder"},
}


def _load_state() -> Dict[str, Any]:
    if SCHED_FILE.exists():
        try:
            return json.loads(SCHED_FILE.read_text())
        except Exception:
            pass
    state = {"interval_sec": 30, "last_run": 0, "paused": False}
    SCHED_FILE.write_text(json.dumps(state, indent=2))
    return state


def _save_state(state: Dict[str, Any]):
    SCHED_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCHED_FILE.write_text(json.dumps(state, indent=2))


def _append_run(task: str, result: Dict[str, Any]):
    RUNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": time.time(),
        "task": task,
        "result": result,
    }
    with RUNS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")
    provenance.append_audit("scheduler_run", {"task": task, "ok": result.get("ok", True)})


def tick(now: float | None = None):
    now = now or time.time()
    state = _load_state()
    if state.get("paused"):
        return {"skipped": True, "reason": "paused"}
    interval = state.get("interval_sec", 30)
    if now - state.get("last_run", 0) < interval:
        return {"skipped": True, "reason": "interval"}
    results = {}
    for name, fn in TASKS.items():
        try:
            results[name] = fn()
        except Exception as exc:
            results[name] = {"ok": False, "error": str(exc)}
        _append_run(name, results[name])
    state["last_run"] = now
    _save_state(state)
    return {"ran": list(results.keys()), "results": results}


def pause():
    st = _load_state()
    st["paused"] = True
    _save_state(st)
    provenance.append_audit("scheduler_paused", {})


def resume():
    st = _load_state()
    st["paused"] = False
    _save_state(st)
    provenance.append_audit("scheduler_resumed", {})
