#!/usr/bin/env python3
"""
weaver_service.py – Main entry-point for the Layer-Weaver control plane.

Runs an event-driven loop:
  1. Collects state from all layers.
  2. Evaluates regime-based objectives.
  3. Scores candidate actions.
  4. Selects (or skips) the best action.
  5. Executes via the SwarmzAdapter.
  6. Logs every decision.

Usage:
    python weaver_service.py            # one-shot cycle
    python weaver_service.py --loop     # continuous (Ctrl-C to stop)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

# ── ensure the package is importable when run as a script ──────────────
_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from control_plane.state_store import StateStore
from control_plane.decision_logger import DecisionLogger
from control_plane.event_debouncer import EventDebouncer
from control_plane.scoring import select_best
from control_plane.regime import RegimeManager
from control_plane.swarmz_adapter import SwarmzAdapter

from control_plane.layers.money import MoneyLayer
from control_plane.layers.health import HealthLayer
from control_plane.layers.build import BuildLayer
from control_plane.layers.swarm_health import SwarmHealthLayer
from control_plane.layers.permissions import PermissionsLayer
from control_plane.layers.memory import MemoryLayer

# ── load actions catalogue ─────────────────────────────────────────────
_ACTIONS_PATH = os.path.join(_DIR, "data", "actions.json")
with open(_ACTIONS_PATH) as _f:
    ACTIONS: list[dict] = json.load(_f)


def _build_components():
    bus = EventDebouncer(window=0.5)
    store = StateStore()
    logger = DecisionLogger()
    adapter = SwarmzAdapter(store, bus)
    regime = RegimeManager()

    layers = [
        MoneyLayer(store, bus),
        HealthLayer(store, bus),
        BuildLayer(store, bus),
        SwarmHealthLayer(store, bus),
        PermissionsLayer(store, bus),
        MemoryLayer(store, bus),
    ]
    return bus, store, logger, adapter, regime, layers


def run_cycle(bus, store, logger, adapter, regime, layers):
    """Execute one full collect → score → act cycle.  Returns the decision."""
    # 1. Collect
    for layer in layers:
        for rec in layer.collect():
            store.put(rec)
    bus.publish("STATE_UPDATED")

    # 2. Regimes
    active_objs = regime.active_objectives(store.get_value)

    # 3. State snapshot for scoring
    state_snap = {v: store.get(v) for v in store.all_latest()}

    # 4. Score & select
    best = select_best(ACTIONS, state_snap)

    if best is None:
        decision = {"decision": "NO_ACTION", "reason": "best score <= 0"}
        logger.log(decision)
        bus.publish("NO_ACTION", decision)
        print("[weaver] NO_ACTION selected")
        return decision

    # 5. Execute
    adapter.execute(best)
    bus.publish("ACTION_SELECTED", best)

    decision = {
        "decision": "ACTION_SELECTED",
        "action_id": best["action_id"],
        "name": best["name"],
        "active_objectives": [o["objective_id"] for o in active_objs],
    }
    logger.log(decision)
    print(f"[weaver] selected {best['action_id']}: {best['name']}")
    return decision


def main():
    parser = argparse.ArgumentParser(description="Layer-Weaver control plane")
    parser.add_argument("--loop", action="store_true",
                        help="Run continuously instead of one-shot")
    parser.add_argument("--interval", type=float, default=5.0,
                        help="Seconds between cycles in loop mode")
    args = parser.parse_args()

    bus, store, logger, adapter, regime, layers = _build_components()

    if args.loop:
        print("[weaver] entering loop mode (Ctrl-C to stop)")
        try:
            while True:
                run_cycle(bus, store, logger, adapter, regime, layers)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[weaver] stopped")
    else:
        run_cycle(bus, store, logger, adapter, regime, layers)


if __name__ == "__main__":
    main()
