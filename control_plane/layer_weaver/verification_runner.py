#!/usr/bin/env python3
"""
verification_runner.py – Post-action verification with automatic rollback.

Listens for ACTION_SELECTED events (via the bus internal queue).
On ACTION_SELECTED:
  1. Capture baseline metric value from latest state
  2. Schedule verification at deadline
  3. At deadline: read latest metric, compute delta
  4. Evaluate using verification.op and verification.target_delta
  5. Emit VERIFY_PASSED or VERIFY_FAILED
  6. On failure: trigger rollback (action_ref, instruction, or none)
  7. Log everything to verification_log.jsonl

Usage:
    python -m control_plane.layer_weaver.verification_runner
    python -m control_plane.layer_weaver.verification_runner --loop
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_DIR = os.path.dirname(os.path.abspath(__file__))
_ACTIONS_PATH = os.path.join(_DIR, "data", "actions.json")

from .event_debouncer import EventDebouncer
from .state_store import StateStore
from .verification_store import VerificationStore
from .expression_eval import evaluate_comparison


def _load_actions() -> Dict[str, dict]:
    """Load actions catalog keyed by id."""
    with open(_ACTIONS_PATH) as f:
        actions = json.load(f)
    return {a["id"]: a for a in actions}


def _deadline_seconds(deadline: dict) -> float:
    """Convert deadline spec to seconds."""
    t = deadline.get("type", "seconds")
    v = deadline.get("value", 60)
    multipliers = {
        "seconds": 1, "minutes": 60, "hours": 3600,
        "days": 86400, "weeks": 604800,
    }
    return v * multipliers.get(t, 1)


class VerificationRunner:
    """Verifies executed actions and triggers rollback on failure."""

    def __init__(self, state_store: StateStore,
                 vstore: VerificationStore,
                 bus: EventDebouncer,
                 config_hash_fn=None):
        self._state = state_store
        self._vstore = vstore
        self._bus = bus
        self._config_hash_fn = config_hash_fn or (lambda: "unknown")
        self._pending: List[dict] = []
        self._actions_by_id: Dict[str, dict] = _load_actions()

        # Subscribe to ACTION_SELECTED events
        bus.subscribe("ACTION_SELECTED", self._on_action_selected)

    def _on_action_selected(self, _event: str, payload: dict):
        """Record action for later verification."""
        if payload is None:
            return
        action = payload.get("action")
        if not action:
            return
        vspec = action.get("verification")
        if not vspec:
            return

        metric = vspec["metric"]
        baseline = self._state.get_latest_value(metric)
        deadline_secs = _deadline_seconds(vspec.get("deadline", {"type": "seconds", "value": 60}))

        item = {
            "action": action,
            "action_id": action["id"],
            "baseline": baseline,
            "metric": metric,
            "queued_at": time.monotonic(),
            "deadline_secs": deadline_secs,
            "config_hash": payload.get("config_hash", self._config_hash_fn()),
        }
        self._pending.append(item)
        self._bus.publish_immediate("VERIFY_SCHEDULED", {
            "action_id": action["id"],
            "metric": metric,
            "baseline": baseline,
            "deadline_seconds": deadline_secs,
            "time": datetime.now(timezone.utc).isoformat(),
        })
        print(f"[verify] scheduled: {action['id']} "
              f"(metric={metric}, deadline={deadline_secs}s)")

    def check_pending(self):
        """Check all pending verifications whose deadline has elapsed."""
        still_pending: List[dict] = []
        now_mono = time.monotonic()

        for item in self._pending:
            elapsed = now_mono - item["queued_at"]
            if elapsed < item["deadline_secs"]:
                still_pending.append(item)
                continue

            # Deadline reached – evaluate
            action = item["action"]
            vspec = action["verification"]
            metric = item["metric"]
            baseline = item["baseline"]
            actual = self._state.get_latest_value(metric)
            now_iso = datetime.now(timezone.utc).isoformat()

            if actual is None or baseline is None:
                passed = False
                delta = None
                reason = "missing_metric"
            else:
                delta = actual - baseline
                try:
                    passed = evaluate_comparison(vspec["op"], delta, vspec["target_delta"])
                except (ValueError, TypeError):
                    passed = False
                reason = None if passed else "threshold_not_met"

            log_entry = {
                "action_id": action["id"],
                "metric": metric,
                "baseline": baseline,
                "actual": actual,
                "delta": delta,
                "target_delta": vspec["target_delta"],
                "op": vspec["op"],
                "passed": passed,
                "config_hash": item.get("config_hash", ""),
                "time": now_iso,
            }

            if passed:
                log_entry["outcome"] = "VERIFY_PASSED"
                self._bus.publish_immediate("VERIFY_PASSED", log_entry)
                print(f"[verify] PASSED: {action['id']}")
            else:
                log_entry["outcome"] = "VERIFY_FAILED"
                log_entry["failure_reason"] = reason
                self._bus.publish_immediate("VERIFY_FAILED", log_entry)
                print(f"[verify] FAILED: {action['id']} – {reason}")
                self._do_rollback(action)

            self._vstore.log(log_entry)

        self._pending = still_pending

    def _do_rollback(self, action: dict):
        """Handle rollback based on rollback spec."""
        rb = action.get("rollback", {})
        rb_type = rb.get("type", "none")

        if rb_type == "action_ref":
            rb_action_id = rb.get("action_id")
            rb_action = self._actions_by_id.get(rb_action_id)
            if rb_action:
                # Import here to avoid circular at module level
                from .swarmz_adapter import InProcessSwarmzBus
                # We can't easily get the adapter here, so we emit an event
                # that the weaver or adapter can pick up
                self._bus.publish_immediate("ROLLBACK_TRIGGERED", {
                    "original_action_id": action["id"],
                    "rollback_action_id": rb_action_id,
                    "rollback_action": rb_action,
                    "type": "action_ref",
                    "time": datetime.now(timezone.utc).isoformat(),
                })
                print(f"[verify] rollback triggered: {rb_action_id}")
            else:
                print(f"[verify] rollback action not found: {rb_action_id}")

        elif rb_type == "instruction":
            steps = rb.get("steps", [])
            self._bus.publish_immediate("ROLLBACK_TRIGGERED", {
                "original_action_id": action["id"],
                "type": "instruction",
                "steps": steps,
                "time": datetime.now(timezone.utc).isoformat(),
            })
            print(f"[verify] rollback instructions emitted for {action['id']}")

        else:  # none
            print(f"[verify] no rollback configured for {action['id']}")


# ── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Verification Runner")
    parser.add_argument("--loop", action="store_true",
                        help="Run continuously")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="Check interval in seconds")
    args = parser.parse_args()

    bus = EventDebouncer(window=0.5)
    store = StateStore()
    vstore = VerificationStore()
    runner = VerificationRunner(store, vstore, bus)

    if args.loop:
        print("[verify] entering loop mode (Ctrl-C to stop)")
        try:
            while True:
                runner.check_pending()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[verify] stopped")
    else:
        runner.check_pending()
        print("[verify] one-shot check complete")


if __name__ == "__main__":
    main()
