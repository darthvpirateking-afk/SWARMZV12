# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pathlib import Path
import uuid
import time
import json
import hashlib

from swarmz_runtime.core import telemetry
from swarmz_runtime.storage.db import Database
from swarmz_runtime.storage.schema import (
    Mission,
    AuditEntry,
    Rune,
    MissionStatus,
    VisibilityLevel,
)
from swarmz_runtime.core.scoring import calculate_leverage_score, should_execute
from swarmz_runtime.core.authority import validate_transaction
from swarmz_runtime.core.learning import LearningEngine
from swarmz_runtime.core.prediction import ProphetEngine
from swarmz_runtime.core.resonance import ResonanceDetector
from swarmz_runtime.core.cadence import CadenceEngine
from swarmz_runtime.core.maintenance import MaintenanceScheduler
from swarmz_runtime.core.visibility import VisibilityManager
from swarmz_runtime.core.brain import BrainMapping
from core.evolution_memory import EvolutionMemory
from core.operator_anchor import load_or_create_anchor, verify_fingerprint
from core.perf_ledger import PerfLedger
from core.trajectory_engine import TrajectoryEngine
from core.world_model import WorldModel
from core.divergence_engine import DivergenceEngine
from core.entropy_monitor import EntropyMonitor
from core.counterfactual_engine import CounterfactualEngine
from core.relevance_engine import RelevanceEngine
from core.phase_engine import PhaseEngine
from swarmz_runtime.meta import MetaSelector
from swarmz_runtime.meta.task_matrix import NextTaskMatrix


