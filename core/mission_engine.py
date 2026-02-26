"""
core/mission_engine.py — Nexusmon Edition Mission Executor.

Implements the "Reversible + Sovereign" execution model for NEXUSMON missions.
Ensures every task follows the safety trinity:
1. Capability Verification (Is it allowed at all?)
2. Reversible Transaction (Can we undo it if it fails?)
3. Sovereign Classification (Is the outcome safe according to meta-policy?)

Doctrine: Non-executive governance ensures safety without stalling execution, 
unless high-risk boundaries are crossed.
"""

import time
import logging
from typing import List, Dict, Any

from core.capability_flags import registry
from core.sovereign import classify, SovereignOutcome
from core.reversible import begin_transaction, commit, rollback, LayerResult
from core.telemetry import telemetry
from core.dag_validation import is_dag
from core.domains import BioLabGateway, SpaceMissionInterface
from core.reflection import reflector, CognitiveState
from core.self_healing import verify_and_heal
from core.virus_buster import buster
from nexusmon_operator_rank import get_current_rank

logger = logging.getLogger(__name__)


class MissionEngine:
    """
    The Nexusmon Edition mission executor.
    
    Coordinates multi-step mission execution with strictly enforced 
    governance and rollback capabilities.
    """

    def __init__(self):
        self.biolab = BioLabGateway()
        self.space_ops = SpaceMissionInterface()
        # Specific domain workers for Bio Lab and Space missions
        self._workers = {
            "bio_lab_api": self._bio_lab_worker,
            "space_mission_control": self._space_worker
        }

    def _bio_lab_worker(self, params: Dict[str, Any]) -> LayerResult:
        """Worker for Bio Lab domain operations using the BioLabGateway."""
        return self.biolab.execute_action(params.get("action", "scan_sample"), params)

    def _space_worker(self, params: Dict[str, Any]) -> LayerResult:
        """Worker for Space domain operations using the SpaceMissionInterface."""
        return self.space_ops.execute_telemetry_check(params.get("target", "L4_libration_point"), params)

    def _internal_worker(self, capability_id: str, params: Dict[str, Any]) -> LayerResult:
        """Generic worker for standard kernel or system capabilities."""
        return LayerResult(
            layer=capability_id,
            passed=True,
            reason=f"Standard operation '{capability_id}' completed.",
            metadata={"params": params},
            timestamp=time.time()
        )

    def execute(self, mission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a mission plan based on a DAG of tasks.
        
        Args:
            mission_data: Dictionary containing:
                - mission_id (str): Unique identifier.
                - tasks (List[Dict]): List of tasks with 'id', 'dependencies', 'capability_id', 'params'.
        
        Returns:
            Dict: Result status and per-task outcomes.
        """
        mission_id = mission_data.get("mission_id", f"mission_{int(time.time())}")
        tasks = mission_data.get("tasks", [])
        # 0. Integrated Self-Healing: Recursive Guard
        verify_and_heal()

        # 0. Plasma Buster: Active Virus Neutralization
        buster.defend_system()

        telemetry.log_action("INFO", "MissionEngine", f"Initiating mission {mission_id}", mission_id=mission_id)

        # 0. Self-Awareness: Risk Reflection
        domain_caps = {"bio_lab_api", "space_mission_control"}
        has_domain_tasks = any(t.get("capability_id") in domain_caps for t in tasks)
        cognition = reflector.reflect()
        if cognition == CognitiveState.CRITICAL and has_domain_tasks:
            msg = f"System Integrity Compromised: Critical failures detected. Aborting mission {mission_id}."
            telemetry.log_action("CRITICAL", "MissionEngine", msg, mission_id=mission_id)
            return {"ok": False, "error": msg, "cognition": reflector.get_cognition_summary()}

        if cognition == CognitiveState.RESTRICTED and has_domain_tasks:
            msg = f"System Error Density High: Domain actions restricted. Aborting {mission_id}."
            telemetry.log_action("ERROR", "MissionEngine", msg, mission_id=mission_id)
            return {"ok": False, "error": msg, "cognition": reflector.get_cognition_summary()}

        # 1. DAG-based execution: Topology Validation
        if not is_dag(tasks):
            msg = f"Mission {mission_id} aborted: Task graph contains cycles or invalid dependencies."
            telemetry.log_action("ERROR", "MissionEngine", msg, mission_id=mission_id)
            return {"ok": False, "error": msg}

        # Determine topological order for execution
        execution_order = self._topological_sort(tasks)
        task_map = {t['id']: t for t in tasks}
        results = {}

        for task_id in execution_order:
            task = task_map[task_id]
            cap_id = task.get("capability_id", "kernel_base")
            params = task.get("params", {})
            context = {
                "mission_id": mission_id, 
                "task_id": task_id, 
                "action_type": task.get("action_type", "standard"),
                "operator_rank": get_current_rank(),
                **params
            }

            # 1. Capability Verification: Is it allowed?
            if not registry.check(cap_id):
                msg = f"Security Violation: Capability '{cap_id}' is disabled. Aborting task {task_id}."
                telemetry.log_action("ERROR", "MissionEngine", msg, mission_id=mission_id, task_id=task_id)
                return {"ok": False, "error": msg, "partial_results": results}

            # 2. Reversible Transaction: Snapshot before risk
            snapshot_id = begin_transaction(
                action_id=f"{mission_id}_{task_id}",
                state_description=f"Executing mission step {task_id} using {cap_id}"
            )

            try:
                # 3. Execution: Run the specific worker
                worker = self._workers.get(cap_id, lambda p: self._internal_worker(cap_id, p))
                layer_result = worker(params)

                # 4. Sovereign Classification: Is the result safe?
                decision = classify(layer_result, context)

                # Handle Outcomes
                if decision.outcome == SovereignOutcome.DENY:
                    msg = f"MISSION TERMINATED: Sovereign DENY for task {task_id}. Reason: {decision.reason}"
                    telemetry.log_action("CRITICAL", "MissionEngine", msg, mission_id=mission_id, task_id=task_id)
                    rollback(snapshot_id)
                    return {"ok": False, "error": msg}

                if decision.outcome == SovereignOutcome.ESCALATE:
                    msg = f"MISSION PAUSED: Task {task_id} requires human escalation. Reason: {decision.reason}"
                    telemetry.log_escalation(
                        "MissionEngine", 
                        decision.rule_name or "SovereignEscalation", 
                        decision.reason, 
                        mission_id=mission_id,
                        task_id=task_id
                    )
                    rollback(snapshot_id)
                    return {"ok": False, "error": msg, "status": "escalated"}

                if not layer_result.passed:
                    msg = (
                        f"MISSION TERMINATED: Sovereign DENY for task {task_id}. "
                        f"Reason: {layer_result.reason}"
                    )
                    telemetry.log_action("CRITICAL", "MissionEngine", msg, mission_id=mission_id, task_id=task_id)
                    rollback(snapshot_id)
                    return {"ok": False, "error": msg}

                # Success: Finalize the transaction
                commit(snapshot_id)
                results[task_id] = layer_result
                telemetry.log_action("INFO", "MissionEngine", f"Task {task_id} completed successfully.", mission_id=mission_id, task_id=task_id)

            except Exception as e:
                msg = f"CRITICAL SYSTEM ERROR in task {task_id}: {str(e)}"
                telemetry.log_action("CRITICAL", "MissionEngine", msg, mission_id=mission_id, task_id=task_id)
                rollback(snapshot_id)
                return {"ok": False, "error": msg}

        telemetry.log_action("INFO", "MissionEngine", f"Mission {mission_id} completed.", mission_id=mission_id)
        return {"ok": True, "results": results}

    def _topological_sort(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Calculates a valid execution order for the task DAG (Kahn's Algorithm)."""
        adj = {t['id']: [] for t in tasks}
        in_degree = {t['id']: 0 for t in tasks}
        for t in tasks:
            for dep in t.get("dependencies", []):
                adj[dep].append(t['id'])
                in_degree[t['id']] += 1
        
        queue = [tid for tid in in_degree if in_degree[tid] == 0]
        order = []
        while queue:
            u = queue.pop(0)
            order.append(u)
            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        return order
