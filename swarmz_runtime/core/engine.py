from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from swarmz_runtime.storage.db import Database
from swarmz_runtime.storage.schema import Mission, AuditEntry, Rune, MissionStatus, VisibilityLevel
from swarmz_runtime.core.scoring import calculate_leverage_score, should_execute
from swarmz_runtime.core.authority import validate_transaction
from swarmz_runtime.core.learning import LearningEngine
from swarmz_runtime.core.prediction import ProphetEngine
from swarmz_runtime.core.resonance import ResonanceDetector
from swarmz_runtime.core.cadence import CadenceEngine
from swarmz_runtime.core.maintenance import MaintenanceScheduler
from swarmz_runtime.core.visibility import VisibilityManager
from swarmz_runtime.core.brain import BrainMapping


class SwarmzEngine:
    def __init__(self, data_dir: str = "data", brain_config: Optional[Dict[str, Any]] = None):
        self.db = Database(data_dir)
        self.learning = LearningEngine()
        self.prophet = ProphetEngine(self.db)
        self.resonance = ResonanceDetector(self.db)
        self.cadence = CadenceEngine()
        self.maintenance = MaintenanceScheduler()
        self.visibility = VisibilityManager()
        self.brain = BrainMapping(brain_config)
        
        self.max_active_missions = 3
        self.operator_key = "swarmz_sovereign_key"
    
    def create_mission(self, goal: str, category: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
        active_missions = self.db.get_active_missions()
        if len(active_missions) >= self.max_active_missions:
            return {
                "error": f"Maximum {self.max_active_missions} active missions exceeded",
                "active_count": len(active_missions)
            }
        
        mission_id = str(uuid.uuid4())[:8]
        
        mission_data = {
            "id": mission_id,
            "goal": goal,
            "category": category,
            "constraints": constraints,
            "expiry": None,
            "status": "pending"
        }
        
        validation = validate_transaction(mission_data)
        
        leverage_score = calculate_leverage_score(mission_data)
        
        try:
            mission = Mission(
                id=mission_id,
                goal=goal,
                category=category,
                constraints=constraints,
                status=MissionStatus.PENDING,
                leverage_score=leverage_score
            )
        except Exception:
            return {"error": f"Invalid category '{category}'. Must be one of: coin, forge, library, sanctuary"}
        
        self.db.save_mission(mission)
        
        audit = AuditEntry(
            event_type="mission_created",
            mission_id=mission_id,
            details={"goal": goal, "category": category},
            visibility=VisibilityLevel.VISIBLE
        )
        self.db.log_audit(audit)
        
        return {
            "mission_id": mission_id,
            "status": "created",
            "validation": validation.model_dump(),
            "leverage_score": leverage_score
        }
    
    def run_mission(self, mission_id: str, operator_key: Optional[str] = None) -> Dict[str, Any]:
        mission = self.db.get_mission(mission_id)
        if not mission:
            return {"error": "Mission not found"}
        
        validation = validate_transaction(mission)
        
        if validation.failing:
            audit = AuditEntry(
                event_type="mission_blocked",
                mission_id=mission_id,
                details={"reason": "validation_failed", "scores": validation.scores.model_dump()},
                visibility=VisibilityLevel.BRIGHT
            )
            self.db.log_audit(audit)
            return {"error": "Mission validation failed - suggestion only", "validation": validation.model_dump()}
        
        if validation.requires_approval and operator_key != self.operator_key:
            audit = AuditEntry(
                event_type="mission_requires_approval",
                mission_id=mission_id,
                details={"reason": "borderline_validation"},
                visibility=VisibilityLevel.VISIBLE
            )
            self.db.log_audit(audit)
            return {"error": "Mission requires operator approval", "validation": validation.model_dump()}
        
        if not should_execute(mission):
            return {"error": "Mission has negative expected value and is not research"}
        
        self.db.update_mission(mission_id, {"status": "active"})
        
        success = True
        roi = 1.5
        
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
                last_used=datetime.now()
            )
            self.db.save_rune(rune)
            
            next_run = self.cadence.schedule_next_run(mission, success=True)
            
            audit = AuditEntry(
                event_type="mission_completed",
                mission_id=mission_id,
                details={"roi": roi, "next_run": next_run.isoformat()},
                visibility=VisibilityLevel.VISIBLE
            )
            self.db.log_audit(audit)
            
            return {
                "status": "completed",
                "mission_id": mission_id,
                "roi": roi,
                "next_run": next_run.isoformat(),
                "rune_created": rune.id
            }
        else:
            self.db.update_mission(mission_id, {"status": "failed"})
            self.resonance.detect_pattern(f"{mission['category']}:failure")
            
            audit = AuditEntry(
                event_type="mission_failed",
                mission_id=mission_id,
                details={"reason": "execution_error", "category": mission["category"]},
                visibility=VisibilityLevel.BRIGHT
            )
            self.db.log_audit(audit)
            
            return {"status": "failed", "mission_id": mission_id}
    
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
            "pattern_counters": len(state.get("pattern_counters", {}))
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
            metrics = {"lines_of_code": 200, "dependencies": 5, "cyclomatic_complexity": 10}
            complexity = self.maintenance.evaluate_module_complexity(module, metrics)
            self.maintenance.schedule_if_needed(module, complexity)
        
        tasks = self.maintenance.get_pending_tasks()
        
        return {
            "scheduled_tasks": len(tasks),
            "tasks": tasks
        }
    
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
