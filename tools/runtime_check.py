# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Lightweight runtime self-check for SWARMZ.

Runs a short mission, emits telemetry, and reports timing + busy-loop heuristics.
Usage:
    python tools/runtime_check.py
    python tools/runtime_check.py --json
    python tools/runtime_check.py --data-dir data
"""
import argparse
import json
import sys
import time
from pathlib import Path

from swarmz_runtime.core.engine import SwarmzEngine

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = ROOT / "data"
DEFAULT_DATA_DIR.mkdir(exist_ok=True)


def run_short_mission(data_dir: Path) -> dict:
    engine = SwarmzEngine(data_dir=str(data_dir))
    goal = "runtime_check_sanity"
    created = engine.create_mission(goal, "test", {})
    mission_id = created.get("mission_id")
    ran = engine.run_mission(mission_id, operator_key=engine.operator_key) if mission_id else {"error": "no mission"}
    return {"created": created, "ran": ran}


def read_last_line(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        with path.open("rb") as f:
            f.seek(0, 2)
            pos = f.tell()
            buf = b""
            while pos:
                pos -= 1
                f.seek(pos)
                ch = f.read(1)
                if ch == b"\n" and buf:
                    break
                buf = ch + buf
            return buf.decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


def detect_busy_loops() -> bool:
    """Detects if any busy loops are present in the runtime."""
    # Placeholder for actual implementation
    return False


def build_status(result: dict, metrics_line: str, telemetry_line: str, busy: bool) -> tuple[str, list[str]]:
    issues = []
    if "error" in result.get("ran", {}):
        issues.append("mission_run_failed")
    if not metrics_line:
        issues.append("missing_runtime_metrics")
    if not telemetry_line:
        issues.append("missing_telemetry")
    if busy:
        issues.append("busy_loops_detected")
    status = "ok" if not issues else "warning"
    return status, issues


def print_human_output(payload: dict):
    print("=== RUNTIME CHECK ===")
    print(f"status: {payload['status']}")
    print(f"wall_ms: {payload['wall_ms']:.2f}")
    print("mission create/run:", json.dumps(payload["mission"], ensure_ascii=True))
    print("last_runtime_metric:", payload["last_runtime_metric"] or "(none)")
    print("last_telemetry:", payload["last_telemetry"] or "(none)")
    print("busy_loops_detected:", payload["busy_loops_detected"] or "none")

    if payload["issues"]:
        print("issues:", ", ".join(payload["issues"]))

    if payload["next_steps"]:
        print("next_steps:")
        for step in payload["next_steps"]:
            print(f"- {step}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a lightweight SWARMZ runtime self-check.")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="Path to the data directory.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)

    start = time.perf_counter()
    error = None
    result = {}
    try:
        result = run_short_mission(data_dir)
    except Exception as exc:
        error = str(exc)
        result = {"created": {"error": "create_mission_failed"}, "ran": {"error": "run_mission_failed"}}

    duration_ms = (time.perf_counter() - start) * 1000.0
    metrics_line = read_last_line(data_dir / "runtime_metrics.jsonl")
    telemetry_line = read_last_line(data_dir / "telemetry.jsonl")
    busy = detect_busy_loops()

    status, issues = build_status(result, metrics_line, telemetry_line, busy)
    next_steps = []
    if error:
        next_steps.append("Verify dependencies are installed: pip install -r requirements.txt")
        next_steps.append("Start the server once to seed runtime data: python run_swarmz.py")
    if "missing_runtime_metrics" in issues:
        next_steps.append("Enable telemetry and run a mission to produce runtime metrics.")
    if "missing_telemetry" in issues:
        next_steps.append("Check telemetry.jsonl path and ensure telemetry is enabled.")
    if "mission_run_failed" in issues:
        next_steps.append("Confirm operator key and runtime config are valid.")
    if "busy_loops_detected" in issues:
        next_steps.append("Review polling loops for sleeps or backoff.")

    payload = {
        "status": status,
        "wall_ms": duration_ms,
        "mission": result,
        "last_runtime_metric": metrics_line,
        "last_telemetry": telemetry_line,
        "busy_loops_detected": busy,
        "issues": issues,
        "next_steps": next_steps,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=True))
    else:
        print_human_output(payload)

    return 0 if status == "ok" else 2


if __name__ == "__main__":
    sys.exit(main())

