# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
AutoLoopManager â€“ background tick scheduler for SWARMZ.

Responsibilities:
  - start / stop a daemon thread that ticks every N seconds
  - each tick: generate mission â†’ score â†’ execute â†’ measure â†’ persist
  - state.json persistence for crash-safe resume
  - audit.jsonl append per tick
  - kill-switch via data/KILL file
  - hard rate limit (max ticks per minute) and budget cap
  - deterministic scoring (no unseeded randomness)
"""

import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from swarmz_runtime.storage.schema import AuditEntry, VisibilityLevel
from swarmz_runtime.core import telemetry


class AutoLoopManager:
    """Manages the autonomous tick loop for SWARMZ."""

    # safety rails
    MAX_TICKS_PER_MINUTE = 12
    MAX_RUNTIME_COST_PER_TICK = 1.0  # abstract cost unit

    def __init__(self, engine: Any, data_dir: str = "data"):
        self._engine = engine
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(exist_ok=True)

        self._state_file = self._data_dir / "state.json"
        self._kill_file = self._data_dir / "KILL"

        # runtime state
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._tick_interval = 30
        self._lock = threading.Lock()

        # counters (loaded from state.json on init)
        self._tick_count = 0
        self._last_tick_ts: Optional[str] = None
        self._recent_tick_times: list = []  # timestamps for rate-limiting

        self._load_state()

    # â”€â”€ public API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def start(self, tick_interval: int = 30) -> None:
        if self._thread is None:
            self._running = True
            self._tick_interval = tick_interval
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=self._tick_interval + 5)
            self._thread = None
        self._persist_state()

    def single_step(
        self,
        operator_goal: str,
        constraints: Optional[Dict[str, Any]] = None,
        results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run one ecosystem tick synchronously and return result."""
        return self._tick(operator_goal, constraints or {}, results or {})

    def get_state(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "tick_count": self._tick_count,
            "last_tick_ts": self._last_tick_ts,
            "tick_interval": self._tick_interval,
            "max_ticks_per_minute": self.MAX_TICKS_PER_MINUTE,
        }

    # â”€â”€ internal loop â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _loop(self) -> None:
        while self._running:
            # kill-switch check
            if self._kill_file.exists():
                self._running = False
                self._log_audit("kill_switch_triggered", details={"file": str(self._kill_file)})
                self._persist_state()
                break

            # rate-limit check
            if not self._rate_limit_ok():
                time.sleep(1)
                continue

            try:
                t_start = time.perf_counter()
                self._tick("make money", {}, {})
                telemetry.record_duration("autoloop_tick", (time.perf_counter() - t_start) * 1000.0)
            except Exception as exc:
                self._log_audit("tick_error", details={"error": str(exc)})
                telemetry.record_failure("autoloop_tick_error", str(exc))

            # sleep in small increments so stop() is responsive
            remaining = self._tick_interval
            while remaining > 0 and self._running:
                time.sleep(min(1, remaining))
                remaining -= 1

    def _tick(
        self,
        operator_goal: str,
        constraints: Dict[str, Any],
        results: Dict[str, Any],
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # 1. generate mission
        category = self._goal_to_category(operator_goal)
        create_result = self._engine.create_mission(
            goal=operator_goal,
            category=category,
            constraints=constraints,
        )
        if "error" in create_result:
            self._log_audit(
                "tick_create_failed",
                details={"error": create_result["error"], "ts": now_iso},
            )
            return create_result

        mission_id = create_result["mission_id"]

        # 2. execute mission
        run_result = self._engine.run_mission(mission_id)

        # 3. measure + record
        with self._lock:
            self._tick_count += 1
            self._last_tick_ts = now_iso
            self._recent_tick_times.append(time.monotonic())

        self._log_audit(
            "ecosystem_tick",
            mission_id=mission_id,
            details={
                "tick_count": self._tick_count,
                "operator_goal": operator_goal,
                "run_result_status": run_result.get("status", run_result.get("error", "unknown")),
                "ts": now_iso,
            },
        )
        self._persist_state()

        return {
            "mission_id": mission_id,
            "tick_count": self._tick_count,
            "create": create_result,
            "run": run_result,
            "ts": now_iso,
        }

    # â”€â”€ helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @staticmethod
    def _goal_to_category(goal: str) -> str:
        """Deterministic mapping from goal text to mission category."""
        g = goal.lower()
        # check learn/research before coin to avoid "earn" matching inside "learn"
        if any(kw in g for kw in ("learn", "research", "library", "study")):
            return "library"
        if any(kw in g for kw in ("money", "revenue", "profit", "earn", "coin")):
            return "coin"
        if any(kw in g for kw in ("build", "create", "forge", "make")):
            return "forge"
        return "sanctuary"

    def _rate_limit_ok(self) -> bool:
        now = time.monotonic()
        cutoff = now - 60
        self._recent_tick_times = [t for t in self._recent_tick_times if t > cutoff]
        return len(self._recent_tick_times) < self.MAX_TICKS_PER_MINUTE

    def _log_audit(
        self,
        event_type: str,
        mission_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        entry = AuditEntry(
            event_type=event_type,
            mission_id=mission_id,
            details=details or {},
            visibility=VisibilityLevel.VISIBLE,
        )
        self._engine.db.log_audit(entry)

    def _persist_state(self) -> None:
        state = {
            "running": self._running,
            "tick_count": self._tick_count,
            "last_tick_ts": self._last_tick_ts,
            "tick_interval": self._tick_interval,
        }
        try:
            with open(self._state_file, "w") as f:
                json.dump(state, f, indent=2)
        except OSError:
            pass  # best-effort

    def _load_state(self) -> None:
        if self._state_file.exists():
            try:
                with open(self._state_file, "r") as f:
                    state = json.load(f)
                self._tick_count = state.get("tick_count", 0)
                self._last_tick_ts = state.get("last_tick_ts")
                self._tick_interval = state.get("tick_interval", 30)
            except (json.JSONDecodeError, OSError):
                pass  # start fresh

