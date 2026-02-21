#!/usr/bin/env python3
"""
weaver_service.py – Main Layer-Weaver control-plane entry-point.

Runs an event-driven, debounced control cycle:
  1. Validate configs (objectives, coupling, actions) against JSON schemas
  2. Collect state from all layers
  3. Evaluate regime objectives with hysteresis
  4. Score eligible actions deterministically
  5. Select best action or suppress (NO_ACTION)
  6. Execute via SwarmzAdapter
  7. Log decision to decision_log.jsonl

Events emitted:
  WEAVER_CYCLE_STARTED, WEAVER_CYCLE_COMPLETED, CONFIG_INVALID,
  ACTION_SELECTED, NO_ACTION

Usage:
    python -m control_plane.layer_weaver.weaver_service
    python -m control_plane.layer_weaver.weaver_service --loop --interval 30
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import jsonschema

_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths
_DATA = os.path.join(_DIR, "data")
_SCHEMAS = os.path.join(_DIR, "schemas")
_OBJECTIVES_PATH = os.path.join(_DATA, "objectives.json")
_COUPLING_PATH = os.path.join(_DATA, "coupling.json")
_ACTIONS_PATH = os.path.join(_DATA, "actions.json")

from .event_debouncer import EventDebouncer
from .state_store import StateStore
from .decision_logger import DecisionLogger
from .swarmz_adapter import InProcessSwarmzBus
from .regime import RegimeManager
from .scoring import select_best_action, check_guardrails
from .layers.money import MoneyLayer
from .layers.health import HealthLayer
from .layers.build import BuildLayer
from .layers.swarm_health import SwarmHealthLayer
from .layers.permissions import PermissionsLayer
from .layers.memory import MemoryLayer

# ── Config loading + validation ────────────────────────────────────────


def _load_schema(name: str) -> dict:
    with open(os.path.join(_SCHEMAS, name)) as f:
        return json.load(f)


def _load_json(path: str) -> Any:
    with open(path) as f:
        return json.load(f)


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:16]


def compute_config_hash() -> str:
    """Compute deterministic config hash from objectives + coupling + actions."""
    parts = []
    for p in [_OBJECTIVES_PATH, _COUPLING_PATH, _ACTIONS_PATH]:
        if os.path.exists(p):
            parts.append(_file_hash(p))
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:24]


def validate_configs(bus: EventDebouncer) -> Optional[tuple]:
    """Validate all config files against schemas.

    Returns (objectives, coupling, actions) or None if invalid.
    Emits CONFIG_INVALID on failure.
    """
    errors: List[str] = []

    # Load schemas
    try:
        obj_schema = _load_schema("objective.schema.json")
        edge_schema = _load_schema("edge.schema.json")
        act_schema = _load_schema("action.schema.json")
    except Exception as e:
        errors.append(f"Schema load error: {e}")
        bus.publish_immediate("CONFIG_INVALID", {"errors": errors})
        return None

    # Load + validate objectives
    try:
        objectives = _load_json(_OBJECTIVES_PATH)
        jsonschema.validate(instance=objectives, schema=obj_schema)
    except Exception as e:
        errors.append(f"objectives.json: {e}")

    # Load + validate coupling
    try:
        coupling = _load_json(_COUPLING_PATH)
        if not isinstance(coupling, list):
            errors.append("coupling.json: must be a JSON array")
        else:
            for i, edge in enumerate(coupling):
                try:
                    jsonschema.validate(instance=edge, schema=edge_schema)
                except jsonschema.ValidationError as e:
                    errors.append(f"coupling.json[{i}]: {e.message}")
    except Exception as e:
        errors.append(f"coupling.json: {e}")

    # Load + validate actions
    try:
        actions = _load_json(_ACTIONS_PATH)
        if not isinstance(actions, list):
            errors.append("actions.json: must be a JSON array")
        else:
            for i, act in enumerate(actions):
                try:
                    jsonschema.validate(instance=act, schema=act_schema)
                except jsonschema.ValidationError as e:
                    errors.append(f"actions.json[{i}]: {e.message}")
    except Exception as e:
        errors.append(f"actions.json: {e}")

    if errors:
        bus.publish_immediate(
            "CONFIG_INVALID",
            {
                "errors": errors,
                "time": datetime.now(timezone.utc).isoformat(),
            },
        )
        return None

    return objectives, coupling, actions


# ── Weaver Cycle ────────────────────────────────────────────────────────


class WeaverService:
    """Event-driven control-plane service."""

    def __init__(self):
        self.bus = EventDebouncer(window=1.0)
        self.state_store = StateStore()
        self.decision_logger = DecisionLogger()
        self.adapter = InProcessSwarmzBus(self.state_store, self.bus)
        self.regime_mgr = RegimeManager()

        # Register layers
        self.layers = [
            MoneyLayer(),
            HealthLayer(),
            BuildLayer(),
            SwarmHealthLayer(),
            PermissionsLayer(),
            MemoryLayer(),
        ]

    def run_cycle(self) -> dict:
        """Execute one Weaver control cycle. Returns decision summary."""
        now = datetime.now(timezone.utc).isoformat()
        self.adapter.emit_event("WEAVER_CYCLE_STARTED", {"time": now})

        # 1. Validate configs
        result = validate_configs(self.bus)
        if result is None:
            print("[weaver] CONFIG_INVALID – skipping cycle")
            return {"outcome": "CONFIG_INVALID"}

        objectives_cfg, coupling, actions = result
        lambdas = objectives_cfg["global"]["lambdas"]
        target_ranges = objectives_cfg["global"]["target_ranges"]
        objectives_list = objectives_cfg["objectives"]
        config_hash = compute_config_hash()

        # 2. Collect state from layers
        for layer in self.layers:
            for rec in layer.collect():
                self.state_store.append(rec)

        state_values = self.state_store.all_latest_values()

        # 3. Evaluate regime objectives
        active_objs = self.regime_mgr.evaluate(objectives_list, state_values)
        active_ids = [o["id"] for o in active_objs]

        if not active_objs:
            decision = {
                "outcome": "NO_ACTION",
                "reason": "no_active_objectives",
                "active_objectives": [],
                "config_hash": config_hash,
                "time": now,
            }
            self.decision_logger.log(decision)
            self.adapter.emit_event("NO_ACTION", decision)
            self.adapter.emit_event("WEAVER_CYCLE_COMPLETED", decision)
            print(f"[weaver] NO_ACTION (no active objectives)")
            return decision

        # 4-5. Score and select best action
        best_action, breakdown = select_best_action(
            actions, active_objs, lambdas, target_ranges, coupling, state_values
        )

        if best_action is None:
            decision = {
                "outcome": "NO_ACTION",
                "reason": "no_eligible_or_positive_score",
                "active_objectives": active_ids,
                "config_hash": config_hash,
                "time": now,
            }
            self.decision_logger.log(decision)
            self.adapter.emit_event("NO_ACTION", decision)
            self.adapter.emit_event("WEAVER_CYCLE_COMPLETED", decision)
            print(f"[weaver] NO_ACTION (score <= 0 or ineligible)")
            return decision

        # 6. Execute
        task_id = self.adapter.publish({"action": best_action})

        decision = {
            "outcome": "ACTION_SELECTED",
            "action_id": best_action["id"],
            "task_id": task_id,
            "score_breakdown": breakdown,
            "active_objectives": active_ids,
            "config_hash": config_hash,
            "time": now,
        }
        self.decision_logger.log(decision)
        self.adapter.emit_event(
            "ACTION_SELECTED",
            {
                **decision,
                "action": best_action,
            },
        )
        self.adapter.emit_event("WEAVER_CYCLE_COMPLETED", decision)
        print(
            f"[weaver] ACTION_SELECTED: {best_action['id']} "
            f"(score={breakdown['score']})"
        )
        return decision


# ── CLI ─────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Layer-Weaver Service")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Cycle interval in seconds (with --loop)",
    )
    args = parser.parse_args()

    svc = WeaverService()

    if args.loop:
        print(f"[weaver] entering loop mode (interval={args.interval}s)")
        try:
            while True:
                svc.run_cycle()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[weaver] stopped")
    else:
        svc.run_cycle()
        print("[weaver] one-shot cycle complete")


if __name__ == "__main__":
    main()
