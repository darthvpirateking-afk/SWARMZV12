from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from runtime.scheduler import RuntimeScheduler

ROOT = Path(__file__).resolve().parents[1]


def _force_all_due(scheduler: RuntimeScheduler, now: datetime) -> None:
    for task in scheduler.tasks.values():
        task.next_due_at = now - timedelta(seconds=1)


def test_scheduler_runs_life_cadence_and_flushes_witness() -> None:
    scheduler = RuntimeScheduler(seed=11)
    now = datetime.now(timezone.utc)
    _force_all_due(scheduler, now)
    result = scheduler.run_due_tasks(now=now, operator_approved=True)

    assert result.executed
    assert any(item["status"] == "ok" for item in result.executed)
    assert result.witness_flush_path is not None
    assert (ROOT / result.witness_flush_path).exists()


def test_scheduler_enforces_operator_gate() -> None:
    scheduler = RuntimeScheduler(seed=17)
    now = datetime.now(timezone.utc)
    _force_all_due(scheduler, now)
    result = scheduler.run_due_tasks(now=now, operator_approved=False)

    assert result.executed
    assert any(item["status"] == "error" for item in result.executed)
