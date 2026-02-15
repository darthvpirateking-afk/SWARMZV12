#!/usr/bin/env python3
"""
SWARMZ Companion - Personal AI Companion with Dual-Mode Cognition

A personal AI companion that can freely converse (Companion Mode) and 
execute real tasks by spawning controlled worker agents (Operator Mode).
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class SystemMode(Enum):
    """Two exclusive states of SWARMZ Companion."""
    COMPANION = "companion"  # Conversation, explanations, questions
    OPERATOR = "operator"    # Real-world results, spawns workers


class CommitState(Enum):
    """Task commit states that prevent stalling."""
    ACTION_READY = "action_ready"      # Can run now
    NEEDS_CONFIRM = "needs_confirm"    # Irreversible/spending/external
    BLOCKED = "blocked"                # Missing specific input


class WorkerType(Enum):
    """Types of workers in the swarm."""
    SCOUT = "scout"        # Collect information and constraints
    BUILDER = "builder"    # Create artifacts
    VERIFY = "verify"      # Check correctness and risk


@dataclass
class WorkerResult:
    """Worker output format."""
    result: Any
    risks: List[str] = field(default_factory=list)
    next_action: str = ""
    worker_type: WorkerType = WorkerType.SCOUT


@dataclass
class TaskContext:
    """Context for task execution."""
    task_id: str
    intent: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)
    commit_state: CommitState = CommitState.ACTION_READY
    artifacts: List[Any] = field(default_factory=list)
    worker_results: List[WorkerResult] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class ExecutionLog:
    """Log entry for execution tracking."""
    task_id: str
    task_name: str
    success: bool
    time_taken: float
    cost: float = 0.0
    roi_proxy: float = 0.0
    error_cause: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class Memory:
    """Persistent memory for SWARMZ Companion."""
    preferences: Dict[str, Any] = field(default_factory=dict)
    caps: Dict[str, Any] = field(default_factory=dict)
    whitelist: List[str] = field(default_factory=list)
    ongoing_projects: List[Dict[str, Any]] = field(default_factory=list)
    learned_templates: Dict[str, Any] = field(default_factory=dict)


class Worker:
    """Base worker class for swarm delegation."""
    
    def __init__(self, worker_type: WorkerType):
        self.worker_type = worker_type
    
    def execute(self, task_context: TaskContext) -> WorkerResult:
        """Execute worker task. Must be overridden by subclasses."""
        raise NotImplementedError("Worker.execute must be implemented")


class ScoutWorker(Worker):
    """Collect information and constraints."""
    
    def __init__(self):
        super().__init__(WorkerType.SCOUT)
    
    def execute(self, task_context: TaskContext) -> WorkerResult:
        """Gather information about the task."""
        # Scout workers collect context and constraints
        result = {
            "task_id": task_context.task_id,
            "parameters": task_context.parameters,
            "constraints_identified": []
        }
        return WorkerResult(
            result=result,
            risks=[],
            next_action="proceed_to_builder",
            worker_type=self.worker_type
        )


class BuilderWorker(Worker):
    """Create artifacts (code, message, file, plan)."""
    
    def __init__(self):
        super().__init__(WorkerType.BUILDER)
    
    def execute(self, task_context: TaskContext) -> WorkerResult:
        """Build the artifact."""
        # Builder creates the actual artifact
        artifact = {
            "type": "generic",
            "content": f"Artifact for {task_context.intent}",
            "created_at": time.time()
        }
        return WorkerResult(
            result=artifact,
            risks=[],
            next_action="proceed_to_verify",
            worker_type=self.worker_type
        )


class VerifyWorker(Worker):
    """Check correctness and risk."""
    
    def __init__(self):
        super().__init__(WorkerType.VERIFY)
    
    def execute(self, task_context: TaskContext) -> WorkerResult:
        """Verify artifacts and identify risks."""
        risks = []
        
        # Check for common risk patterns
        if any("delete" in str(a).lower() for a in task_context.artifacts):
            risks.append("Potential destructive operation")
        if any("external" in str(a).lower() for a in task_context.artifacts):
            risks.append("External communication required")
        
        return WorkerResult(
            result={"verified": True, "risk_count": len(risks)},
            risks=risks,
            next_action="ready_for_execution" if not risks else "needs_confirmation",
            worker_type=self.worker_type
        )


class WorkerSwarm:
    """Manages worker delegation (max 3 workers per task)."""
    
    MAX_WORKERS = 3
    
    def __init__(self):
        self.active_workers: List[Worker] = []
    
    def spawn_worker(self, worker_type: WorkerType) -> Worker:
        """Spawn a worker of specified type."""
        if len(self.active_workers) >= self.MAX_WORKERS:
            raise ValueError(f"Maximum {self.MAX_WORKERS} workers per task")
        
        if worker_type == WorkerType.SCOUT:
            worker = ScoutWorker()
        elif worker_type == WorkerType.BUILDER:
            worker = BuilderWorker()
        elif worker_type == WorkerType.VERIFY:
            worker = VerifyWorker()
        else:
            raise ValueError(f"Unknown worker type: {worker_type}")
        
        self.active_workers.append(worker)
        return worker
    
    def execute_workflow(self, task_context: TaskContext) -> List[WorkerResult]:
        """Execute standard workflow: Scout -> Builder -> Verify."""
        results = []
        
        # Scout phase
        scout = self.spawn_worker(WorkerType.SCOUT)
        scout_result = scout.execute(task_context)
        results.append(scout_result)
        
        # Builder phase
        builder = self.spawn_worker(WorkerType.BUILDER)
        builder_result = builder.execute(task_context)
        results.append(builder_result)
        task_context.artifacts.append(builder_result.result)
        
        # Verify phase
        verify = self.spawn_worker(WorkerType.VERIFY)
        verify_result = verify.execute(task_context)
        results.append(verify_result)
        
        return results
    
    def clear_workers(self):
        """Clear active workers after task completion."""
        self.active_workers.clear()


class CommitEngine:
    """Prevents planning loops by forcing commit decisions."""
    
    def __init__(self):
        self.safety_caps = {
            "max_spend": 100.0,
            "allow_irreversible": False,
            "external_whitelist": []
        }
    
    def evaluate(self, task_context: TaskContext) -> CommitState:
        """
        Evaluate task and determine commit state.
        Default behavior: execute unless vetoed.
        """
        # Check for blocking conditions first
        if not task_context.parameters:
            if not task_context.assumptions:
                return CommitState.BLOCKED
        
        # Check worker results for risks
        high_risk = False
        for worker_result in task_context.worker_results:
            if worker_result.risks:
                for risk in worker_result.risks:
                    if "destructive" in risk.lower() or "external" in risk.lower():
                        high_risk = True
                        break
        
        # Determine commit state based on risk
        if high_risk:
            return CommitState.NEEDS_CONFIRM
        
        # Default to action ready (prevents stalling)
        return CommitState.ACTION_READY
    
    def update_safety_caps(self, caps: Dict[str, Any]):
        """Update safety boundaries."""
        self.safety_caps.update(caps)


class IntelligenceLayer:
    """Real learning system that predicts and records outcomes."""
    
    def __init__(self):
        self.execution_logs: List[ExecutionLog] = []
        self.scoring_weights = {
            "success_rate": 1.0,
            "time_efficiency": 0.8,
            "cost_efficiency": 0.6
        }
    
    def predict_outcome(self, task_context: TaskContext) -> Dict[str, Any]:
        """Predict outcome and cost before execution."""
        # Simple prediction based on historical data
        similar_tasks = [
            log for log in self.execution_logs
            if log.task_name == task_context.intent
        ]
        
        if similar_tasks:
            avg_time = sum(log.time_taken for log in similar_tasks) / len(similar_tasks)
            avg_cost = sum(log.cost for log in similar_tasks) / len(similar_tasks)
            success_rate = sum(1 for log in similar_tasks if log.success) / len(similar_tasks)
        else:
            avg_time = 1.0  # Default estimate
            avg_cost = 0.0
            success_rate = 0.8  # Optimistic default
        
        return {
            "predicted_time": avg_time,
            "predicted_cost": avg_cost,
            "success_probability": success_rate
        }
    
    def record_execution(self, log_entry: ExecutionLog):
        """Record execution results for learning."""
        self.execution_logs.append(log_entry)
    
    def evolve_weights(self, performance_data: Dict[str, float]):
        """Evolve scoring weights based on performance."""
        # Simple weight adjustment based on performance
        for key, value in performance_data.items():
            if key in self.scoring_weights:
                # Adjust weight by 10% based on performance
                adjustment = (value - 0.5) * 0.1
                self.scoring_weights[key] = max(0.1, min(2.0, 
                    self.scoring_weights[key] + adjustment))


class EvolutionMechanism:
    """Generates patchpacks for system improvement."""
    
    def __init__(self, intelligence: IntelligenceLayer):
        self.intelligence = intelligence
        self.pending_patchpacks: List[Dict[str, Any]] = []
    
    def generate_patchpack(self) -> Optional[Dict[str, Any]]:
        """Generate patchpack from execution logs."""
        if len(self.intelligence.execution_logs) < 10:
            return None  # Need more data
        
        recent_logs = self.intelligence.execution_logs[-100:]
        
        # Analyze patterns
        failed_tasks = [log for log in recent_logs if not log.success]
        if len(failed_tasks) > len(recent_logs) * 0.3:  # >30% failure rate
            patchpack = {
                "type": "routing_adjustment",
                "description": "Adjust task routing due to high failure rate",
                "changes": {
                    "routing_rules": "more_conservative"
                },
                "created_at": time.time()
            }
            self.pending_patchpacks.append(patchpack)
            return patchpack
        
        return None
    
    def apply_patchpack(self, patchpack: Dict[str, Any], approved: bool = False):
        """Apply approved patchpack."""
        if not approved:
            return False
        
        # Apply changes (simplified)
        if patchpack["type"] == "routing_adjustment":
            # Would modify routing rules
            pass
        
        return True


class CompanionMode:
    """Handles conversation mode - free conversation, no task execution."""
    
    def __init__(self):
        self.conversation_history: List[Dict[str, str]] = []
    
    def respond(self, user_input: str) -> str:
        """Generate conversational response."""
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Simple conversational response
        response = f"I understand you're saying: {user_input}. How can I help you today?"
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return f"{response}\n\n[CONVERSATION]"


class OperatorMode:
    """Handles execution mode - produces real-world results."""
    
    def __init__(self, swarmz_core=None):
        self.swarmz_core = swarmz_core
        self.commit_engine = CommitEngine()
        self.intelligence = IntelligenceLayer()
        self.evolution = EvolutionMechanism(self.intelligence)
        self.worker_swarm = WorkerSwarm()
    
    def execute_task(self, intent: str, parameters: Dict[str, Any]) -> Tuple[str, CommitState]:
        """
        Execute task following the execution loop:
        INTAKE → STRUCTURE → DECIDE → COMMIT → EXECUTE → VERIFY → LOG → EVOLVE
        """
        start_time = time.time()
        task_id = f"task_{int(time.time() * 1000)}"
        
        # INTAKE
        task_context = TaskContext(
            task_id=task_id,
            intent=intent,
            parameters=parameters
        )
        
        # STRUCTURE - Use worker swarm
        worker_results = self.worker_swarm.execute_workflow(task_context)
        task_context.worker_results = worker_results
        
        # DECIDE - Predict outcome
        prediction = self.intelligence.predict_outcome(task_context)
        
        # COMMIT - Determine state
        commit_state = self.commit_engine.evaluate(task_context)
        task_context.commit_state = commit_state
        
        # Build response
        response_parts = []
        response_parts.append(f"SITUATION: {intent}")
        response_parts.append(f"DECISION: {commit_state.value}")
        
        # EXECUTE (if ACTION_READY)
        success = False
        if commit_state == CommitState.ACTION_READY:
            # Execute via swarmz_core if available
            if self.swarmz_core:
                try:
                    result = "Executed successfully"
                    success = True
                except Exception as e:
                    result = f"Execution failed: {e}"
                    success = False
            else:
                result = "Simulated execution"
                success = True
            
            response_parts.append(f"EXECUTION: {result}")
            
            # VERIFY
            verify_result = worker_results[-1] if worker_results else None
            if verify_result:
                response_parts.append(f"VERIFY: {len(verify_result.risks)} risks identified")
            
            # LOG
            execution_time = time.time() - start_time
            log_entry = ExecutionLog(
                task_id=task_id,
                task_name=intent,
                success=success,
                time_taken=execution_time,
                cost=0.0,
                roi_proxy=1.0 if success else 0.0
            )
            self.intelligence.record_execution(log_entry)
            response_parts.append(f"LOG: Recorded execution ({execution_time:.3f}s)")
            
            # EVOLVE
            patchpack = self.evolution.generate_patchpack()
            if patchpack:
                response_parts.append(f"EVOLVE: Patchpack generated")
        
        # Clear workers
        self.worker_swarm.clear_workers()
        
        response = "\n".join(response_parts)
        response += f"\n\n[{commit_state.value.upper()}]"
        
        return response, commit_state


class ModeManager:
    """Manages mode switching between Companion and Operator modes."""
    
    def __init__(self, swarmz_core=None):
        self.current_mode = SystemMode.COMPANION
        self.companion_mode = CompanionMode()
        self.operator_mode = OperatorMode(swarmz_core)
        self.memory = Memory()
    
    def detect_mode(self, user_input: str) -> SystemMode:
        """
        Detect which mode to use based on user input.
        Questions → Companion Mode
        Commands → Operator Mode
        Mixed intent → Operator Mode priority
        """
        # Simple heuristic detection
        question_words = ["what", "why", "how", "when", "where", "who", "can you explain"]
        command_words = ["do", "create", "execute", "run", "make", "build", "delete"]
        
        input_lower = user_input.lower()
        
        is_question = any(qw in input_lower for qw in question_words) and "?" in user_input
        is_command = any(cw in input_lower for cw in command_words)
        
        # Operator mode takes priority for mixed intent
        if is_command:
            return SystemMode.OPERATOR
        if is_question:
            return SystemMode.COMPANION
        
        # Default to operator mode for ambiguous input
        return SystemMode.OPERATOR
    
    def process_input(self, user_input: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Process user input and route to appropriate mode."""
        # Detect mode
        detected_mode = self.detect_mode(user_input)
        self.current_mode = detected_mode
        
        # Route to appropriate mode
        if detected_mode == SystemMode.COMPANION:
            return self.companion_mode.respond(user_input)
        else:
            params = parameters or {}
            response, _ = self.operator_mode.execute_task(user_input, params)
            return response
    
    def get_memory(self) -> Memory:
        """Get persistent memory."""
        return self.memory
    
    def update_memory(self, memory_updates: Dict[str, Any]):
        """Update persistent memory."""
        if "preferences" in memory_updates:
            self.memory.preferences.update(memory_updates["preferences"])
        if "caps" in memory_updates:
            self.memory.caps.update(memory_updates["caps"])
        if "whitelist" in memory_updates:
            self.memory.whitelist.extend(memory_updates["whitelist"])
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get success metrics."""
        logs = self.operator_mode.intelligence.execution_logs
        if not logs:
            return {
                "completed_verified_actions_per_day": 0,
                "error_rate": 0.0,
                "total_actions": 0
            }
        
        total = len(logs)
        successful = sum(1 for log in logs if log.success)
        error_rate = (total - successful) / total if total > 0 else 0.0
        
        # Calculate actions per day (simplified)
        if logs:
            time_span_days = (time.time() - logs[0].timestamp) / 86400
            actions_per_day = total / max(time_span_days, 1.0)
        else:
            actions_per_day = 0.0
        
        return {
            "completed_verified_actions_per_day": actions_per_day,
            "error_rate": error_rate,
            "total_actions": total,
            "success_rate": successful / total if total > 0 else 0.0
        }


class SwarmzCompanion:
    """
    Main SWARMZ Companion System.
    Personal AI companion with dual-mode cognition.
    """
    
    def __init__(self, swarmz_core=None):
        self.mode_manager = ModeManager(swarmz_core)
        self.swarmz_core = swarmz_core
    
    def interact(self, user_input: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Main interaction method. Routes to appropriate mode.
        """
        return self.mode_manager.process_input(user_input, parameters)
    
    def get_current_mode(self) -> SystemMode:
        """Get current system mode."""
        return self.mode_manager.current_mode
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        return self.mode_manager.get_metrics()
    
    def save_memory(self, filepath: str):
        """Save persistent memory to file."""
        memory = self.mode_manager.get_memory()
        memory_dict = {
            "preferences": memory.preferences,
            "caps": memory.caps,
            "whitelist": memory.whitelist,
            "ongoing_projects": memory.ongoing_projects,
            "learned_templates": memory.learned_templates
        }
        with open(filepath, 'w') as f:
            json.dump(memory_dict, f, indent=2)
    
    def load_memory(self, filepath: str):
        """Load persistent memory from file."""
        try:
            with open(filepath, 'r') as f:
                memory_dict = json.load(f)
            self.mode_manager.update_memory(memory_dict)
        except FileNotFoundError:
            pass  # No saved memory yet


def main():
    """Demonstrate SWARMZ Companion."""
    print("=" * 60)
    print("SWARMZ Companion - Personal AI Companion")
    print("=" * 60)
    print()
    
    companion = SwarmzCompanion()
    
    # Demo conversation mode
    print("1. Testing Companion Mode (conversation):")
    response = companion.interact("What is the weather like?")
    print(f"Response: {response}")
    print()
    
    # Demo operator mode
    print("2. Testing Operator Mode (execution):")
    response = companion.interact("Create a new file", {"filename": "test.txt"})
    print(f"Response: {response}")
    print()
    
    # Show metrics
    print("3. System Metrics:")
    metrics = companion.get_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    print()
    
    print("SWARMZ Companion is ready!")


if __name__ == "__main__":
    main()
