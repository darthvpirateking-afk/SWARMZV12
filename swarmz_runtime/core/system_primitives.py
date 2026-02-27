from __future__ import annotations

import hashlib
import json
import secrets
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Deque, Dict, List, Optional

ERROR_TAXONOMY: Dict[str, Dict[str, str]] = {
    "constraint_violation": {
        "severity": "high",
        "category": "policy",
        "description": "Request violates one or more operator constraints.",
    },
    "compile_failed": {
        "severity": "high",
        "category": "compiler",
        "description": "Mission compilation failed deterministically.",
    },
    "reality_sync_conflict": {
        "severity": "medium",
        "category": "sync",
        "description": "Reality sync stream received conflicting state update.",
    },
    "override_denied": {
        "severity": "high",
        "category": "override",
        "description": "Operator override rejected by doctrine gate.",
    },
    "unknown_error": {
        "severity": "medium",
        "category": "unknown",
        "description": "Unexpected runtime exception.",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify_error(
    code: str, message: str, details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    meta = ERROR_TAXONOMY.get(code, ERROR_TAXONOMY["unknown_error"])
    return {
        "code": code if code in ERROR_TAXONOMY else "unknown_error",
        "severity": meta["severity"],
        "category": meta["category"],
        "message": message,
        "details": details or {},
        "timestamp": _now(),
    }


class RealTimeConstraintSolver:
    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()

    @staticmethod
    def _key(
        mission_type: str, constraints: Dict[str, Any], facts: Dict[str, Any]
    ) -> str:
        payload = {
            "mission_type": mission_type,
            "constraints": constraints,
            "facts": facts,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def evaluate(
        self, mission_type: str, constraints: Dict[str, Any], facts: Dict[str, Any]
    ) -> Dict[str, Any]:
        k = self._key(mission_type, constraints, facts)
        with self._lock:
            if k in self._cache:
                cached = dict(self._cache[k])
                cached["cache_hit"] = True
                return cached

        violations: List[str] = []
        budget_cap = float(constraints.get("budget_cap", 0) or 0)
        planned_spend = float(facts.get("planned_spend", 0) or 0)
        autonomy = int(facts.get("autonomy_level", 0) or 0)
        max_autonomy = int(constraints.get("max_autonomy", 100) or 100)
        profit_floor = float(constraints.get("profit_floor", 0) or 0)
        projected_profit = float(facts.get("projected_profit", 0) or 0)

        if budget_cap > 0 and planned_spend > budget_cap:
            violations.append("budget_cap_exceeded")
        if autonomy > max_autonomy:
            violations.append("autonomy_exceeds_operator_cap")
        if projected_profit < profit_floor:
            violations.append("profit_floor_not_met")

        decision = {
            "mission_type": mission_type,
            "allowed": len(violations) == 0,
            "violations": violations,
            "cache_hit": False,
            "evaluated_at": _now(),
        }
        with self._lock:
            self._cache[k] = dict(decision)
        return decision


class DecisionLedger:
    def __init__(self, path: Path):
        self._path = path
        self._lock = RLock()

    def append(
        self,
        *,
        state_snapshot: Dict[str, Any],
        regime: str,
        scores: Dict[str, Any],
        chosen_action: str,
        suppression_reason: Optional[str],
        config_checksum: str,
    ) -> Dict[str, Any]:
        row = {
            "decision_id": f"dec-{secrets.token_hex(6)}",
            "state_snapshot": state_snapshot,
            "regime": regime,
            "scores": scores,
            "chosen_action": chosen_action,
            "suppression_reason": suppression_reason,
            "config_checksum": config_checksum,
            "timestamp": _now(),
        }
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
        return row


class ContractValidator:
    ALLOWED_TOP_LEVEL = {"action_type", "payload", "safety", "resources", "meta"}
    ALLOWED_ACTIONS = {
        "dispatch",
        "create_mission",
        "run_mission",
        "publish",
        "fulfill",
        "sync_template",
    }

    def validate(self, action: Dict[str, Any]) -> Dict[str, Any]:
        violations: List[str] = []

        if not isinstance(action, dict):
            violations.append("action_must_be_object")
            return {"allowed": False, "violations": violations}

        unknown_fields = [k for k in action.keys() if k not in self.ALLOWED_TOP_LEVEL]
        if unknown_fields:
            violations.append(f"unknown_fields:{','.join(sorted(unknown_fields))}")

        action_type = str(action.get("action_type", "")).strip()
        if not action_type:
            violations.append("action_type_required")
        elif action_type not in self.ALLOWED_ACTIONS:
            violations.append("action_type_not_allowed")

        payload = action.get("payload", {})
        if not isinstance(payload, dict):
            violations.append("payload_must_be_object")

        safety = action.get("safety", {})
        if not isinstance(safety, dict):
            violations.append("safety_must_be_object")
        else:
            if bool(safety.get("irreversible", False)) and not bool(
                safety.get("operator_approved", False)
            ):
                violations.append("irreversible_requires_operator_approval")

        resources = action.get("resources", {})
        if not isinstance(resources, dict):
            violations.append("resources_must_be_object")
        else:
            cpu = float(resources.get("cpu", 0) or 0)
            memory_mb = int(resources.get("memory_mb", 0) or 0)
            timeout_s = int(resources.get("timeout_s", 0) or 0)
            if cpu > 4.0:
                violations.append("cpu_limit_exceeded")
            if memory_mb > 4096:
                violations.append("memory_limit_exceeded")
            if timeout_s > 600:
                violations.append("timeout_limit_exceeded")

        meta = action.get("meta", {})
        if not isinstance(meta, dict):
            violations.append("meta_must_be_object")
        else:
            if not bool(meta.get("weaver_validated", False)):
                violations.append("weaver_validation_required")
            source = str(meta.get("source", "")).strip().lower()
            if source.startswith("companion") and not bool(
                meta.get("weaver_validated", False)
            ):
                violations.append("companion_bypass_forbidden")

        return {
            "allowed": len(violations) == 0,
            "violations": violations,
            "validated_at": _now(),
        }


class MissionCompiler:
    @staticmethod
    def compile_mission(
        intent: str,
        mission_type: str,
        constraints: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not intent.strip():
            raise ValueError("intent_required")

        mission_id = f"cmp-{secrets.token_hex(6)}"
        steps = [
            {"order": 1, "stage": "validate_constraints", "replayable": True},
            {"order": 2, "stage": "prepare_artifacts", "replayable": True},
            {"order": 3, "stage": "execute", "replayable": True},
            {"order": 4, "stage": "verify_outcome", "replayable": True},
            {"order": 5, "stage": "append_audit", "replayable": True},
        ]

        return {
            "mission_id": mission_id,
            "version": 1,
            "intent": intent,
            "mission_type": mission_type,
            "constraints": constraints,
            "context": context,
            "compiled_steps": steps,
            "compiled_at": _now(),
            "deterministic": True,
        }


class RealitySyncLayer:
    def __init__(self) -> None:
        self._queue: Deque[Dict[str, Any]] = deque()
        self._lock = RLock()
        self._state_projection: Dict[str, Any] = {
            "events_seen": 0,
            "last_event_type": None,
            "by_type": {},
        }

    def push(
        self, event_type: str, payload: Dict[str, Any], source: str = "runtime"
    ) -> Dict[str, Any]:
        event = {
            "event_id": f"evt-{secrets.token_hex(6)}",
            "event_type": event_type,
            "payload": payload,
            "source": source,
            "timestamp": _now(),
        }
        with self._lock:
            self._queue.append(event)
        return event

    def drain(self, max_items: int = 100) -> Dict[str, Any]:
        consumed: List[Dict[str, Any]] = []
        with self._lock:
            for _ in range(max(1, min(max_items, len(self._queue)))):
                item = self._queue.popleft()
                consumed.append(item)
                by_type = self._state_projection.setdefault("by_type", {})
                by_type[item["event_type"]] = (
                    int(by_type.get(item["event_type"], 0)) + 1
                )
                self._state_projection["events_seen"] = (
                    int(self._state_projection.get("events_seen", 0)) + 1
                )
                self._state_projection["last_event_type"] = item["event_type"]

        return {
            "consumed": consumed,
            "count": len(consumed),
            "projection": dict(self._state_projection),
            "drained_at": _now(),
        }

    def projection(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state_projection)


class OperatorOverrideShell:
    def __init__(self) -> None:
        self._lock = RLock()
        self._frozen = False
        self._max_autonomy_override: Optional[int] = None

    def execute(
        self, command: str, args: Dict[str, Any], operator_approved: bool, reason: str
    ) -> Dict[str, Any]:
        if not operator_approved:
            return {
                "ok": False,
                "error": classify_error(
                    "override_denied",
                    "Operator approval required for override shell execution.",
                    {"command": command},
                ),
            }

        with self._lock:
            if command == "freeze":
                self._frozen = True
                result = {"frozen": True}
            elif command == "unfreeze":
                self._frozen = False
                result = {"frozen": False}
            elif command == "set_max_autonomy":
                level = int(args.get("level", 0))
                self._max_autonomy_override = max(0, min(level, 100))
                result = {"max_autonomy_override": self._max_autonomy_override}
            elif command == "clear_max_autonomy":
                self._max_autonomy_override = None
                result = {"max_autonomy_override": None}
            elif command == "replay_checkpoint":
                result = {
                    "checkpoint": str(args.get("checkpoint", "latest")),
                    "replayed": True,
                }
            else:
                return {
                    "ok": False,
                    "error": classify_error(
                        "override_denied",
                        "Unsupported override command.",
                        {"command": command},
                    ),
                }

        return {
            "ok": True,
            "command": command,
            "reason": reason,
            "result": result,
            "executed_at": _now(),
        }

    def state(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "frozen": self._frozen,
                "max_autonomy_override": self._max_autonomy_override,
            }


class SystemPrimitivesRuntime:
    def __init__(self, root_dir: Path):
        self._root_dir = root_dir
        self._base = root_dir / "data" / "system_primitives"
        self._base.mkdir(parents=True, exist_ok=True)
        self._event_log = self._base / "immutable_event_log.jsonl"
        self._decision_ledger_file = self._base / "decision_ledger.jsonl"
        self._runtime_config_file = root_dir / "config" / "runtime.json"

        self.solver = RealTimeConstraintSolver()
        self.compiler = MissionCompiler()
        self.sync = RealitySyncLayer()
        self.override_shell = OperatorOverrideShell()
        self.validator = ContractValidator()
        self.decision_ledger = DecisionLedger(self._decision_ledger_file)

    def _config_checksum(self) -> str:
        if not self._runtime_config_file.exists():
            return "missing"
        raw = self._runtime_config_file.read_text(encoding="utf-8")
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _append_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        row = {
            "event_id": f"log-{secrets.token_hex(6)}",
            "event_type": event_type,
            "payload": payload,
            "timestamp": _now(),
        }
        with self._event_log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")

    def solve_constraints(
        self, mission_type: str, constraints: Dict[str, Any], facts: Dict[str, Any]
    ) -> Dict[str, Any]:
        decision = self.solver.evaluate(mission_type, constraints, facts)
        self._append_event("constraints_evaluated", decision)
        return decision

    def compile_mission(
        self,
        intent: str,
        mission_type: str,
        constraints: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        try:
            compiled = self.compiler.compile_mission(
                intent, mission_type, constraints, context
            )
        except Exception as exc:
            error = classify_error(
                "compile_failed",
                str(exc),
                {"intent": intent, "mission_type": mission_type},
            )
            self._append_event("mission_compile_failed", error)
            return {"ok": False, "error": error}
        self._append_event("mission_compiled", compiled)
        return {"ok": True, "compiled": compiled}

    def push_reality_event(
        self, event_type: str, payload: Dict[str, Any], source: str
    ) -> Dict[str, Any]:
        event = self.sync.push(event_type, payload, source)
        self._append_event("reality_event_pushed", event)
        return event

    def drain_reality_events(self, max_items: int) -> Dict[str, Any]:
        drained = self.sync.drain(max_items)
        self._append_event("reality_events_drained", {"count": drained.get("count", 0)})
        return drained

    def execute_override(
        self, command: str, args: Dict[str, Any], operator_approved: bool, reason: str
    ) -> Dict[str, Any]:
        result = self.override_shell.execute(command, args, operator_approved, reason)
        self._append_event("operator_override", result)
        return result

    def validate_contract(
        self, action: Dict[str, Any], regime: str = "default"
    ) -> Dict[str, Any]:
        decision = self.validator.validate(action)
        suppression_reason = (
            None if decision["allowed"] else ";".join(decision["violations"])
        )
        ledger_row = self.decision_ledger.append(
            state_snapshot={
                "override": self.override_shell.state(),
                "projection": self.sync.projection(),
            },
            regime=regime,
            scores={
                "violation_count": len(decision["violations"]),
                "allowed_score": 1.0 if decision["allowed"] else 0.0,
            },
            chosen_action=str(action.get("action_type", "unknown")),
            suppression_reason=suppression_reason,
            config_checksum=self._config_checksum(),
        )

        out = {
            "validation": decision,
            "ledger": ledger_row,
            "companion_notified": not decision["allowed"],
        }
        self._append_event("contract_validated", out)
        return out

    def snapshot(self) -> Dict[str, Any]:
        return {
            "override": self.override_shell.state(),
            "reality_projection": self.sync.projection(),
            "error_taxonomy": ERROR_TAXONOMY,
            "contract_validator": {
                "allowed_top_level": sorted(list(ContractValidator.ALLOWED_TOP_LEVEL)),
                "allowed_actions": sorted(list(ContractValidator.ALLOWED_ACTIONS)),
            },
        }
