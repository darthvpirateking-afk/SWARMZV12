# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Lightweight runtime self-check for SWARMZ.

Runs a short mission, emits telemetry, and reports timing + busy-loop heuristics.
Usage:
    python tools/runtime_check.py
"""

import json
import re
import time
from pathlib import Path

from swarmz_runtime.core.engine import SwarmzEngine

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def run_short_mission() -> dict:
    engine = SwarmzEngine(data_dir=str(DATA_DIR))
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


def detect_busy_loops() -> list:
    alerts = []
    for path in (ROOT / "swarmz_runtime" / "core").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"while True", text):
            window = text[m.start() : m.start() + 200]
            if "sleep" not in window:
                alerts.append(f"Potential busy loop in {path.relative_to(ROOT)}")
    return alerts


def main():
    start = time.perf_counter()
    result = run_short_mission()
    duration_ms = (time.perf_counter() - start) * 1000.0

    metrics_line = read_last_line(DATA_DIR / "runtime_metrics.jsonl")
    telemetry_line = read_last_line(DATA_DIR / "telemetry.jsonl")
    busy = detect_busy_loops()

    print("=== RUNTIME CHECK ===")
    print("mission create/run:", json.dumps(result))
    print(f"wall_ms: {duration_ms:.2f}")
    print("last_runtime_metric:", metrics_line)
    print("last_telemetry:", telemetry_line)
    print("busy_loops_detected:", busy or "none")


if __name__ == "__main__":
    main()

