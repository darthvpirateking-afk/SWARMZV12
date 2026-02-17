# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
verification_runner.py â€“ Post-action verification with automatic rollback.

Behaviour:
  * Listens for ``ACTION_SELECTED`` events.
  * Stores a baseline metric snapshot.
  * Waits until the verification deadline.
  * Checks the metric against the action's verification spec.
  * Emits ``VERIFY_PASSED`` or ``VERIFY_FAILED``.
  * On failure, auto-publishes the rollback action.
  * All outcomes are appended to verification_log.jsonl.

Usage:
    python verification_runner.py           # one-shot (verify last action)
    python verification_runner.py --loop    # continuous listener
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from control_plane.state_store import StateStore
from control_plane.verification_store import VerificationStore
from control_plane.event_debouncer import EventDebouncer
from control_plane.swarmz_adapter import SwarmzAdapter
from control_plane.expression_eval import evaluate

# Load actions for rollback lookup
_ACTIONS_PATH = os.path.join(_DIR, "data", "actions.json")
with open(_ACTIONS_PATH) as _f:
    _ACTIONS: list[dict] = json.load(_f)
_ACTIONS_BY_ID: dict[str, dict] = {a["action_id"]: a for a in _ACTIONS}


class VerificationRunner:
    """Verifies executed actions and triggers rollback on failure."""

    def __init__(self, store: StateStore, vstore: VerificationStore,
                 bus: EventDebouncer, adapter: SwarmzAdapter):
        self._state = store
        self._vstore = vstore
        self._bus = bus
        self._adapter = adapter
        self._pending: list[dict] = []

        bus.subscribe("ACTION_SELECTED", self._on_action_selected)

    def _on_action_selected(self, _event: str, action: dict):
        """Record the action for later verification."""
        vspec = action.get("verification")
        if not vspec:
            return
        baseline = self._state.get_value(vspec["metric"])
        self._pending.append({
            "action": action,
            "baseline": baseline,
            "queued_at": time.monotonic(),
        })

    def check_pending(self):
        """Check all pending verifications whose deadline has elapsed."""
        still_pending: list[dict] = []
        for item in self._pending:
            action = item["action"]
            vspec = action["verification"]
            elapsed = time.monotonic() - item["queued_at"]

            if elapsed < vspec["deadline_seconds"]:
                still_pending.append(item)
                continue

            # Deadline reached â€“ evaluate
            actual = self._state.get_value(vspec["metric"])
            passed = False
            if actual is not None:
                passed = evaluate(vspec["operator"], actual, vspec["threshold"])

            log_entry = {
                "action_id": action["action_id"],
                "metric": vspec["metric"],
                "baseline": item["baseline"],
                "actual": actual,
                "threshold": vspec["threshold"],
                "operator": vspec["operator"],
                "passed": passed,
            }

            if passed:
                log_entry["outcome"] = "VERIFY_PASSED"
                self._bus.publish("VERIFY_PASSED", log_entry)
                print(f"[verify] PASSED: {action['action_id']}")
            else:
                log_entry["outcome"] = "VERIFY_FAILED"
                self._bus.publish("VERIFY_FAILED", log_entry)
                print(f"[verify] FAILED: {action['action_id']} â€“ triggering rollback")
                self._do_rollback(action)

            self._vstore.log(log_entry)

        self._pending = still_pending

    def _do_rollback(self, action: dict):
        rb_spec = action.get("rollback", {})
        rb_id = rb_spec.get("action_id")
        rb_action = _ACTIONS_BY_ID.get(rb_id) if rb_id else None
        if rb_action:
            self._adapter.execute(rb_action)
            self._bus.publish("ROLLBACK_EXECUTED", rb_action)
            print(f"[verify] rollback executed: {rb_id}")
        else:
            print(f"[verify] no rollback action found for {action['action_id']}")


def main():
    parser = argparse.ArgumentParser(description="Verification runner")
    parser.add_argument("--loop", action="store_true",
                        help="Run continuously")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="Poll interval in seconds")
    args = parser.parse_args()

    bus = EventDebouncer(window=0.5)
    store = StateStore()
    vstore = VerificationStore()
    adapter = SwarmzAdapter(store, bus)
    runner = VerificationRunner(store, vstore, bus, adapter)

    if args.loop:
        print("[verify] entering loop mode (Ctrl-C to stop)")
        try:
            while True:
                runner.check_pending()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[verify] stopped")
    else:
        # One-shot: just check anything already pending
        runner.check_pending()
        print("[verify] one-shot check complete (no pending items in this run)")


if __name__ == "__main__":
    main()

