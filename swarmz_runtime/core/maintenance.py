# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from typing import Dict, Any, List
from datetime import datetime


class MaintenanceScheduler:
    def __init__(self):
        self.complexity_threshold = 75
        self.maintenance_tasks = []
    
    def evaluate_module_complexity(self, module_name: str, metrics: Dict[str, Any]) -> float:
        lines_of_code = metrics.get("lines_of_code", 0)
        dependencies = metrics.get("dependencies", 0)
        cyclomatic_complexity = metrics.get("cyclomatic_complexity", 0)
        
        complexity = (lines_of_code / 10) + (dependencies * 5) + (cyclomatic_complexity * 2)
        return min(100, complexity)
    
    def schedule_if_needed(self, module_name: str, complexity_score: float) -> bool:
        if complexity_score > self.complexity_threshold:
            task = {
                "module": module_name,
                "complexity_score": complexity_score,
                "scheduled_at": datetime.now().isoformat(),
                "reason": f"Complexity score {complexity_score} exceeds threshold {self.complexity_threshold}"
            }
            self.maintenance_tasks.append(task)
            return True
        return False
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        return self.maintenance_tasks