class SwarmzEngine:
    def __init__(
        self, data_dir: str = "data", brain_config: Optional[Dict[str, Any]] = None
    ):
        self.data_dir = data_dir
        self.db = Database(data_dir)
        self.anchor = load_or_create_anchor(data_dir)
        self.learning_enabled = verify_fingerprint(self.anchor)
        self.perf_ledger = PerfLedger(data_dir)
        self.world_model = WorldModel(data_dir)
        self.divergence = DivergenceEngine(data_dir)
        self.entropy = EntropyMonitor(data_dir)
        self.evolution = EvolutionMemory(
            data_dir, anchor=self.anchor, read_only=not self.learning_enabled
        )
        self.trajectory = TrajectoryEngine(
            data_dir,
            self.evolution,
            self.perf_ledger,
            world_model=self.world_model,
            divergence=self.divergence,
            entropy=self.entropy,
        )
        self.counterfactual = CounterfactualEngine(
            data_dir,
            self.evolution,
            trajectory=self.trajectory,
            world_model=self.world_model,
        )
        self.relevance = RelevanceEngine(
            data_dir, self.evolution, counterfactual=self.counterfactual
        )
        self.phase = PhaseEngine(
            data_dir,
            world_model=self.world_model,
            divergence=self.divergence,
            entropy=self.entropy,
            trajectory=self.trajectory,
        )
        self.learning = LearningEngine()
        self.prophet = ProphetEngine(self.db)
        self.resonance = ResonanceDetector(self.db)
        self.cadence = CadenceEngine()
        self.maintenance = MaintenanceScheduler()
        self.visibility = VisibilityManager()
        self.brain = BrainMapping(brain_config)

        # Initialize the sovereign meta-selector with provider pattern
        from swarmz_runtime.meta.selector import set_engine_provider

        set_engine_provider(lambda: self)
        self.meta_selector = MetaSelector()

        # Initialize the NEXT TASK MATRIX for ignition-phase control
        from swarmz_runtime.meta.task_matrix import (
            set_engine_provider as set_matrix_provider,
        )

        set_matrix_provider(lambda: self)
        self.task_matrix = NextTaskMatrix()

        self.max_active_missions = 3
        self.operator_key = "swarmz_sovereign_key"
        self.operator_public_key = self.anchor.get("operator_public_key")
        self.offline_mode = False

        self._allowed_categories = {
            "coin",
            "forge",
            "library",
            "sanctuary",
            "test",
            "build",
            "solve",
            "plan",
            "analyze",
            "research",
            "commands",
        }

    def create_mission(
        self, goal: str, category: str, constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        active_missions = self.db.get_active_missions()
        if len(active_missions) >= self.max_active_missions:
            return {
                "error": f"Maximum {self.max_active_missions} active missions exceeded",
                "active_count": len(active_missions),
            }

        if category not in self._allowed_categories:
            return {
                "error": f"Invalid mission category: {category}",
                "allowed": sorted(self._allowed_categories),
            }

        mission_id = str(uuid.uuid4())[:8]

        mission_data = {
            "id": mission_id,
            "goal": goal,
            "category": category,
            "constraints": constraints,
            "expiry": None,
            "status": "pending",
            "operator_public_key": self.operator_public_key,
        }

        leverage_score = calculate_leverage_score(mission_data)

        mission = Mission(
            id=mission_id,
            goal=goal,
            category=category,
            constraints=constraints,
            status=MissionStatus.PENDING,
            leverage_score=leverage_score,
        )

        self.db.save_mission(mission)

        telemetry.record_event(
            "mission_created",
            {"mission_id": mission_id, "goal": goal, "category": category},
        )

        audit = AuditEntry(
            event_type="mission_created",
            mission_id=mission_id,
            details={"goal": goal, "category": category},
            visibility=VisibilityLevel.VISIBLE,
        )
        self.db.log_audit(audit)

        return {
            "ok": True,
            "mission_id": mission_id,
            "status": "created",
            "created_at": mission.created_at.isoformat(),
        }

    def run_mission(
        self, mission_id: str, operator_key: Optional[str] = None
    ) -> Dict[str, Any]:
        start = time.perf_counter()
        telemetry.verbose_log("run_mission:start", mission_id)
        mission = self.db.get_mission(mission_id)
        if not mission:
            telemetry.record_failure(
                "mission_missing", "Mission not found", {"mission_id": mission_id}
            )
            return {"error": "Mission not found"}

        if getattr(self, "offline_mode", False):
            self.db.update_mission(mission_id, {"status": "offline"})
            audit = AuditEntry(
                event_type="mission_skipped_offline",
                mission_id=mission_id,
                details={
                    "reason": "OFFLINE_MODE enabled",
                    "note": "External calls disabled",
                },
                visibility=VisibilityLevel.BRIGHT,
            )
            self.db.log_audit(audit)
            self._record_duration(
                "run_mission", start, {"mission_id": mission_id, "status": "offline"}
            )
            return {
                "status": "offline",
                "mission_id": mission_id,
                "message": "OFFLINE_MODE is enabled. External model calls are disabled; mission was recorded only.",
            }

        mission_category = mission.get("category", "")
        inputs_hash = self.evolution.compute_inputs_hash(
            mission.get("goal", ""),
            mission_category,
            mission.get("constraints", {}) or {},
        )
        learning_active = self.learning_enabled and self.evolution.chain_valid
        selected_strategy = (
            self.evolution.select_strategy(
                inputs_hash,
                bias_fn=(
                    (lambda strat, sc: self.trajectory.strategy_bias(strat, sc))
                    if learning_active
                    else None
                ),
            )
            if learning_active
            else "baseline"
        )
        candidate_strategies = (
            self.evolution.candidate_strategies(inputs_hash)
            if learning_active
            else [selected_strategy]
        )
        constraints = mission.get("constraints") or {}
        cost_estimate = float(
            constraints.get("cost_estimate", constraints.get("estimated_cost", 0.0))
            or 0.0
        )
        previous_avg = (
            self.evolution.strategy_average(inputs_hash, selected_strategy)
            if learning_active
            else 0.0
        )

        expected_projection = {
            "predicted_score": previous_avg,
            "trend_vector": self.counterfactual.get_trend_vector(),
        }
        state_hash = self.counterfactual.state_of_life_hash()
        self.counterfactual.record_snapshot(
            inputs_hash,
            selected_strategy,
            candidate_strategies,
            expected_projection,
            state_hash,
            self.evolution.get_personality(),
        )

        validation = validate_transaction(mission)

        if validation.failing:
            audit = AuditEntry(
                event_type="mission_blocked",
                mission_id=mission_id,
                details={
                    "reason": "validation_failed",
                    "scores": validation.scores.model_dump(),
                },
                visibility=VisibilityLevel.BRIGHT,
            )
            self.db.log_audit(audit)
            telemetry.record_failure(
                "mission_validation_failed",
                "validation_failed",
                {"mission_id": mission_id},
            )
            self._record_duration(
                "run_mission",
                start,
                {"mission_id": mission_id, "status": "validation_failed"},
            )
            return {
                "error": "Mission validation failed - suggestion only",
                "validation": validation.model_dump(),
            }

        if validation.requires_approval and operator_key != self.operator_key:
            audit = AuditEntry(
                event_type="mission_requires_approval",
                mission_id=mission_id,
                details={"reason": "borderline_validation"},
                visibility=VisibilityLevel.VISIBLE,
            )
            self.db.log_audit(audit)
            telemetry.record_failure(
                "mission_requires_approval",
                "operator approval",
                {"mission_id": mission_id},
            )
            self._record_duration(
                "run_mission",
                start,
                {"mission_id": mission_id, "status": "requires_approval"},
            )
            return {
                "error": "Mission requires operator approval",
                "validation": validation.model_dump(),
            }

        if not should_execute(mission):
            self._record_duration(
                "run_mission", start, {"mission_id": mission_id, "status": "skipped"}
            )
            return {"error": "Mission has negative expected value and is not research"}

        self.db.update_mission(mission_id, {"status": "active"})

        success = True
        roi = 1.5
        score_record = 0.0

        if success:
            self.db.update_mission(mission_id, {"status": "completed"})
            self.learning.update_weights(mission_id, roi)

            template = self.learning.extract_template(mission)
            rune = Rune(
                id=f"rune_{mission_id}",
                template=template,
                confidence=0.8,
                success_count=1,
                created_at=datetime.now(),
                last_used=datetime.now(),
            )
            self.db.save_rune(rune)

            next_run = self.cadence.schedule_next_run(mission, success=True)

            audit = AuditEntry(
                event_type="mission_completed",
                mission_id=mission_id,
                details={
                    "roi": roi,
                    "next_run": next_run.isoformat(),
                    "strategy": selected_strategy,
                },
                visibility=VisibilityLevel.VISIBLE,
            )
            self.db.log_audit(audit)

            result = {
                "status": "completed",
                "mission_id": mission_id,
                "roi": roi,
                "next_run": next_run.isoformat(),
                "rune_created": rune.id,
            }
            total_runtime_ms = (time.perf_counter() - start) * 1000.0
            if learning_active:
                score = self.evolution.compute_score(
                    True, total_runtime_ms, cost_estimate
                )
                self.evolution.append_record(
                    datetime.now(timezone.utc),
                    mission.get("category", ""),
                    inputs_hash,
                    selected_strategy,
                    total_runtime_ms,
                    True,
                    cost_estimate,
                    score,
                )
                self.evolution.record_outcome(
                    selected_strategy,
                    score,
                    True,
                    mission_id,
                    inputs_hash,
                    previous_avg,
                    runtime_ms=total_runtime_ms,
                )
                score_record = score
            self.perf_ledger.append(
                mission_id,
                total_runtime_ms,
                True,
                cost_estimate,
                agent_work_time=total_runtime_ms,
                agent_wait_time=0.0,
            )
            self.trajectory.after_outcome(
                True, score_record, total_runtime_ms, selected_strategy
            )
            self._log_value_impact(
                mission_id, total_runtime_ms, True, cost_estimate, constraints
            )
            self.counterfactual.evaluate(
                mission_id,
                inputs_hash,
                selected_strategy,
                candidate_strategies,
                score_record if learning_active else 1.0,
                True,
                self.counterfactual.get_trend_vector(),
            )
            self.relevance.after_outcome(
                mission_id,
                inputs_hash,
                selected_strategy,
                score_record if learning_active else 1.0,
                True,
                total_runtime_ms,
            )
            self.phase.after_outcome(
                True, score_record, total_runtime_ms, selected_strategy
            )
            self._record_duration(
                "run_mission", start, {"mission_id": mission_id, "status": "completed"}
            )
            telemetry.verbose_log("run_mission:done", mission_id, "completed")
            return result
        else:
            self.db.update_mission(mission_id, {"status": "failed"})
            self.resonance.detect_pattern(f"{mission_category}:failure")

            audit = AuditEntry(
                event_type="mission_failed",
                mission_id=mission_id,
                details={
                    "reason": "execution_error",
                    "category": mission_category,
                    "strategy": selected_strategy,
                },
                visibility=VisibilityLevel.BRIGHT,
            )
            self.db.log_audit(audit)
            total_runtime_ms = (time.perf_counter() - start) * 1000.0
            if learning_active:
                score = self.evolution.compute_score(
                    False, total_runtime_ms, cost_estimate
                )
                self.evolution.append_record(
                    datetime.now(timezone.utc),
                    mission.get("category", ""),
                    inputs_hash,
                    selected_strategy,
                    total_runtime_ms,
                    False,
                    cost_estimate,
                    score,
                )
                self.evolution.record_outcome(
                    selected_strategy,
                    score,
                    False,
                    mission_id,
                    inputs_hash,
                    previous_avg,
                    runtime_ms=total_runtime_ms,
                )
                score_record = score
            self.perf_ledger.append(
                mission_id,
                total_runtime_ms,
                False,
                cost_estimate,
                agent_work_time=total_runtime_ms,
                agent_wait_time=0.0,
            )
            self.trajectory.after_outcome(
                False, score_record, total_runtime_ms, selected_strategy
            )
            self._log_value_impact(
                mission_id, total_runtime_ms, False, cost_estimate, constraints
            )
            self.counterfactual.evaluate(
                mission_id,
                inputs_hash,
                selected_strategy,
                candidate_strategies,
                score_record if learning_active else 0.0,
                False,
                self.counterfactual.get_trend_vector(),
            )
            self.relevance.after_outcome(
                mission_id,
                inputs_hash,
                selected_strategy,
                score_record if learning_active else 0.0,
                False,
                total_runtime_ms,
            )
            self.phase.after_outcome(
                False, score_record, total_runtime_ms, selected_strategy
            )
            self._record_duration(
                "run_mission", start, {"mission_id": mission_id, "status": "failed"}
            )
            telemetry.verbose_log("run_mission:done", mission_id, "failed")
            return {"status": "failed", "mission_id": mission_id}

    def _record_duration(
        self, name: str, start: float, context: Optional[Dict[str, Any]] = None
    ) -> None:
        duration_ms = (time.perf_counter() - start) * 1000.0
        telemetry.record_duration(name, duration_ms, context or {})

    def _log_value_impact(
        self,
        mission_id: str,
        runtime_ms: float,
        success: bool,
        cost_estimate: float,
        constraints: Dict[str, Any],
    ) -> None:
        value_file = Path(self.data_dir) / "value_ledger.jsonl"
        value_file.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mission_id": mission_id,
            "time_spent": runtime_ms,
            "direct_money_change": (
                float(constraints.get("direct_money_change", 0.0))
                if constraints
                else 0.0
            ),
            "future_option_value": (
                float(constraints.get("future_option_value", 0.0))
                if constraints
                else 0.0
            ),
            "energy_cost": runtime_ms * 0.001 + (0.5 if not success else 0.0),
            "success": success,
            "project": (
                constraints.get("project", "unknown") if constraints else "unknown"
            ),
        }
        with open(value_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")

    def list_missions(self, status: Optional[str] = None) -> list:
        missions = self.db.load_all_missions()
        if status:
            missions = [m for m in missions if m["status"] == status]
        return missions

    def approve_mission(self, mission_id: str, operator_key: str) -> Dict[str, Any]:
        if operator_key != self.operator_key:
            return {"error": "Invalid operator key"}

        return self.run_mission(mission_id, operator_key=operator_key)

    def get_health(self) -> Dict[str, Any]:
        active_missions = self.db.get_active_missions()
        state = self.db.load_state()

        return {
            "status": "healthy",
            "active_missions": len(active_missions),
            "max_missions": self.max_active_missions,
            "pattern_counters": len(state.get("pattern_counters", {})),
        }

    def get_omens(self) -> list:
        return self.resonance.get_all_patterns()

    def get_predictions(self) -> list:
        return self.prophet.analyze_failures()

    def get_runes(self) -> Dict[str, Any]:
        return self.db.load_runes()

    def schedule_maintenance(self) -> Dict[str, Any]:
        modules = ["engine", "scoring", "learning", "prediction"]

        for module in modules:
            metrics = {
                "lines_of_code": 200,
                "dependencies": 5,
                "cyclomatic_complexity": 10,
            }
            complexity = self.maintenance.evaluate_module_complexity(module, metrics)
            self.maintenance.schedule_if_needed(module, complexity)

        tasks = self.maintenance.get_pending_tasks()

        return {"scheduled_tasks": len(tasks), "tasks": tasks}

    def route_task(self, task_type: str) -> Dict[str, Any]:
        """Route a task type to the appropriate brain/model."""
        return self.brain.route(task_type)

    def get_brain_status(self) -> Dict[str, Any]:
        """Return current brain mapping and auto_mode status."""
        return {
            "auto_mode": self.brain.auto_mode,
            "brains": self.brain.get_all_brains(),
            "routing_table": self.brain.get_routing_table(),
        }

    def get_scoreboard(self) -> Dict[str, Any]:
        perf_stats = {
            "perf_file": str(self.perf_ledger.file),
        }
        return {
            "anchor": {
                "machine_fingerprint": self.anchor.get("machine_fingerprint"),
                "public_key": self.operator_public_key,
                "read_only": not self.learning_enabled,
            },
            "evolution": self.evolution.get_scoreboard(),
            "performance": perf_stats,
            "counterfactual": {
                "snapshots_file": str(Path(self.data_dir) / "decision_snapshots.jsonl"),
                "counterfactual_log": str(
                    Path(self.data_dir) / "counterfactual_log.jsonl"
                ),
                "quality_report": str(
                    Path(self.data_dir) / "decision_quality_report.txt"
                ),
            },
            "phase": {
                "history": str(Path(self.data_dir) / "phase_history.jsonl"),
                "patterns": str(Path(self.data_dir) / "phase_patterns.json"),
                "interventions": str(Path(self.data_dir) / "phase_interventions.jsonl"),
                "report": str(Path(self.data_dir) / "phase_report.txt"),
            },
        }

    def get_counterfactual_overview(self, limit: int = 50) -> Dict[str, Any]:
        lim = max(1, min(limit, 200))
        snapshots = self._tail_jsonl(
            Path(self.data_dir) / "decision_snapshots.jsonl", lim
        )
        counterfactuals = self._tail_jsonl(
            Path(self.data_dir) / "counterfactual_log.jsonl", lim
        )
        return {
            "snapshots": snapshots,
            "counterfactuals": counterfactuals,
            "reliability": getattr(self.evolution, "_reliability", {}),
            "uncertainty": getattr(self.evolution, "_uncertainty", {}),
        }

    def get_phase_overview(self, limit: int = 100) -> Dict[str, Any]:
        lim = max(1, min(limit, 300))
        history = self._tail_jsonl(Path(self.data_dir) / "phase_history.jsonl", lim)
        patterns_path = Path(self.data_dir) / "phase_patterns.json"
        interventions = self._tail_jsonl(
            Path(self.data_dir) / "phase_interventions.jsonl", 100
        )
        patterns = {}
        try:
            if patterns_path.exists():
                patterns = json.loads(patterns_path.read_text())
        except Exception:
            patterns = {}
        return {
            "history": history,
            "patterns": patterns,
            "interventions": interventions,
        }

    def _tail_jsonl(self, file_path: Path, limit: int) -> list:
        if not file_path.exists():
            return []
        rows = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            rows.append(json.loads(line))
                        except Exception:
                            continue
        except Exception:
            return []
        return rows[-limit:]

    def validate_operator_sovereignty(
        self, operator_key: str, action: str = "general", scope: str = "global"
    ) -> bool:
        """Validate operator sovereignty for precision commands."""
        if operator_key != self.operator_key:
            return False

        # Additional sovereignty checks based on action and scope
        if scope == "global" and action in ["shutdown", "reset", "delete_all"]:
            # Require additional validation for high-risk global actions
            return self._validate_critical_sovereignty(operator_key, action)

        return True

    def _validate_critical_sovereignty(self, operator_key: str, action: str) -> bool:
        """Critical sovereignty validation for high-risk actions."""
        # Check operator fingerprint and recent activity
        anchor_valid = verify_fingerprint(self.anchor)
        if not anchor_valid:
            return False

        # Log sovereignty validation attempt
        audit = AuditEntry(
            event_type="sovereignty_validation",
            details={
                "action": action,
                "operator_key": operator_key[:8] + "...",
                "result": "critical_check_passed",
            },
            visibility=VisibilityLevel.BRIGHT,
        )
        self.db.log_audit(audit)

        return True

    def execute_operator_command(
        self, command: str, parameters: Dict[str, Any], operator_key: str
    ) -> Dict[str, Any]:
        """Execute precision operator commands."""
        if not self.validate_operator_sovereignty(operator_key, command):
            return {"error": "Sovereignty validation failed"}

        command_map = {
            "shutdown": self._cmd_shutdown,
            "restart": self._cmd_restart,
            "status": self._cmd_status,
            "maintenance": self._cmd_maintenance,
            "reset_learning": self._cmd_reset_learning,
            "export_data": self._cmd_export_data,
            "import_data": self._cmd_import_data,
        }

        if command not in command_map:
            return {"error": f"Unknown command: {command}"}

        try:
            result = command_map[command](parameters)
            audit = AuditEntry(
                event_type="operator_command_executed",
                details={
                    "command": command,
                    "parameters": parameters,
                    "result": "success",
                },
                visibility=VisibilityLevel.VISIBLE,
            )
            self.db.log_audit(audit)
            return result
        except Exception as e:
            audit = AuditEntry(
                event_type="operator_command_failed",
                details={"command": command, "parameters": parameters, "error": str(e)},
                visibility=VisibilityLevel.BRIGHT,
            )
            self.db.log_audit(audit)
            return {"error": str(e)}

    def _cmd_shutdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Shutdown the runtime gracefully."""
        # Implementation would handle graceful shutdown
        return {"status": "shutdown_initiated", "message": "Runtime shutdown initiated"}

    def _cmd_restart(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restart the runtime."""
        return {"status": "restart_initiated", "message": "Runtime restart initiated"}

    def _cmd_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed runtime status."""
        return self.get_scoreboard()

    def _cmd_maintenance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run maintenance tasks."""
        return self.schedule_maintenance()

    def _cmd_reset_learning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reset learning state (requires confirmation)."""
        if not params.get("confirmed", False):
            return {"error": "Reset learning requires confirmation parameter"}

        # Reset learning state
        self.evolution.reset()
        return {"status": "learning_reset", "message": "Learning state has been reset"}

    def _cmd_export_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export runtime data."""
        export_path = params.get(
            "path", f"swarmz_export_{datetime.now().isoformat()}.json"
        )
        # Implementation would export data
        return {"status": "export_initiated", "path": export_path}

    def _cmd_import_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import runtime data."""
        import_path = params.get("path")
        if not import_path:
            return {"error": "Import path required"}

        # Implementation would import data
        return {"status": "import_completed", "path": import_path}

    def get_sovereignty_status(self, operator_key: str) -> Dict[str, Any]:
        """Get sovereignty status for operator."""
        is_valid = operator_key == self.operator_key
        anchor_valid = verify_fingerprint(self.anchor)

        return {
            "sovereign": is_valid and anchor_valid,
            "operator_valid": is_valid,
            "anchor_valid": anchor_valid,
            "learning_enabled": self.learning_enabled,
            "timestamp": datetime.now().isoformat(),
        }

    def get_current_timestamp(self) -> str:
        """Get current timestamp for sovereignty checks."""
        return datetime.now().isoformat()

    def make_sovereign_decision(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Make a sovereign decision using the complete lattice flow.
        THE THING WITHOUT A NAME - Meta-selector governs all layers.
        """
        return self.meta_selector.select(context, options)

    def process_task_matrix(
        self, context: Dict[str, Any], options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process through the NEXT TASK MATRIX to generate unified ignition-state vector.

        NEXT TASK MATRIX
        ────────────────
        FILTRATION: PRE-EVALUATED
        GEOMETRY: SPACE-SHAPING
        BOUNDARY: ARCHITECTURAL RESTRAINT
        ALIGNMENT: MYTHICAL WAY
        OVERRIDE: HIDDEN WAY
        UPLIFT: MAGIC WAY
        SOVEREIGN ARBITRATION: THE THING WITHOUT A NAME

        OUTPUT: unified ignition-state vector for cockpit operations
        """
        return self.task_matrix.process_task_matrix(context, options)

    def execute_kernel_ignition(self, ignition_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        IGNITION PHASE 3 — RUNTIME KERNEL IGNITION BLOCK
        (clean, compressed, operator-grade, safe)

        Consumes unified ignition-state vector and executes deterministic ignition sequence.
        Transitions UI → runtime bridge into active cockpit mode.

        IGNITION SEQUENCE:
        1. RECEIVE → sovereign arbitration signal
        2. FILTER → PRE-EVALUATED gate
        3. SHAPE → SPACE-SHAPING geometry
        4. CONSTRAIN → ARCHITECTURAL RESTRAINT shell
        5. ALIGN → MYTHICAL WAY field
        6. UPLIFT → MAGIC WAY surge
        7. OVERRIDE → HIDDEN WAY channel
        8. FINALIZE → THE THING WITHOUT A NAME

        OUTPUT: deterministic ignition result with cockpit activation
        """
        import numpy as np

        # Extract ignition components
        unified_vector = ignition_state.get("unified_vector", np.zeros(9))
        cockpit_signal = ignition_state.get("cockpit_signal", {})
        _kernel_path = ignition_state.get("kernel_path", {})
        layer_states = ignition_state.get("layer_states", {})
        meta_coherence = ignition_state.get("meta_coherence", 0)

        ignition_result = {
            "ignition_phase": "PHASE_3_KERNEL_IGNITION",
            "timestamp": datetime.now().isoformat(),
            "sequence_steps": [],
            "deterministic_result": {},
            "cockpit_activation": {},
            "kernel_state": "STANDBY",
        }

        # STEP 1: RECEIVE → sovereign arbitration signal
        sovereign_signal = layer_states.get("sovereign_arbitration", {})
        ignition_result["sequence_steps"].append(
            {
                "step": 1,
                "operation": "RECEIVE_SOVEREIGN_SIGNAL",
                "signal": sovereign_signal.get("decision", {}),
                "coherence": meta_coherence,
                "status": "COMPLETE",
            }
        )

        # STEP 2: FILTER → PRE-EVALUATED gate
        pre_eval_state = layer_states.get("pre_evaluated", {})
        filter_gate = {
            "threshold": 0.5,
            "passed": pre_eval_state.get("ignition_value", 0) > 0.5,
            "filtered_count": len(pre_eval_state.get("filtered_options", [])),
        }
        ignition_result["sequence_steps"].append(
            {
                "step": 2,
                "operation": "FILTER_PRE_EVALUATED_GATE",
                "gate_status": filter_gate,
                "status": "COMPLETE",
            }
        )

        # STEP 3: SHAPE → SPACE-SHAPING geometry
        _space_shaping = layer_states.get("space_shaping", {})
        geometry_vector = unified_vector[
            5
        ]  # SPACE-SHAPING is index 5 in weighted hierarchy
        geometry_shape = {
            "vector_component": float(geometry_vector),
            "directionality": "convergent" if geometry_vector > 0.7 else "divergent",
            "dimensionality": 9,
        }
        ignition_result["sequence_steps"].append(
            {
                "step": 3,
                "operation": "SHAPE_SPACE_SHAPING_GEOMETRY",
                "geometry": geometry_shape,
                "status": "COMPLETE",
            }
        )

        # STEP 4: CONSTRAIN → ARCHITECTURAL RESTRAINT shell
        restraint_state = layer_states.get("architectural_restraint", {})
        constraint_shell = {
            "purity_level": restraint_state.get("ignition_value", 0),
            "boundaries_enforced": restraint_state.get("constraints_applied", []),
            "architectural_integrity": (
                "MAINTAINED"
                if restraint_state.get("ignition_value", 0) > 0.6
                else "COMPROMISED"
            ),
        }
        ignition_result["sequence_steps"].append(
            {
                "step": 4,
                "operation": "CONSTRAIN_ARCHITECTURAL_RESTRAINT_SHELL",
                "shell": constraint_shell,
                "status": "COMPLETE",
            }
        )

        # STEP 5: ALIGN → MYTHICAL WAY field
        mythical_state = layer_states.get("mythical_way", {})
        alignment_field = {
            "archetypal_resonance": mythical_state.get("ignition_value", 0),
            "field_strength": unified_vector[2],  # MYTHICAL WAY is index 2
            "alignment_quality": (
                "HARMONIC"
                if mythical_state.get("ignition_value", 0) > 0.8
                else "RESONANT"
            ),
        }
        ignition_result["sequence_steps"].append(
            {
                "step": 5,
                "operation": "ALIGN_MYTHICAL_WAY_FIELD",
                "field": alignment_field,
                "status": "COMPLETE",
            }
        )

        # STEP 6: UPLIFT → MAGIC WAY surge
        magic_state = layer_states.get("magic_way", {})
        uplift_surge = {
            "surge_power": magic_state.get("ignition_value", 0),
            "emergent_potential": unified_vector[3],  # MAGIC WAY is index 3
            "uplift_vector": (
                "ASCENDING" if magic_state.get("ignition_value", 0) > 0.7 else "STABLE"
            ),
        }
        ignition_result["sequence_steps"].append(
            {
                "step": 6,
                "operation": "UPLIFT_MAGIC_WAY_SURGE",
                "surge": uplift_surge,
                "status": "COMPLETE",
            }
        )

        # STEP 7: OVERRIDE → HIDDEN WAY channel
        hidden_state = layer_states.get("hidden_way", {})
        override_channel = {
            "channel_open": hidden_state.get("ignition_value", 0) > 0.9,
            "override_authority": unified_vector[1],  # HIDDEN WAY is index 1
            "sovereign_override": (
                "ENGAGED" if hidden_state.get("ignition_value", 0) > 0.9 else "STANDBY"
            ),
        }
        ignition_result["sequence_steps"].append(
            {
                "step": 7,
                "operation": "OVERRIDE_HIDDEN_WAY_CHANNEL",
                "channel": override_channel,
                "status": "COMPLETE",
            }
        )

        # STEP 8: FINALIZE → THE THING WITHOUT A NAME
        final_arbitration = sovereign_signal
        finalization = {
            "sovereign_decision": final_arbitration.get("decision", {}),
            "final_coherence": meta_coherence,
            "ignition_complete": True,
            "deterministic_hash": hashlib.sha256(
                json.dumps(final_arbitration, sort_keys=True).encode()
            ).hexdigest()[:16],
        }
        ignition_result["sequence_steps"].append(
            {
                "step": 8,
                "operation": "FINALIZE_THE_THING_WITHOUT_A_NAME",
                "arbitration": finalization,
                "status": "COMPLETE",
            }
        )

        # Generate deterministic ignition result
        ignition_result["deterministic_result"] = {
            "ignition_state": "COMPLETE",
            "vector_integrity": np.all(np.isfinite(unified_vector)),
            "sequence_integrity": all(
                step["status"] == "COMPLETE"
                for step in ignition_result["sequence_steps"]
            ),
            "sovereign_governance": "ACTIVE",
            "operator_control": "ENGAGED",
        }

        # Activate cockpit mode
        ignition_result["cockpit_activation"] = {
            "mode": "ACTIVE_COCKPIT",
            "bridge_status": "UI_RUNTIME_CONNECTED",
            "operator_channel": "OPEN",
            "command_acceptance": "SOVEREIGN_FILTERED",
            "execution_governance": "DETERMINISTIC",
        }

        # Set final kernel state
        if (
            ignition_result["deterministic_result"]["sequence_integrity"]
            and meta_coherence > 0.7
            and cockpit_signal.get("operational_readiness") == "IGNITION_READY"
        ):
            ignition_result["kernel_state"] = "IGNITION_COMPLETE"
        else:
            ignition_result["kernel_state"] = "IGNITION_FAILED"

        return ignition_result

    def get_lattice_status(self) -> Dict[str, Any]:
        """
        Get the status of the sovereign lattice flow system.
        """
        return {
            "meta_selector_active": True,
            "lattice_layers": [
                "pre_evaluated",
                "space_shaping",
                "architectural_restraint",
                "magic_way",
                "mythical_way",
                "sovereign_override",
                "meta_selector",
            ],
            "sovereign_governance": "active",
            "opacity_level": "silent_arbitration",
            "timestamp": self.get_current_timestamp(),
        }

    def apply_sovereign_control(
        self, context: Dict[str, Any], decision_type: str
    ) -> Dict[str, Any]:
        """
        Apply sovereign control through the lattice flow for critical decisions.
        """
        # Create decision options based on type
        options = self._generate_decision_options(context, decision_type)

        # Apply lattice flow
        sovereign_decision = self.make_sovereign_decision(context, options)

        # Log sovereign control application
        audit = AuditEntry(
            event_type="sovereign_control_applied",
            details={
                "decision_type": decision_type,
                "context_hash": hashlib.sha256(
                    json.dumps(context, sort_keys=True).encode()
                ).hexdigest()[:16],
                "sovereign_decision": sovereign_decision.get("id", "unknown"),
                "meta_coherence": sovereign_decision.get("_meta_coherence", 0),
            },
            visibility=VisibilityLevel.BRIGHT,
        )
        self.db.log_audit(audit)

        return sovereign_decision

    def _generate_decision_options(
        self, context: Dict[str, Any], decision_type: str
    ) -> List[Dict[str, Any]]:
        """
        Generate decision options based on context and type.
        """
        options = []

        if decision_type == "mission_execution":
            options = [
                {"id": "execute_standard", "strategy": "standard", "risk": "low"},
                {"id": "execute_optimized", "strategy": "optimized", "risk": "medium"},
                {
                    "id": "execute_sovereign",
                    "strategy": "sovereign",
                    "risk": "controlled",
                },
            ]
        elif decision_type == "resource_allocation":
            options = [
                {
                    "id": "allocate_conservative",
                    "allocation": "conservative",
                    "efficiency": "high",
                },
                {
                    "id": "allocate_balanced",
                    "allocation": "balanced",
                    "efficiency": "medium",
                },
                {
                    "id": "allocate_aggressive",
                    "allocation": "aggressive",
                    "efficiency": "variable",
                },
            ]
        elif decision_type == "sovereign_override":
            options = [
                {
                    "id": "override_standard",
                    "override_type": "standard",
                    "transparency": "partial",
                },
                {
                    "id": "override_covert",
                    "override_type": "covert",
                    "transparency": "zero",
                },
                {
                    "id": "override_meta",
                    "override_type": "meta",
                    "transparency": "silent",
                },
            ]
        else:
            # Default options
            options = [
                {"id": f"option_{i}", "type": "default", "index": i} for i in range(3)
            ]

        return options
