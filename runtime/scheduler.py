from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from backend.life_runtime import tail_witness
from runtime.hooks import RuntimeHookDispatcher

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WITNESS_ROOT = PROJECT_ROOT / "observatory" / "witness"
WITNESS_ROOT.mkdir(parents=True, exist_ok=True)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ScheduledTask:
    name: str
    system_id: str
    hook: str
    min_interval_s: int
    max_interval_s: int
    next_due_at: datetime
    run_count: int = 0
    last_run_at: datetime | None = None


@dataclass
class SchedulerResult:
    executed: List[Dict[str, Any]] = field(default_factory=list)
    skipped: List[Dict[str, Any]] = field(default_factory=list)
    witness_flush_path: str | None = None


class RuntimeScheduler:
    """
    Deterministic scheduler for life-system cadences and periodic witness flushing.
    """

    def __init__(self, dispatcher: RuntimeHookDispatcher | None = None, seed: int = 7) -> None:
        self.dispatcher = dispatcher or RuntimeHookDispatcher()
        self.seed = int(seed)
        now = _utc_now()
        self.tasks: Dict[str, ScheduledTask] = {
            "diary": ScheduledTask(
                name="diary",
                system_id="life.diary.core",
                hook="on_consult",
                min_interval_s=30 * 60,
                max_interval_s=90 * 60,
                next_due_at=now,
            ),
            "breath": ScheduledTask(
                name="breath",
                system_id="life.breath.core",
                hook="on_invoke",
                min_interval_s=60,
                max_interval_s=300,
                next_due_at=now,
            ),
            "heart": ScheduledTask(
                name="heart",
                system_id="life.heart",
                hook="on_invoke",
                min_interval_s=60,
                max_interval_s=120,
                next_due_at=now,
            ),
            "awakening": ScheduledTask(
                name="awakening",
                system_id="life.awakening_loop.core",
                hook="on_consult",
                min_interval_s=2 * 60 * 60,
                max_interval_s=6 * 60 * 60,
                next_due_at=now,
            ),
            "dark_pool": ScheduledTask(
                name="dark_pool",
                system_id="life.cosmic.dark_pool_oracle",
                hook="on_trigger_anomaly",
                min_interval_s=300,
                max_interval_s=900,
                next_due_at=now,
            ),
            "noetic": ScheduledTask(
                name="noetic",
                system_id="life.cosmic.noetic_resonance",
                hook="on_symbolic_interpretation",
                min_interval_s=300,
                max_interval_s=900,
                next_due_at=now,
            ),
        }
        self._flush_interval_s = 300
        self._next_flush_at = now

    def _interval_for(self, task: ScheduledTask) -> int:
        span = max(1, task.max_interval_s - task.min_interval_s + 1)
        offset = (self.seed + task.run_count + sum(ord(ch) for ch in task.name)) % span
        return task.min_interval_s + offset

    def _payload_for(self, task: ScheduledTask) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "ritual_confirmation": {
                "confirmed": True,
                "source": "runtime.scheduler",
                "task": task.name,
            },
            "scheduler": {"task": task.name, "run_count": task.run_count},
        }
        if task.name == "diary":
            payload.update(
                {
                    "active_layers": ["symbolic", "life", "governance"],
                    "routing_imbalance": "balanced",
                    "operator_actions": ["approval_toggle", "panel_refresh"],
                    "anomalies": [],
                    "optimization_goals": ["stability", "coverage"],
                    "recent_missions": ["scheduler_heartbeat"],
                }
            )
        elif task.name == "breath":
            payload.update({"phase": "inhale" if task.run_count % 2 == 0 else "exhale"})
        elif task.name == "heart":
            payload.update({"swarm_health": 0.82})
        elif task.name == "awakening":
            payload.update(
                {
                    "active_layers": ["symbolic", "life", "proposals"],
                    "routing_patterns": {"symmetry": "stable"},
                    "cockpit_usage": {"refresh_events": 3},
                    "proposal_history": [],
                }
            )
        elif task.name == "dark_pool":
            payload.update({"death_states": 0})
        elif task.name == "noetic":
            payload.update({"pattern_spike": 0.41})
        return payload

    def flush_witness_log(self, now: datetime | None = None) -> str:
        timestamp = (now or _utc_now()).strftime("%Y%m%dT%H%M%SZ")
        snapshot_path = WITNESS_ROOT / f"flush-{timestamp}.json"
        snapshot = {
            "created_at": (now or _utc_now()).isoformat().replace("+00:00", "Z"),
            "count": 0,
            "witness": [],
        }
        witness = tail_witness(500)
        snapshot["count"] = len(witness)
        snapshot["witness"] = witness
        snapshot_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        return str(snapshot_path.relative_to(PROJECT_ROOT)).replace("\\", "/")

    def run_due_tasks(
        self,
        now: datetime | None = None,
        *,
        operator_approved: bool = False,
    ) -> SchedulerResult:
        now = now or _utc_now()
        result = SchedulerResult()

        for task in self.tasks.values():
            if now < task.next_due_at:
                result.skipped.append(
                    {
                        "task": task.name,
                        "reason": "not_due",
                        "next_due_at": task.next_due_at.isoformat().replace("+00:00", "Z"),
                    }
                )
                continue

            payload = self._payload_for(task)
            try:
                dispatched = self.dispatcher.dispatch(
                    hook=task.hook,
                    system_id=task.system_id,
                    payload=payload,
                    operator_approved=operator_approved,
                )
                status = "ok"
            except Exception as exc:  # pragma: no cover - explicit capture path
                dispatched = {"error": str(exc)}
                status = "error"

            task.run_count += 1
            task.last_run_at = now
            task.next_due_at = now + timedelta(seconds=self._interval_for(task))
            result.executed.append(
                {
                    "task": task.name,
                    "system_id": task.system_id,
                    "hook": task.hook,
                    "status": status,
                    "result": dispatched,
                    "next_due_at": task.next_due_at.isoformat().replace("+00:00", "Z"),
                }
            )

        if now >= self._next_flush_at:
            result.witness_flush_path = self.flush_witness_log(now=now)
            self._next_flush_at = now + timedelta(seconds=self._flush_interval_s)

        return result

    def run_once(self, operator_approved: bool = True) -> Dict[str, Any]:
        """
        Execute one scheduling cycle with deterministic payloads.
        """
        outcome = self.run_due_tasks(operator_approved=operator_approved)
        return {
            "executed": outcome.executed,
            "skipped": outcome.skipped,
            "witness_flush_path": outcome.witness_flush_path,
        }
