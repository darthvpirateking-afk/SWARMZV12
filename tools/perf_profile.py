#!/usr/bin/env python3
# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Performance Profiler — hot-path benchmarking tool.

Profiles the core hot-path functions:
  • core.trials  — load_all_trials, get_trial, inbox_counts
  • core.hologram — compute_power_currencies, compute_level

Usage:
    python tools/perf_profile.py [--count N] [--output {text,json}]

Outputs timing statistics (mean, p50, p95, p99) in either
human-readable text or machine-readable JSON.
"""

import argparse
import json
import os
import sys
import time
import statistics
import tempfile
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _make_fake_trials(n: int, tmp_dir: Path) -> None:
    """Write n fake trial records into a temporary data directory."""
    import uuid
    from datetime import datetime, timezone, timedelta

    trials_dir = tmp_dir / "trials"
    trials_dir.mkdir(parents=True, exist_ok=True)
    trials_file = trials_dir / "trials.jsonl"
    now = datetime.now(timezone.utc)
    with trials_file.open("w", encoding="utf-8") as f:
        for i in range(n):
            checked = now - timedelta(days=i % 60)
            record = {
                "id": str(uuid.uuid4()),
                "created_at": (now - timedelta(days=i)).isoformat(),
                "created_by": "perf_test",
                "context": f"ctx_{i % 5}",
                "action": f"action_{i % 10}: step",
                "metric_name": f"metric_{i % 3}",
                "metric_before": 0.5,
                "expected_delta": 0.1,
                "check_after_sec": 300,
                "check_at": checked.isoformat(),
                "checked_at": checked.isoformat(),
                "metric_after": 0.6,
                "survived": (i % 3 != 0),
                "reverted": (i % 7 == 0),
                "notes": None,
                "tags": [f"tag_{i % 4}"],
                "evidence": {},
                "baseline_evidence": None,
            }
            f.write(json.dumps(record) + "\n")


def _timeit(fn, count: int) -> list[float]:
    """Run fn() count times and return list of elapsed seconds."""
    times = []
    for _ in range(count):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return times


def _stats(times: list[float]) -> dict:
    s = sorted(times)
    n = len(s)
    return {
        "count": n,
        "mean_ms": round(statistics.mean(s) * 1000, 3),
        "median_ms": round(statistics.median(s) * 1000, 3),
        "p95_ms": round(s[int(n * 0.95)] * 1000, 3),
        "p99_ms": round(s[int(n * 0.99)] * 1000, 3),
        "min_ms": round(s[0] * 1000, 3),
        "max_ms": round(s[-1] * 1000, 3),
    }


def run_profile(trial_count: int = 500, repeat: int = 50, output: str = "text") -> None:
    with tempfile.TemporaryDirectory(prefix="swarmz_perf_") as tmp:
        tmp_path = Path(tmp)
        _make_fake_trials(trial_count, tmp_path)

        # Patch data dirs before importing core modules
        import core.trials as trials_mod
        import core.hologram as holo_mod

        orig_trials_file = trials_mod._TRIALS_FILE
        orig_holo_dir = holo_mod._HOLO_DIR
        orig_holo_state = holo_mod._STATE_FILE

        try:
            trials_mod._TRIALS_FILE = tmp_path / "trials" / "trials.jsonl"
            holo_mod._HOLO_DIR = tmp_path / "hologram"
            holo_mod._HOLO_DIR.mkdir(parents=True, exist_ok=True)
            holo_mod._STATE_FILE = holo_mod._HOLO_DIR / "holo_state.json"

            results = {}

            results["load_all_trials"] = _stats(
                _timeit(trials_mod.load_all_trials, repeat)
            )
            results["inbox_counts"] = _stats(
                _timeit(trials_mod.inbox_counts, repeat)
            )
            results["compute_power_currencies"] = _stats(
                _timeit(holo_mod.compute_power_currencies, repeat)
            )
            results["compute_level"] = _stats(
                _timeit(holo_mod.compute_level, repeat)
            )

            # get_trial: look up a known ID
            all_t = trials_mod.load_all_trials()
            if all_t:
                tid = all_t[len(all_t) // 2]["id"]
                results["get_trial"] = _stats(
                    _timeit(lambda: trials_mod.get_trial(tid), repeat)
                )

        finally:
            trials_mod._TRIALS_FILE = orig_trials_file
            holo_mod._HOLO_DIR = orig_holo_dir
            holo_mod._STATE_FILE = orig_holo_state

    if output == "json":
        print(json.dumps({"trial_count": trial_count, "repeat": repeat, "results": results}, indent=2))
    else:
        print(f"\nSWARMZ Performance Profile  —  {trial_count} trials × {repeat} runs\n")
        print(f"{'Function':<30} {'mean':>8} {'p50':>8} {'p95':>8} {'p99':>8}  (ms)")
        print("-" * 70)
        for fn, st in results.items():
            print(
                f"{fn:<30} {st['mean_ms']:>8.2f} {st['median_ms']:>8.2f}"
                f" {st['p95_ms']:>8.2f} {st['p99_ms']:>8.2f}"
            )
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SWARMZ performance profiler")
    parser.add_argument("--count", type=int, default=500, help="Number of fake trials to generate")
    parser.add_argument("--repeat", type=int, default=50, help="Number of timing runs per function")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()
    run_profile(trial_count=args.count, repeat=args.repeat, output=args.output)
